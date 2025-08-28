The grayscale of individual pixel data is analysed for the brightness and a
char value is assigned to it, ' ' for rgb(0, 0, 0) and '$' for rgb(255, 255,
255). Since all the pixels are mapped and converted to their char counterpart
which taken up a lot more pixel as compared to a single pixel, the original
image is to be scaled down to obtain legible ASCII counterpart. The font color
is set according to the rgb of the pixel.

## Usage

```
python ascii.py --format image  # default
python ascii.py --format text   # write ASCII characters to a .txt file
python ascii.py --format html   # write colored characters to a .html file
```

