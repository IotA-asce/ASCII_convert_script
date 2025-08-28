# ASCII Convert Script

Convert images (PNG, JPG, GIF, BMP, etc.) into colorized ASCII art. Each pixel
is mapped to a character whose "ink" coverage approximates the pixel
brightness.

## Installation

```bash
pip install pillow
```

## Command line usage

```bash
python ascii.py --input image.jpg --scale 0.2 --brightness 30
```

### Options

- `--format {image,text,html}`: choose between PNG image output, plain text or
  HTML with coloured spans.
- `--batch <directory>`: convert every image in a directory.
- `--dynamic-set`: build a brightness-ranked character set using
  `computeUnicode.py`.

If no `--input` is supplied the program will prompt for a file from
`assets/input`.

## Graphical interface

A Tkinter based GUI is available for interactive conversions:

```bash
python gui.py
```

Use the **Browse** button to pick an image (any common format) and tweak the
scale, brightness and output format. Converted images are previewed directly in
the window when the image output mode is selected.

## Generating custom character sets

`computeUnicode.py` exposes `generate_char_array` which analyses each glyph of a
font and sorts characters by coverage. The CLI `--dynamic-set` flag leverages
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
