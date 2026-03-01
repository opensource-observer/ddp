#!/usr/bin/env python3
"""
Serve all marimo notebooks from the notebooks directory.
Run this script to start a marimo server that serves all notebooks.
"""

import marimo
from pathlib import Path
import os

# Get the current directory (where this script is located)
current_dir = Path(__file__).parent
notebooks_dir = current_dir / "notebooks"

# Load local .env (so notebook kernels inherit OSO_API_KEY, etc.)
def _load_dotenv_file(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        # Handle common `.env` patterns like `KEY=value # comment`
        if value and value[0] in ("'", '"') and value[-1:] == value[0]:
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()

        os.environ.setdefault(key, value)


_load_dotenv_file(current_dir / ".env")

# Create the ASGI application using the builder pattern
# Need to call .build() to get the actual ASGI app
app = (
    marimo.create_asgi_app()
    .with_dynamic_directory(path="/notebooks", directory=str(notebooks_dir))
    .build()
)

if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required to run this server.")
        print("Install it with: pip install uvicorn")
        exit(1)
    
    if "OSO_API_KEY" not in os.environ:
        print("Warning: OSO_API_KEY is not set. OSO queries in notebooks may fail with 401.")
        print("Create `.env` from `.env.example` and add your OSO API key.\n")

    print(f"Serving marimo notebooks from: {notebooks_dir}")
    print("Notebooks will be available at: http://localhost:8000/notebooks/{notebook-name}")
    print("For example: http://localhost:8000/notebooks/home for notebooks/home.py")
    print("Press Ctrl+C to stop the server\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
