# Agent Notes (ASCII_convert_script)

This repository converts images (and optionally video/webcam frames) into ASCII
art using Pillow. There is a CLI, a Streamlit GUI, and a small pytest suite.

Repo layout
- `ascii_art/` : library + entrypoints (`cli.py`, `gui.py`)
- `assets/input/` : sample inputs (tests may create files here)
- `assets/output/` : generated outputs (gitignored)
- `config.ini` : CLI defaults
- `config.json` : GUI persisted settings
- `tests/` : pytest tests

Cursor/Copilot instructions
- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` found
  at the time this file was generated.


## Setup

Python
- Target Python: 3.10+ (code uses `str | None` type unions).

Install dependencies
```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

Notes on dependencies
- Required: `pillow`
- Optional (listed in `requirements.txt`): `tqdm` (CLI progress), `streamlit` + `streamlit-webrtc` + `numpy` (GUI, live webcam/audio)
- Optional (not in `requirements.txt`):
  - Video/webcam: `opencv-python` (imports as `cv2`), `imageio`


## Commands (Build / Lint / Test)

There is no packaging build step (no `pyproject.toml` / `setup.py`). Treat
"build" as "install deps + run checks".

Run the CLI
```bash
python -m ascii_art.cli --input "assets/input/your_image.jpg" --scale 0.2 --brightness 30 --format image
```

Run the GUI
```bash
python -m ascii_art.gui
```

Run tests
```bash
pytest
```

Run a single test (by node id)
```bash
pytest tests/test_ascii.py::test_convert_image_text_output
```

Run tests matching a substring
```bash
pytest -k "convert_image and ansi"
```

Fast sanity check (syntax/type parse)
```bash
python -m compileall ascii_art
```

Lint/format (optional; not currently enforced by repo)
- If you introduce linting, prefer `ruff` (lint + import sorting) and keep the
  config in `pyproject.toml`.
```bash
python -m pip install ruff
ruff check .
ruff format .
```


## Code Style Guidelines

General
- Prefer small, composable functions. Keep `ascii_art/converter.py` as the
  low-level conversion library and keep user interaction in `ascii_art/cli.py`
  and `ascii_art/gui.py`.
- Default encoding for text IO is UTF-8. This matters because the character
  sets include non-ASCII glyphs and HTML/text outputs are UTF-8.

Imports
- Standard library first, then third-party, then local imports.
- Prefer absolute imports within the package (`from ascii_art import ...`) in
  GUI code, and relative imports (`from .converter import ...`) in package
  internals.
- Do not add `sys.path` manipulation in new modules. Tests already do
  `sys.path.insert(...)` to import from the repo root; keep production code
  clean.

Formatting
- 4-space indentation.
- Keep lines reasonably short (aim for ~88-100 chars). Wrap long argument lists
  with one argument per line, trailing commas.
- Use double quotes for user-facing strings unless existing surrounding code
  consistently uses single quotes.

Types
- Add type hints for new/changed public functions and for complex data
  structures.
- Use modern typing (`list[str]`, `dict[str, ...]`, `str | None`) since Python
  3.10+ is assumed.
- Avoid over-typing simple scripts; focus on signatures and return types.

Naming
- Modules/files: `snake_case.py`.
- Functions/variables: `snake_case`.
- Classes: `CapWords`.
- Constants: `UPPER_SNAKE_CASE` (see `ascii_art/converter.py`).
- Private helpers: prefix with `_` (see `_validate_scale` in `ascii_art/cli.py`).

Error handling
- Library functions should prefer raising exceptions for programmer errors
  (invalid arguments) and returning early only for expected user/runtime errors
  where the calling surface is interactive.
- CLI surface (`ascii_art/cli.py`): validate inputs early and print a clear
  message before returning (current behavior).
- Optional dependencies: follow the existing pattern
  `try: import ... except ModuleNotFoundError: ...` and provide a graceful
  fallback or a helpful error.
- When catching broad exceptions (mostly GUI worker threads), keep the except
  block narrow and avoid swallowing errors silently; if you need to suppress,
  log to stderr or show a messagebox.

Filesystem and paths
- Prefer `pathlib.Path` for new code; accept both `str` and `PathLike` inputs
  where convenient.
- Do not commit generated outputs. `assets/output/` is intentionally gitignored.
- Keep test outputs in `tmp_path` and avoid writing large fixtures into the
  repo.

CLI/GUI behavior
- `ascii_art/cli.py` reads defaults from `config.ini`. If you add new CLI flags,
  also add config defaults (with fallbacks) and update `README.md` accordingly.
- `ascii_art/gui.py` persists settings to `config.json`. Keep the schema
  backward compatible (handle missing keys, tolerate invalid JSON).

Character sets
- The default `char_array` includes non-ASCII glyphs. Preserve file encodings
  and avoid accidental re-encoding when editing.
- `ascii_art/charset.py` generates a brightness-ranked set and caches it in
  `ascii_art/char_cache.json` (generated file). Do not commit the cache unless
  the project decides to vendor it explicitly.

Testing guidelines
- Tests use pytest and live in `tests/`.
- Prefer `tmp_path` for outputs and `capsys` for stdout capture.
- When adding functionality, add at least one focused unit test and, if it
  touches output formatting, assert on the exact output (as done for ANSI).
