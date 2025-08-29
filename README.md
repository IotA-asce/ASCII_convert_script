# ASCII Convert Script

Convert images into colorized ASCII art. Each pixel is mapped to a character
whose "ink" coverage approximates the pixel brightness.

## Installation

```bash
pip install -r requirements.txt
```

Optional packages:
- `tkinter` (usually included with Python) and `tkinterdnd2` for the Tk GUI.
- `tqdm` adds a progress bar to the CLI.

## Command line usage

```bash
python ascii.py --input image.jpg --scale 0.2 --brightness 30 --mono
```

### Options

- `--format {image,text,html}`: choose between PNG image output, plain text or
  HTML with coloured spans.
- `--batch <directory>`: convert every image in a directory.
- `--dynamic-set`: build a brightness-ranked character set using
  `ascii_art.charset`.
- `--mono`: render ASCII output in grayscale instead of colour.

If no `--input` is supplied the program will prompt for a file from
`assets/input`.

## GUI usage

Launch the Tkinter interface with:

```bash
python -m ascii_art.gui
```

Use the file picker or drag and drop an image onto the window, adjust the scale
and brightness sliders, and the ASCII preview will update automatically.

## Generating custom character sets

`ascii_art/charset.py` exposes `generate_char_array` which analyses each glyph of
a font and sorts characters by coverage. The CLI `--dynamic-set` flag leverages
this function automatically.

## Testing

Run the unit tests with:

```bash
pytest
```

## Contributing

Issues and pull requests are welcome.

## License

MIT
