"""Streamlit GUI launcher.

Run with:
  python -m ascii_art.gui

This spawns:
  python -m streamlit run <repo>/ascii_art/streamlit_gui.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    app_path = Path(__file__).with_name("streamlit_gui.py")
    if not app_path.exists():
        print(f"Missing Streamlit app at: {app_path}")
        return 1

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), *argv]
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        print("Streamlit is not installed. Install it first:")
        print("  python -m pip install streamlit")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
