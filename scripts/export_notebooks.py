"""
Export all notebooks to static HTML using `marimo export html`.

Auto-discovers *.py files under notebooks/, excluding:
  - notebooks/__marimo__/ (marimo metadata)

Outputs to app/public/notebooks/ mirroring the source directory structure.
Insight pages (insights/*.py) are included — their HTML is served via MarimoIframe.

After each export the HTML is post-processed to reduce its size:
  - The large inline ``window.__MARIMO_MOUNT_CONFIG__`` JSON blob is extracted
    and gzip-compressed into a ``<name>.data.gz`` sidecar file (typically ~90%
    smaller than the raw blob).
  - The Marimo CDN ``<script type="module">`` tag is replaced with a small
    async loader that fetches + decompresses the sidecar file at runtime, then
    dynamically imports the Marimo frontend bundle from the same CDN URL.
  - ``<link rel="preload">`` and ``<link rel="modulepreload">`` hints are added
    so the browser can fetch both assets in parallel while parsing the tiny HTML
    shell.

Result: each exported HTML drops from ~25 MB to a few KB; the data sidecar is
~2-3 MB (compressed), and repeat visitors benefit from browser caching.
"""

import gzip
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
OUTPUT_DIR = REPO_ROOT / "app" / "public" / "notebooks"

EXCLUDE_DIRS = {"__marimo__"}

# Regex that matches the Marimo frontend CDN <script type="module"> tag.
# Example:
#   <script type="module" crossorigin crossorigin="anonymous"
#           src="https://cdn.jsdelivr.net/npm/@marimo-team/frontend@X.Y.Z/…/index-…js">
#   </script>
_MARIMO_MODULE_RE = re.compile(
    r'<script[^>]+type="module"[^>]+src="'
    r"(https://cdn\.jsdelivr\.net/npm/@marimo-team/frontend[^\"]+\.js)"
    r'"[^>]*>\s*</script>',
    re.DOTALL,
)


def _strip_trailing_commas(text: str) -> str:
    """Remove trailing commas from a JS object/array literal, ignoring string contents.

    Marimo embeds the config as a JavaScript object literal (not strict JSON),
    which may include trailing commas before closing braces/brackets.  Those
    commas are valid JS but are rejected by ``JSON.parse()`` – and by Python's
    ``json`` module – so we strip them before compressing.
    """
    result: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    escape_next = False

    while i < n:
        c = text[i]
        if escape_next:
            escape_next = False
            result.append(c)
        elif c == "\\" and in_string:
            escape_next = True
            result.append(c)
        elif c == '"':
            in_string = not in_string
            result.append(c)
        elif not in_string and c == ",":
            # Peek ahead: if only whitespace stands between this comma and a
            # closing brace / bracket, it is a trailing comma – drop it.
            j = i + 1
            while j < n and text[j] in " \t\n\r":
                j += 1
            if j < n and text[j] in "}]":
                pass  # skip trailing comma
            else:
                result.append(c)
        else:
            result.append(c)
        i += 1

    return "".join(result)


def _extract_json_object(text: str, start: int) -> str:
    """Return the first complete JSON object in *text* beginning at *start*.

    Uses brace counting so that deeply nested objects are handled correctly,
    even when the source text is a JavaScript assignment inside an HTML
    ``<script>`` block.
    """
    if text[start] != "{":
        raise ValueError(
            f"Expected '{{' at position {start}, got {text[start]!r}"
        )
    depth = 0
    i = start
    in_string = False
    escape_next = False
    while i < len(text):
        c = text[i]
        if escape_next:
            escape_next = False
        elif c == "\\" and in_string:
            escape_next = True
        elif c == '"':
            in_string = not in_string
        elif not in_string:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        i += 1
    raise ValueError("Unterminated JSON object – brace mismatch")


def post_process_html(html_path: Path) -> bool:
    """Reduce the size of an exported Marimo HTML file.

    Marimo's ``export html`` command embeds the entire notebook output state
    (charts, tables, cell outputs …) as a large inline JSON blob inside a
    ``<script data-marimo="true">`` tag.  For data-heavy notebooks this blob
    can exceed 25 MB, making the page slow to load and expensive to store in
    git.

    This function:

    1. Extracts ``window.__MARIMO_MOUNT_CONFIG__`` and gzip-compresses it to a
       ``<stem>.data.gz`` sidecar file alongside the HTML.  Compression
       typically achieves ~90% reduction (25 MB → ~2 MB).

    2. Replaces the Marimo CDN ``<script type="module">`` tag (in ``<head>``)
       with a compact async loader module that:

       a. Fetches and decompresses the sidecar file via the ``DecompressionStream``
          Web API (supported by all modern browsers).
       b. Sets ``window.__MARIMO_MOUNT_CONFIG__`` before Marimo initialises.
       c. Dynamically imports the Marimo frontend bundle from the same CDN URL,
          so Marimo runs only after the config is ready.

    3. Removes the now-redundant large inline config ``<script>`` block from
       ``<body>``.

    4. Adds ``<link rel="preload">`` / ``<link rel="modulepreload">`` hints in
       ``<head>`` so the browser starts fetching both the data sidecar and the
       Marimo bundle in parallel while it parses the (now tiny) HTML shell.

    Returns ``True`` on success.  On a non-fatal warning the original file is
    left unchanged and ``True`` is still returned so the overall export is not
    aborted.
    """
    html = html_path.read_text(encoding="utf-8")
    original_size = len(html)

    # ── 1. Locate window.__MARIMO_MOUNT_CONFIG__ ──────────────────────────
    MARKER = "window.__MARIMO_MOUNT_CONFIG__ = "
    marker_idx = html.find(MARKER)
    if marker_idx == -1:
        # No config blob present (e.g. empty / placeholder notebook).
        return True

    json_start = html.find("{", marker_idx + len(MARKER))
    if json_start == -1:
        print(
            f"  WARNING: could not locate JSON start in {html_path.name}",
            file=sys.stderr,
        )
        return True

    try:
        config_json = _extract_json_object(html, json_start)
        config_json = _strip_trailing_commas(config_json)
        json.loads(config_json)  # validate
    except (ValueError, json.JSONDecodeError) as exc:
        print(
            f"  WARNING: could not extract JSON from {html_path.name}: {exc}",
            file=sys.stderr,
        )
        return True

    # ── 2. Gzip-compress and save the sidecar data file ───────────────────
    data_gz_path = html_path.with_suffix(".data.gz")
    compressed = gzip.compress(config_json.encode("utf-8"), compresslevel=9)
    data_gz_path.write_bytes(compressed)

    orig_kb = len(config_json) / 1024
    comp_kb = len(compressed) / 1024
    ratio = round(100 * len(compressed) / len(config_json))
    print(f"    data: {orig_kb:,.0f} KB → {comp_kb:,.0f} KB ({ratio}% of original)")

    data_filename = data_gz_path.name

    # ── 3. Find the Marimo CDN module script URL ───────────────────────────
    module_match = _MARIMO_MODULE_RE.search(html)
    marimo_url = module_match.group(1) if module_match else None

    # ── 4. Build the async loader that replaces the CDN module script ──────
    #
    # The loader is a <script type="module"> (deferred by default) that:
    #   • Fetches the gzip sidecar and decompresses via DecompressionStream.
    #   • Sets window.__MARIMO_MOUNT_CONFIG__ before importing Marimo.
    #   • Dynamically imports the Marimo bundle (runs after config is ready).
    #
    # Because the loader is placed where the original CDN <script type="module">
    # was (in <head>), it executes after HTML parsing – the same timing as the
    # original inline assignment, so Marimo sees a fully populated config.
    #
    # Browser support: DecompressionStream is available in Chrome 80+, Edge 80+,
    # Firefox 113+, and Safari 16.4+ (released March 2023).
    _err_html = (
        "<div style='padding:2rem;font-family:sans-serif;color:#dc2626'>"
        "<strong>Failed to load notebook data</strong><br>"
        "Please reload the page or check your network connection.</div>"
    )
    if marimo_url:
        loader = (
            '<script type="module">\n'
            "(async () => {\n"
            "  try {\n"
            f"    const res = await fetch('./{data_filename}');\n"
            "    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);\n"
            "    const ds = new DecompressionStream('gzip');\n"
            "    window.__MARIMO_MOUNT_CONFIG__ = JSON.parse(\n"
            "      await new Response(res.body.pipeThrough(ds)).text()\n"
            "    );\n"
            f"    await import('{marimo_url}');\n"
            "  } catch (err) {\n"
            "    const root = document.getElementById('root');\n"
            f"    if (root) root.innerHTML = {json.dumps(_err_html)};\n"
            "    console.error('Notebook loader error:', err);\n"
            "  }\n"
            "})();\n"
            "</script>"
        )
    else:
        # Fallback: CDN URL not found – inject a config-only loader before </body>.
        loader = (
            '<script type="module">\n'
            "(async () => {\n"
            "  try {\n"
            f"    const res = await fetch('./{data_filename}');\n"
            "    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);\n"
            "    const ds = new DecompressionStream('gzip');\n"
            "    window.__MARIMO_MOUNT_CONFIG__ = JSON.parse(\n"
            "      await new Response(res.body.pipeThrough(ds)).text()\n"
            "    );\n"
            "  } catch (err) {\n"
            "    const root = document.getElementById('root');\n"
            f"    if (root) root.innerHTML = {json.dumps(_err_html)};\n"
            "    console.error('Notebook loader error:', err);\n"
            "  }\n"
            "})();\n"
            "</script>"
        )

    # ── 5. Patch the HTML ─────────────────────────────────────────────────
    #
    # IMPORTANT: compute all positions against the ORIGINAL html *before* any
    # substitution.  The loader we insert in 5b itself contains the MARKER
    # string; searching for it after insertion would land on the wrong spot.
    # We apply changes right-to-left (config removal first, then module swap)
    # so earlier byte offsets are unaffected by later modifications.

    # Pre-compute the config <script data-marimo="true"> block boundaries.
    cfg_script_open = html.rfind('<script data-marimo="true">', 0, marker_idx)
    close_tag_pos = html.find("</script>", marker_idx)
    cfg_script_close = close_tag_pos + len("</script>")
    if cfg_script_open == -1 or close_tag_pos == -1:
        print(
            f"  WARNING: could not locate config script block in {html_path.name}",
            file=sys.stderr,
        )
        return True

    # 5a. Remove the inline config block.  This is the rightmost change, so
    #     it does not shift positions of anything earlier in the document.
    html = html[:cfg_script_open] + html[cfg_script_close:]

    # 5b. Replace the CDN module <script> with the async loader.  The config
    #     block was *after* the module tag, so 5a did not shift module_match's
    #     span.
    if module_match:
        html = (
            html[: module_match.start()] + loader + html[module_match.end() :]
        )
    else:
        html = html.replace("</body>", loader + "\n</body>", 1)

    # 5c. Add <link rel="preload"> for the data sidecar so the browser starts
    #     fetching it while the lightweight HTML shell is still parsing.
    # No crossorigin attribute: the sidecar is same-origin, so adding
    # crossorigin would cause the preload to be cached separately from the
    # actual fetch and result in a double download.
    preload = (
        f'  <link rel="preload" href="./{data_filename}" as="fetch">\n'
    )
    html = html.replace("</head>", preload + "</head>", 1)

    # 5d. Add <link rel="modulepreload"> for the Marimo CDN bundle so the
    #     browser can start fetching it in parallel with the data file.
    # crossorigin is required for cross-origin module scripts.
    if marimo_url:
        modpreload = (
            f'  <link rel="modulepreload" href="{marimo_url}" crossorigin>\n'
        )
        html = html.replace("</head>", modpreload + "</head>", 1)

    html_path.write_text(html, encoding="utf-8")

    new_kb = html_path.stat().st_size / 1024
    print(
        f"    html: {original_size / 1024:,.0f} KB → {new_kb:,.0f} KB"
    )
    return True


def find_notebooks():
    for path in sorted(NOTEBOOKS_DIR.rglob("*.py")):
        rel = path.relative_to(NOTEBOOKS_DIR)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        yield path


def export_notebook(src: Path) -> bool:
    rel = src.relative_to(NOTEBOOKS_DIR)
    out = OUTPUT_DIR / rel.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Exporting {rel} → {out.relative_to(REPO_ROOT)}")
    result = subprocess.run(
        ["marimo", "export", "html", "--no-include-code", str(src), "-o", str(out), "-f"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR exporting {rel}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    return post_process_html(out)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Export marimo notebooks to HTML.")
    parser.add_argument(
        "notebooks",
        nargs="*",
        metavar="NOTEBOOK",
        help="Specific notebook path(s) relative to notebooks/ (e.g. data/models/events.py). "
             "If omitted, all notebooks are exported.",
    )
    args = parser.parse_args()

    if args.notebooks:
        notebooks = []
        for n in args.notebooks:
            path = NOTEBOOKS_DIR / n
            if not path.exists():
                print(f"Not found: {path}", file=sys.stderr)
                sys.exit(1)
            notebooks.append(path)
    else:
        notebooks = list(find_notebooks())

    if not notebooks:
        print("No notebooks found.")
        return

    print(f"Found {len(notebooks)} notebook(s) to export.\n")
    failures = []
    for nb in notebooks:
        ok = export_notebook(nb)
        if not ok:
            failures.append(nb)

    print(f"\nDone. {len(notebooks) - len(failures)}/{len(notebooks)} succeeded.")
    if failures:
        print("Failed:")
        for f in failures:
            print(f"  {f.relative_to(NOTEBOOKS_DIR)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
