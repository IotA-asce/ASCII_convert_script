# Contributing

Thanks for contributing!

## Setup

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

## GUI (Streamlit)

```bash
python -m ascii_art.gui
```

Optional (video/webcam)
```bash
python -m pip install opencv-python imageio
```

## Tests

Run the full suite
```bash
pytest
```

Run a single test (node id)
```bash
pytest tests/test_ascii.py::test_convert_image_ansi_stdout
```

Run tests by keyword
```bash
pytest -k "convert_image and mono"
```

Fast sanity check
```bash
python -m compileall ascii_art
```

## Style

- Follow `AGENTS.md` for code style guidelines.
- No formatter/linter is enforced currently; if you use one locally, prefer
  `ruff` and keep config in `pyproject.toml`.

## Repository hygiene

- Do not commit generated outputs; `assets/output/` is gitignored.
- Prefer `tmp_path` for test outputs.
- Avoid adding `sys.path` hacks in production code; tests already handle imports.
