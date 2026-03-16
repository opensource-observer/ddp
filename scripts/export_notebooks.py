"""
Export all notebooks to static HTML using `marimo export html`.

Auto-discovers *.py files under notebooks/, excluding:
  - notebooks/__marimo__/ (marimo metadata)

Outputs to app/public/notebooks/ mirroring the source directory structure.
Insight pages (insights/*.py) are included — their HTML is served via MarimoIframe.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
OUTPUT_DIR = REPO_ROOT / "app" / "public" / "notebooks"

EXCLUDE_DIRS = {"__marimo__"}


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
    return True


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
