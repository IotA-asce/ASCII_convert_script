# ASCII Convert Script

Convert images into colorized ASCII art. Each pixel is mapped to a character
whose "ink" coverage approximates the pixel brightness.

## Installation

```bash
python -m pip install -r requirements.txt
```

Optional packages:
- `tqdm` adds a progress bar to the CLI.

## Command line usage

```bash
python -m ascii_art.cli --input "image.jpg" --scale 0.2 --brightness 30 --format image
```

Notes
- `--input` can be either:
  - a file name located in `assets/input/` (example: `--input "image.jpg"`), or
  - an absolute path to an image (example: `--input "/abs/path/image.jpg"`).
- If you want to pass a relative path outside `assets/input/`, use an absolute
  path instead (the CLI currently validates `--input` in a way that can reject
  other relative paths).
- By default, outputs are written to `assets/output/` (gitignored) unless you
  pass `--output-dir`.

### Options

Core
- `--input <name-or-abs-path>`: input image (see notes above).
- `--batch <directory>`: convert every file in a directory.
- `--output-dir <dir>`: where outputs are written (default from `config.ini`).
- `--format {image,text,html,ansi}`:
  - `image`: write a PNG
  - `text`: write a UTF-8 `.txt`
  - `html`: write a UTF-8 `.html` with colored spans
  - `ansi`: write ANSI-colored output to stdout (no files written)

Rendering
- `--scale <float>`: output scaling factor (0 < scale <= 1).
- `--brightness <int>`: background brightness (0-255).
- `--mono`: render in grayscale instead of color.

Character set / fonts
- `--dynamic-set`: generate a brightness-ranked character set via `ascii_art.charset`.
- `--font <path>`: optional TTF font path (used for dynamic set generation and
  for rendering characters when writing images).

Video/webcam
- `--video <path>`: convert frames from a video file.
- `--webcam`: convert frames from the default webcam.

If no `--input` is supplied the program will prompt for a file from
`assets/input`.

### Examples

Convert an image from `assets/input/` to an output PNG
```bash
python -m ascii_art.cli --input "IMG20230214135212.jpg" --scale 0.2 --brightness 30 --format image
```

Render ANSI output directly in your terminal
```bash
python -m ascii_art.cli --input "IMG20230214135212.jpg" --scale 0.2 --format ansi
```

Convert a whole directory
```bash
python -m ascii_art.cli --batch "assets/input" --format text --output-dir "assets/output"
```

Use a custom font and a dynamically generated character set
```bash
python -m ascii_art.cli --input "IMG20230214135212.jpg" --dynamic-set --font "/path/to/font.ttf" --format image
```

## GUI usage

Launch the Streamlit interface with:

```bash
python -m ascii_art.gui
```

This will start a local Streamlit server and open a browser window.

You can also run it directly:
```bash
streamlit run ascii_art/streamlit_gui.py
```

Use the uploader (supports drag and drop), adjust the scale/brightness, and the
ASCII preview will update automatically.

Live mode
- Open the "Live (Webcam + Audio)" tab to convert a webcam feed in real time.
- The microphone level inversely modulates detail (louder sound -> less detail).
- Your browser will prompt for camera/microphone permissions.

## Video and webcam

Video/webcam conversion requires extra dependencies that are not listed in
`requirements.txt`:

```bash
python -m pip install opencv-python imageio
```

Example
```bash
python -m ascii_art.cli --video "/path/to/movie.mp4" --scale 0.2 --format image
```

## Generating custom character sets

`ascii_art/charset.py` exposes `generate_char_array` which analyses each glyph of
a font and sorts characters by coverage. The CLI `--dynamic-set` flag leverages
this function automatically.

## Configuration

- CLI defaults live in `config.ini` and are used when flags are omitted.
- GUI settings are persisted to `config.json` (delete it to reset).

## Testing

Run the unit tests with:

```bash
pytest
```

Run a single test
```bash
pytest tests/test_ascii.py::test_convert_image_text_output
```

## Troubleshooting

- GUI import errors: `tkinter` is part of the stdlib but may require an OS
  package; `tkinterdnd2` must be installed for drag-and-drop.
- `--format ansi` is meant for terminal display; it prints to stdout and does
  not create output files.

## Contributing

Issues and pull requests are welcome.
See `CONTRIBUTING.md` for dev workflows.

## License

MIT
