import html
import os
import sys
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageFont, ImageSequence

from .charset import generate_char_array


# Pillow changed resampling constants to an enum; use getattr for compatibility.
_RESAMPLE_NEAREST = getattr(getattr(Image, "Resampling", Image), "NEAREST")

try:
    from tqdm import tqdm
except ModuleNotFoundError:  # pragma: no cover - fallback when tqdm is missing
    tqdm = None

# Default character array – can be replaced by a dynamically generated one
char_array = [
    " ",
    "`",
    "¨",
    "·",
    "¸",
    ".",
    "-",
    "'",
    ",",
    "¹",
    ":",
    "_",
    "¯",
    "~",
    "¬",
    "¦",
    ";",
    "¡",
    "!",
    "÷",
    "*",
    "*",
    "ı",
    "|",
    "+",
    "<",
    ">",
    "/",
    "=",
    "»",
    "«",
    "ì",
    "í",
    "ï",
    "i",
    "^",
    "º",
    "_r",
    "L",
    "ª",
    "®",
    "ī",
    "ĩ",
    "î",
    "ĭ",
    "l",
    "¿",
    "J",
    "×",
    "v",
    "?",
    "c",
    "į",
    ")",
    "Ĺ",
    "Ŀ",
    "(",
    "Y",
    "T",
    "Ļ",
    "Ľ",
    "ĺ",
    "7",
    "¤",
    "t",
    "ľ",
    "ŀ",
    "Ł",
    "}",
    "{",
    "F",
    "ċ",
    "ļ",
    "s",
    "ĸ",
    "Ý",
    "[",
    "x",
    "ć",
    "z",
    "ç",
    "1",
    "I",
    "]",
    "ł",
    "j",
    "Ĵ",
    "C",
    "y",
    "V",
    "£",
    "5",
    "2",
    "f",
    "3",
    "ĉ",
    "č",
    "n",
    "Ì",
    "Í",
    "İ",
    "¢",
    "ĵ",
    "U",
    "X",
    "Ć",
    "Z",
    "Ċ",
    "S",
    "u",
    "Ï",
    "Þ",
    "P",
    "Į",
    "Ç",
    "K",
    "A",
    "o",
    "ÿ",
    "ý",
    "a",
    "e",
    "4",
    "Ĭ",
    "E",
    "Î",
    "Č",
    "Ĉ",
    "Ī",
    "Ĩ",
    "Ú",
    "Ù",
    "ń",
    "ņ",
    "ŉ",
    "k",
    "Ü",
    "Á",
    "À",
    "ù",
    "ú",
    "ü",
    "¥",
    "ė",
    "w",
    "H",
    "È",
    "É",
    "Ä",
    "Å",
    "ö",
    "Ė",
    "ò",
    "G",
    "ó",
    "Ķ",
    "ä",
    "Û",
    "á",
    "à",
    "Ą",
    "ë",
    "é",
    "è",
    "_h",
    "ą",
    "ę",
    "Ë",
    "å",
    "ñ",
    "ň",
    "Ę",
    "O",
    "Ă",
    "$",
    "Â",
    "û",
    "Ĕ",
    "Ā",
    "Ě",
    "Ê",
    "Ã",
    "Æ",
    "R",
    "ā",
    "D",
    "ē",
    "ķ",
    "õ",
    "½",
    "Ē",
    "p",
    "ã",
    "ô",
    "ă",
    "Ġ",
    "â",
    "ĕ",
    "9",
    "6",
    "ê",
    "ě",
    "q",
    "¼",
    "Ĳ",
    "m",
    "N",
    "%",
    "0",
    "Ģ",
    "ħ",
    "_b",
    "Ò",
    "Ó",
    "#",
    "ø",
    "_d",
    "Ö",
    "Ĥ",
    "Ğ",
    "§",
    "Ĝ",
    "W",
    "M",
    "B",
    "æ",
    "Ð",
    "Đ",
    "Q",
    "Ô",
    "©",
    "Ń",
    "Ħ",
    "8",
    "ĥ",
    "Õ",
    "_g",
    "Ď",
    "Ņ",
    "ĳ",
    "đ",
    "ß",
    "þ",
    "Ň",
    "ð",
    "@",
    "Ŋ",
    "Ñ",
    "¾",
    "ġ",
    "Ø",
    "ģ",
    "ď",
    "ğ",
    "&",
    "ĝ",
]


def _recompute_interval():
    global CHAR_LENGTH, INTERVAL, CHAR_LUT
    CHAR_LENGTH = len(char_array)
    INTERVAL = CHAR_LENGTH / 256
    # Map grayscale values [0..255] directly to a character.
    # Using integer math avoids per-pixel floating point work.
    CHAR_LUT = tuple(char_array[(i * CHAR_LENGTH) // 256] for i in range(256))


_recompute_interval()

ONE_CHAR_WIDTH = 10
ONE_CHAR_HEIGHT = 18

# Cache glyph masks for faster `format=image` rendering.
# Keyed by (font_key, cell_width, cell_height, char_set).
_GLYPH_MASK_CACHE: dict[
    tuple[str, int, int, tuple[str, ...]], dict[str, Image.Image]
] = {}


def _glyph_masks(
    *,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    cell_width: int,
    cell_height: int,
    font_key: str,
    chars: list[str],
) -> dict[str, Image.Image]:
    key = (font_key, int(cell_width), int(cell_height), tuple(chars))
    cached = _GLYPH_MASK_CACHE.get(key)
    if cached is not None:
        return cached

    masks: dict[str, Image.Image] = {}
    # Preserve order while removing duplicates.
    unique_chars = list(dict.fromkeys(chars))
    for ch in unique_chars:
        im = Image.new("L", (int(cell_width), int(cell_height)), color=0)
        d = ImageDraw.Draw(im)
        d.text((0, 0), ch, font=font, fill=255)
        masks[ch] = im
    _GLYPH_MASK_CACHE[key] = masks
    return masks


OUTPUT_IMAGE_PREFIX = "FrameOut"  # output image file name prefix
INPUT_FILE_PREFIX = "Frame"  # input file name prefix


class _DummyLoader:
    def __init__(self, total: int | None):
        self.total = total or 0
        self.count = 0

    def update(self, n: int = 1) -> None:
        if not self.total:
            return
        self.count += n
        percent = (self.count / self.total) * 100
        sys.stdout.write(f"\rprocessing - {percent}\t%")

    def close(self) -> None:
        if self.total:
            sys.stdout.write("\n")


def load_char_array(dynamic: bool = False, font_path: str | None = None) -> None:
    """Load the character array either statically or by computing it.

    If ``dynamic`` is ``True`` and ``font_path`` points to a valid TTF file,
    that font is used to generate the array. If the font cannot be loaded the
    default character set is used instead.
    """

    global char_array
    if dynamic:
        try:
            char_array = generate_char_array(font_path)
        except OSError:
            print(f"Could not load font '{font_path}', using default set")
            char_array = generate_char_array(None)
    _recompute_interval()


def get_char(input_int: int) -> str:
    """
    Returns a character from the `char_array` list based on the given `input_int`
    which represents the brightness value of the pixel at hand

    Args:
        input_int (int): The brightness value (grayscale) of a pixel that is being worked on

    Returns:
        A character (string) from the `char_array` list
    """
    if input_int <= 0:
        return CHAR_LUT[0]
    if input_int >= 255:
        return CHAR_LUT[255]
    return CHAR_LUT[input_int]


def list_files_from_assets():
    """
    Lists all the image file available in the "./assets/input/" directory,
    prompts the user to select one of them, and returns the name of the selected file.

    Returns:
        A string that represents the name of the selected image file.

    Example:
        If the "./assets/input/" directory contains three image files:

            "image1.jpg", "image2.jpg" and "image3.jpg"

        then calling `list_files_from_assets()` will output:

        Available choice ->

        _________________________________________________

        1 - image1.jpg
        2 - image2.jpg
        3 - image3.jpg

        _________________________________________________

        The user will be prompted to enter a choice, and if they enter "2", the function
        will return "image2.jpg".
    """
    list_of_images = os.listdir("./assets/input/")
    index = 1

    print("Available choice -> \n")
    print_divider()
    for image in list_of_images:
        print(f"{index} - {image}")
        index += 1
    print_divider()
    index = int(input("Enter the choice : "))
    return list_of_images[index - 1]


def convert_image(
    input_name: Any,
    scale_factor: float = 0.2,
    bg_brightness: int = 30,
    output_dir: str = "./assets/output",
    output_format: str = "image",
    base_name: str | None = None,
    mono: bool = False,
    font_path: str | None = None,
    grayscale_mode: str = "avg",
    dither: str = "none",
    assemble: bool = False,
    gif_fps: float | None = None,
    gif_loop: int = 0,
    cell_width: int = ONE_CHAR_WIDTH,
    cell_height: int = ONE_CHAR_HEIGHT,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """
    Converts an image file to an ASCII art representation, and saves the output
    image to ``output_dir`` with a filename that includes the chosen parameters
    and the input filename.

    Args:
        input_name (str):   The name of the image file to be converted, including the
                            file extension.
        scale_factor (float):   The scaling factor for the output image. Default is 0.2,
                                which means the output image will be 20% of the size of the
                                input image times the width and height of one character.
        bg_brightness (int):    The brightness level of the output image background. Default is
                                30, which is close to medium gray.
        output_dir (str):   Directory where the resulting image will be saved.
                            Defaults to ``./assets/output``.
        mono (bool): Render characters in grayscale instead of colour.
        font_path (str, optional): Path to a TTF font used for rendering.
        grayscale_mode (str): How RGB pixels are mapped to a single brightness
            value for character selection. One of:
            - `avg`: average of channels (current behavior)
            - `luma601`: BT.601 luma (integer approximation)
            - `luma709`: BT.709 luma (integer approximation)
        dither (str): Optional error-diffusion dithering applied to brightness
            before character selection. One of: `none`, `floyd-steinberg`,
            `atkinson`.
        assemble (bool): If the input is an animated image and `output_format`
            is `image`, assemble frames into a single animated GIF.
        gif_fps (float, optional): When assembling an animated GIF, override the
            per-frame duration using a fixed frames-per-second value.
        gif_loop (int): When assembling an animated GIF, the GIF loop count
            passed to Pillow. 0 means loop forever.
        cell_width (int): Width (in pixels) of one character cell when rendering
            `format=image`. Also used for aspect correction when resizing.
        cell_height (int): Height (in pixels) of one character cell when
            rendering `format=image`. Also used for aspect correction when
            resizing.
        progress_callback (callable, optional): Callback invoked as
            ``progress_callback(current, total)`` to report the number of
            processed rows.

    Returns:
        None. The output image is saved to a file.

    Example:
        If the "./assets/input/" directory contains an image file called
        ``image1.jpg``, calling ``convert_image("image1.jpg", 0.1, 50)`` will
        create an ASCII art representation of the image with a scale factor of
        0.1 and a background brightness level of 50, and save the output image
        to ``./assets/output/O_h:50_f_0.1_image1.jpg``.
    """

    def _resolve_input_image(name, default_base_name: str) -> tuple[Image.Image, str]:
        if isinstance(name, Image.Image):
            return name, default_base_name
        name = os.fspath(name)
        input_path = (
            name
            if os.path.isabs(name) or os.path.exists(name)
            else os.path.join("./assets/input", name)
        )
        try:
            return Image.open(input_path), Path(name).stem
        except FileNotFoundError:
            print(f"Input file '{name}' not found")
            raise

    def _load_font(
        user_font: str | None,
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        windows_font = r"C:\\Windows\\Fonts\\lucon.ttf"
        linux_font = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        if user_font:
            try:
                return ImageFont.truetype(user_font, cell_height)
            except OSError:
                print(f"Could not load font '{user_font}', falling back to defaults")
        if os.path.exists(windows_font):
            return ImageFont.truetype(windows_font, cell_height)
        if os.path.exists(linux_font):
            return ImageFont.truetype(linux_font, cell_height)
        return ImageFont.load_default()

    try:
        _im, resolved_base = _resolve_input_image(input_name, base_name or "frame")
    except FileNotFoundError:
        return
    if base_name is None:
        base_name = resolved_base

    fnt = _load_font(font_path)

    if grayscale_mode not in ("avg", "luma601", "luma709"):
        raise ValueError("grayscale_mode must be one of: avg, luma601, luma709")

    if dither not in ("none", "floyd-steinberg", "atkinson"):
        raise ValueError("dither must be one of: none, floyd-steinberg, atkinson")

    if gif_fps is not None and float(gif_fps) <= 0:
        raise ValueError("gif_fps must be positive")
    gif_loop = int(gif_loop)
    if gif_loop < 0:
        raise ValueError("gif_loop must be >= 0")

    cell_width = int(cell_width)
    cell_height = int(cell_height)
    if cell_width <= 0 or cell_height <= 0:
        raise ValueError("cell_width and cell_height must be positive integers")

    is_animated = getattr(_im, "is_animated", False)
    n_frames = int(getattr(_im, "n_frames", 1)) if is_animated else 1
    frames_iter = ImageSequence.Iterator(_im) if is_animated else (_im,)

    assemble_gif = (
        bool(assemble) and is_animated and output_format == "image" and n_frames > 1
    )
    gif_frames: list[Image.Image] = []
    gif_durations: list[int] = []

    for frame_index, frame in enumerate(frames_iter):
        if is_animated:
            frame = frame.copy()
        frame_duration_ms = int(getattr(frame, "info", {}).get("duration", 40))
        width, height = frame.size
        frame = frame.resize(
            (
                max(1, int(scale_factor * width)),
                max(1, int(scale_factor * height * (cell_width / cell_height))),
            ),
            _RESAMPLE_NEAREST,
        )
        width, height = frame.size
        frame_rgb = frame.convert("RGB")
        rgb_bytes = memoryview(frame_rgb.tobytes())
        stride = width * 3
        lut = CHAR_LUT

        is_avg = grayscale_mode == "avg"
        wr = wg = wb = 0
        if not is_avg:
            if grayscale_mode == "luma601":
                wr, wg, wb = 77, 150, 29
            else:  # luma709
                wr, wg, wb = 54, 183, 19

        levels = CHAR_LENGTH
        levels_m1 = max(1, levels - 1)

        output_image = None
        draw = None
        glyph_masks: dict[str, Image.Image] | None = None
        if output_format == "image":
            output_image = Image.new(
                "RGB",
                (cell_width * width, cell_height * height),
                color=(bg_brightness, bg_brightness, bg_brightness),
            )
            draw = ImageDraw.Draw(output_image)
            font_key = str(getattr(fnt, "path", "") or font_path or "default")
            glyph_masks = _glyph_masks(
                font=fnt,
                cell_width=cell_width,
                cell_height=cell_height,
                font_key=font_key,
                chars=char_array,
            )

        text_lines: list[str] | None = None
        html_lines: list[str] | None = None
        ansi_lines: list[str] | None = None
        if output_format == "text":
            text_lines = []
        elif output_format == "html":
            html_lines = []
        elif output_format == "ansi":
            ansi_lines = []

        progress = (
            None
            if progress_callback
            else loader(
                total=height,
                desc=f"Frame {frame_index + 1}/{n_frames}" if n_frames > 1 else "Rows",
            )
        )
        if progress_callback:
            progress_callback(0, height)
        if output_format == "image":
            assert draw is not None
            assert output_image is not None
            assert glyph_masks is not None
            paste = output_image.paste
            draw_text = draw.text
            x_positions = [x * cell_width for x in range(width)]
            if dither == "none":
                if is_avg:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        y_pos = y * cell_height
                        off = 0
                        for x in range(width):
                            r = row[off]
                            g = row[off + 1]
                            b = row[off + 2]
                            off += 3
                            h = (r + g + b) // 3
                            ch = lut[h]
                            color = (h, h, h) if mono else (r, g, b)
                            mask = glyph_masks.get(ch)
                            if mask is None:
                                draw_text(
                                    (x_positions[x], y_pos),
                                    ch,
                                    font=fnt,
                                    fill=color,
                                )
                            else:
                                paste(color, (x_positions[x], y_pos), mask)
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
                else:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        y_pos = y * cell_height
                        off = 0
                        for x in range(width):
                            r = row[off]
                            g = row[off + 1]
                            b = row[off + 2]
                            off += 3
                            h = (wr * r + wg * g + wb * b) >> 8
                            ch = lut[h]
                            color = (h, h, h) if mono else (r, g, b)
                            mask = glyph_masks.get(ch)
                            if mask is None:
                                draw_text(
                                    (x_positions[x], y_pos),
                                    ch,
                                    font=fnt,
                                    fill=color,
                                )
                            else:
                                paste(color, (x_positions[x], y_pos), mask)
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
            elif dither == "floyd-steinberg":
                err_curr = [0.0] * (width + 2)
                err_next = [0.0] * (width + 2)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    y_pos = y * cell_height
                    err_curr, err_next = err_next, [0.0] * (width + 2)
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        v = float(base) + err_curr[x + 1]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            idx = int(v * levels_m1 / 255.0 + 0.5)
                            if idx < 0:
                                idx = 0
                            elif idx > levels_m1:
                                idx = levels_m1
                            qh = int(idx * 255.0 / levels_m1 + 0.5)
                        err = v - float(qh)
                        err_curr[x + 2] += err * (7.0 / 16.0)
                        err_next[x + 0] += err * (3.0 / 16.0)
                        err_next[x + 1] += err * (5.0 / 16.0)
                        err_next[x + 2] += err * (1.0 / 16.0)

                        ch = lut[qh]
                        color = (qh, qh, qh) if mono else (r, g, b)
                        mask = glyph_masks.get(ch)
                        if mask is None:
                            draw_text(
                                (x_positions[x], y_pos),
                                ch,
                                font=fnt,
                                fill=color,
                            )
                        else:
                            paste(color, (x_positions[x], y_pos), mask)
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
            else:  # atkinson
                err_curr = [0.0] * (width + 4)
                err_next = [0.0] * (width + 4)
                err_next2 = [0.0] * (width + 4)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    y_pos = y * cell_height
                    err_curr, err_next, err_next2 = (
                        err_next,
                        err_next2,
                        [0.0] * (width + 4),
                    )
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        idx0 = x + 2
                        v = float(base) + err_curr[idx0]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            qidx = int(v * levels_m1 / 255.0 + 0.5)
                            if qidx < 0:
                                qidx = 0
                            elif qidx > levels_m1:
                                qidx = levels_m1
                            qh = int(qidx * 255.0 / levels_m1 + 0.5)
                        err = (v - float(qh)) / 8.0
                        err_curr[idx0 + 1] += err
                        err_curr[idx0 + 2] += err
                        err_next[idx0 - 1] += err
                        err_next[idx0 + 0] += err
                        err_next[idx0 + 1] += err
                        err_next2[idx0 + 0] += err

                        ch = lut[qh]
                        color = (qh, qh, qh) if mono else (r, g, b)
                        mask = glyph_masks.get(ch)
                        if mask is None:
                            draw_text(
                                (x_positions[x], y_pos),
                                ch,
                                font=fnt,
                                fill=color,
                            )
                        else:
                            paste(color, (x_positions[x], y_pos), mask)
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
        elif output_format == "text":
            assert text_lines is not None
            if dither == "none":
                if is_avg:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        line_chars: list[str] = []
                        off = 0
                        for _ in range(width):
                            r = row[off]
                            g = row[off + 1]
                            b = row[off + 2]
                            off += 3
                            h = (r + g + b) // 3
                            line_chars.append(lut[h])
                        text_lines.append("".join(line_chars))
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
                else:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        line_chars: list[str] = []
                        off = 0
                        for _ in range(width):
                            r = row[off]
                            g = row[off + 1]
                            b = row[off + 2]
                            off += 3
                            h = (wr * r + wg * g + wb * b) >> 8
                            line_chars.append(lut[h])
                        text_lines.append("".join(line_chars))
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
            elif dither == "floyd-steinberg":
                err_curr = [0.0] * (width + 2)
                err_next = [0.0] * (width + 2)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    err_curr, err_next = err_next, [0.0] * (width + 2)
                    line_chars: list[str] = []
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        v = float(base) + err_curr[x + 1]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            idx = int(v * levels_m1 / 255.0 + 0.5)
                            if idx < 0:
                                idx = 0
                            elif idx > levels_m1:
                                idx = levels_m1
                            qh = int(idx * 255.0 / levels_m1 + 0.5)
                        err = v - float(qh)
                        err_curr[x + 2] += err * (7.0 / 16.0)
                        err_next[x + 0] += err * (3.0 / 16.0)
                        err_next[x + 1] += err * (5.0 / 16.0)
                        err_next[x + 2] += err * (1.0 / 16.0)
                        line_chars.append(lut[qh])
                    text_lines.append("".join(line_chars))
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
            else:  # atkinson
                err_curr = [0.0] * (width + 4)
                err_next = [0.0] * (width + 4)
                err_next2 = [0.0] * (width + 4)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    err_curr, err_next, err_next2 = (
                        err_next,
                        err_next2,
                        [0.0] * (width + 4),
                    )
                    line_chars = []
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        idx0 = x + 2
                        v = float(base) + err_curr[idx0]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            qidx = int(v * levels_m1 / 255.0 + 0.5)
                            if qidx < 0:
                                qidx = 0
                            elif qidx > levels_m1:
                                qidx = levels_m1
                            qh = int(qidx * 255.0 / levels_m1 + 0.5)
                        err = (v - float(qh)) / 8.0
                        err_curr[idx0 + 1] += err
                        err_curr[idx0 + 2] += err
                        err_next[idx0 - 1] += err
                        err_next[idx0 + 0] += err
                        err_next[idx0 + 1] += err
                        err_next2[idx0 + 0] += err
                        line_chars.append(lut[qh])
                    text_lines.append("".join(line_chars))
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
        elif output_format == "html":
            assert html_lines is not None
            if dither == "none":
                if is_avg:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        parts: list[str] = []
                        off = 0
                        for _ in range(width):
                            r = row[off]
                            g = row[off + 1]
                            b = row[off + 2]
                            off += 3
                            h = (r + g + b) // 3
                            ch = lut[h]
                            if mono:
                                cr = cg = cb = h
                            else:
                                cr, cg, cb = r, g, b
                            parts.append(
                                f'<span style="color:rgb({cr},{cg},{cb})">{html.escape(ch)}</span>'
                            )
                        html_lines.append("".join(parts))
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
                else:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        parts: list[str] = []
                        off = 0
                        for _ in range(width):
                            r = row[off]
                            g = row[off + 1]
                            b = row[off + 2]
                            off += 3
                            h = (wr * r + wg * g + wb * b) >> 8
                            ch = lut[h]
                            if mono:
                                cr = cg = cb = h
                            else:
                                cr, cg, cb = r, g, b
                            parts.append(
                                f'<span style="color:rgb({cr},{cg},{cb})">{html.escape(ch)}</span>'
                            )
                        html_lines.append("".join(parts))
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
            elif dither == "floyd-steinberg":
                err_curr = [0.0] * (width + 2)
                err_next = [0.0] * (width + 2)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    err_curr, err_next = err_next, [0.0] * (width + 2)
                    parts: list[str] = []
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        v = float(base) + err_curr[x + 1]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            idx = int(v * levels_m1 / 255.0 + 0.5)
                            if idx < 0:
                                idx = 0
                            elif idx > levels_m1:
                                idx = levels_m1
                            qh = int(idx * 255.0 / levels_m1 + 0.5)
                        err = v - float(qh)
                        err_curr[x + 2] += err * (7.0 / 16.0)
                        err_next[x + 0] += err * (3.0 / 16.0)
                        err_next[x + 1] += err * (5.0 / 16.0)
                        err_next[x + 2] += err * (1.0 / 16.0)

                        ch = lut[qh]
                        if mono:
                            cr = cg = cb = qh
                        else:
                            cr, cg, cb = r, g, b
                        parts.append(
                            f'<span style="color:rgb({cr},{cg},{cb})">{html.escape(ch)}</span>'
                        )
                    html_lines.append("".join(parts))
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
            else:  # atkinson
                err_curr = [0.0] * (width + 4)
                err_next = [0.0] * (width + 4)
                err_next2 = [0.0] * (width + 4)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    err_curr, err_next, err_next2 = (
                        err_next,
                        err_next2,
                        [0.0] * (width + 4),
                    )
                    parts = []
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        idx0 = x + 2
                        v = float(base) + err_curr[idx0]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            qidx = int(v * levels_m1 / 255.0 + 0.5)
                            if qidx < 0:
                                qidx = 0
                            elif qidx > levels_m1:
                                qidx = levels_m1
                            qh = int(qidx * 255.0 / levels_m1 + 0.5)
                        err = (v - float(qh)) / 8.0
                        err_curr[idx0 + 1] += err
                        err_curr[idx0 + 2] += err
                        err_next[idx0 - 1] += err
                        err_next[idx0 + 0] += err
                        err_next[idx0 + 1] += err
                        err_next2[idx0 + 0] += err

                        ch = lut[qh]
                        if mono:
                            cr = cg = cb = qh
                        else:
                            cr, cg, cb = r, g, b
                        parts.append(
                            f'<span style="color:rgb({cr},{cg},{cb})">{html.escape(ch)}</span>'
                        )
                    html_lines.append("".join(parts))
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
        elif output_format == "ansi":
            assert ansi_lines is not None
            if dither == "none":
                if is_avg:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        parts: list[str] = []
                        off = 0
                        if mono:
                            for _ in range(width):
                                r = row[off]
                                g = row[off + 1]
                                b = row[off + 2]
                                off += 3
                                h = (r + g + b) // 3
                                ch = lut[h]
                                parts.append(f"\x1b[38;2;{h};{h};{h}m{ch}")
                        else:
                            for _ in range(width):
                                r = row[off]
                                g = row[off + 1]
                                b = row[off + 2]
                                off += 3
                                h = (r + g + b) // 3
                                ch = lut[h]
                                parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
                        ansi_lines.append("".join(parts))
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
                else:
                    for y in range(height):
                        row = rgb_bytes[y * stride : (y + 1) * stride]
                        parts: list[str] = []
                        off = 0
                        if mono:
                            for _ in range(width):
                                r = row[off]
                                g = row[off + 1]
                                b = row[off + 2]
                                off += 3
                                h = (wr * r + wg * g + wb * b) >> 8
                                ch = lut[h]
                                parts.append(f"\x1b[38;2;{h};{h};{h}m{ch}")
                        else:
                            for _ in range(width):
                                r = row[off]
                                g = row[off + 1]
                                b = row[off + 2]
                                off += 3
                                h = (wr * r + wg * g + wb * b) >> 8
                                ch = lut[h]
                                parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
                        ansi_lines.append("".join(parts))
                        if progress:
                            progress.update(1)
                        if progress_callback:
                            progress_callback(y + 1, height)
            elif dither == "floyd-steinberg":
                err_curr = [0.0] * (width + 2)
                err_next = [0.0] * (width + 2)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    err_curr, err_next = err_next, [0.0] * (width + 2)
                    parts = []
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        v = float(base) + err_curr[x + 1]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            idx = int(v * levels_m1 / 255.0 + 0.5)
                            if idx < 0:
                                idx = 0
                            elif idx > levels_m1:
                                idx = levels_m1
                            qh = int(idx * 255.0 / levels_m1 + 0.5)
                        err = v - float(qh)
                        err_curr[x + 2] += err * (7.0 / 16.0)
                        err_next[x + 0] += err * (3.0 / 16.0)
                        err_next[x + 1] += err * (5.0 / 16.0)
                        err_next[x + 2] += err * (1.0 / 16.0)

                        ch = lut[qh]
                        if mono:
                            parts.append(f"\x1b[38;2;{qh};{qh};{qh}m{ch}")
                        else:
                            parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
                    ansi_lines.append("".join(parts))
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
            else:  # atkinson
                err_curr = [0.0] * (width + 4)
                err_next = [0.0] * (width + 4)
                err_next2 = [0.0] * (width + 4)
                for y in range(height):
                    row = rgb_bytes[y * stride : (y + 1) * stride]
                    err_curr, err_next, err_next2 = (
                        err_next,
                        err_next2,
                        [0.0] * (width + 4),
                    )
                    parts = []
                    off = 0
                    for x in range(width):
                        r = row[off]
                        g = row[off + 1]
                        b = row[off + 2]
                        off += 3
                        base = (
                            (r + g + b) // 3
                            if is_avg
                            else (wr * r + wg * g + wb * b) >> 8
                        )
                        idx0 = x + 2
                        v = float(base) + err_curr[idx0]
                        if v < 0.0:
                            v = 0.0
                        elif v > 255.0:
                            v = 255.0
                        if levels_m1 <= 0:
                            qh = 0
                        else:
                            qidx = int(v * levels_m1 / 255.0 + 0.5)
                            if qidx < 0:
                                qidx = 0
                            elif qidx > levels_m1:
                                qidx = levels_m1
                            qh = int(qidx * 255.0 / levels_m1 + 0.5)
                        err = (v - float(qh)) / 8.0
                        err_curr[idx0 + 1] += err
                        err_curr[idx0 + 2] += err
                        err_next[idx0 - 1] += err
                        err_next[idx0 + 0] += err
                        err_next[idx0 + 1] += err
                        err_next2[idx0 + 0] += err

                        ch = lut[qh]
                        if mono:
                            parts.append(f"\x1b[38;2;{qh};{qh};{qh}m{ch}")
                        else:
                            parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
                    ansi_lines.append("".join(parts))
                    if progress:
                        progress.update(1)
                    if progress_callback:
                        progress_callback(y + 1, height)
        if progress:
            progress.close()

        if output_format != "ansi":
            os.makedirs(output_dir, exist_ok=True)
            file_stem = f"O_h_{bg_brightness}_f_{scale_factor}_{base_name}"
            if n_frames > 1:
                file_stem += f"_{frame_index}"

            if output_format == "image":
                assert output_image is not None
                if assemble_gif:
                    gif_frames.append(output_image)
                    gif_durations.append(frame_duration_ms)
                else:
                    output_image.save(os.path.join(output_dir, file_stem + ".png"))
            elif output_format == "text":
                assert text_lines is not None
                lines = text_lines
                with open(
                    os.path.join(output_dir, file_stem + ".txt"), "w", encoding="utf-8"
                ) as fh:
                    fh.write("\n".join(lines))
            elif output_format == "html":
                assert html_lines is not None
                html_content = "<br>\n".join(html_lines)
                page = (
                    f"<html><body style='background-color:rgb({bg_brightness},{bg_brightness},{bg_brightness});'>"
                    f"<pre style='font-family:monospace;'>{html_content}</pre></body></html>"
                )
                with open(
                    os.path.join(output_dir, file_stem + ".html"), "w", encoding="utf-8"
                ) as fh:
                    fh.write(page)
        else:
            assert ansi_lines is not None
            sys.stdout.write("\n")
            for line in ansi_lines:
                sys.stdout.write(line + "\x1b[0m\n")

    if assemble_gif and gif_frames:
        os.makedirs(output_dir, exist_ok=True)
        gif_stem = f"O_h_{bg_brightness}_f_{scale_factor}_{base_name}"
        gif_path = os.path.join(output_dir, gif_stem + ".gif")
        if gif_fps is not None:
            frame_ms = max(1, int(1000.0 / float(gif_fps)))
            duration = [frame_ms] * len(gif_frames)
        else:
            duration = gif_durations if gif_durations else 40
        try:
            gif_frames[0].save(
                gif_path,
                save_all=True,
                append_images=gif_frames[1:],
                duration=duration,
                loop=gif_loop,
            )
        except OSError as exc:
            print(f"Could not write GIF '{gif_path}': {exc}")


def convert_video(
    video_path=None,
    scale_factor=0.2,
    bg_brightness=30,
    output_dir="./assets/output",
    output_format="image",
    assemble=False,
    video_out: str | None = None,
    mono=False,
    font_path=None,
    grayscale_mode: str = "avg",
    dither: str = "none",
    cell_width: int = ONE_CHAR_WIDTH,
    cell_height: int = ONE_CHAR_HEIGHT,
):
    """Convert a video or webcam stream to ASCII using ``convert_image`` for each frame.

    Args:
        video_path: Path to a video file. If ``None`` the default webcam is used.
        scale_factor: Scaling factor for each frame.
        bg_brightness: Background brightness for the output.
        output_dir: Directory to store generated frames.
        output_format: Output format passed to ``convert_image``.
        assemble: Legacy flag. Prefer ``video_out``.
        video_out: One of: ``frames`` (default), ``gif``, ``mp4``.
        mono: Render frames in grayscale instead of colour.
        font_path: Optional path to a TTF font used for rendering.
    """

    import cv2
    import shutil
    import subprocess

    out_mode = video_out or ("gif" if assemble else "frames")
    if out_mode not in ("frames", "gif", "mp4"):
        raise ValueError("video_out must be one of: frames, gif, mp4")

    cap = cv2.VideoCapture(0 if video_path is None else video_path)
    if not cap.isOpened():
        print("Could not open video source")
        return

    base = "webcam" if video_path is None else Path(video_path).stem
    frames_for_gif = []
    frame_index = 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = None
    progress = loader(total=total_frames, desc="Frames")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        frame_name = f"{base}_{frame_index:05d}"
        convert_image(
            pil_img,
            scale_factor=scale_factor,
            bg_brightness=bg_brightness,
            output_dir=output_dir,
            output_format=output_format,
            base_name=frame_name,
            mono=mono,
            font_path=font_path,
            grayscale_mode=grayscale_mode,
            dither=dither,
            cell_width=cell_width,
            cell_height=cell_height,
        )
        if out_mode == "gif" and output_format == "image":
            import imageio

            out_path = os.path.join(
                output_dir,
                f"O_h_{bg_brightness}_f_{scale_factor}_{frame_name}.png",
            )
            frames_for_gif.append(imageio.imread(out_path))
        frame_index += 1
        progress.update(1)

    cap.release()
    progress.close()

    if out_mode == "gif" and frames_for_gif:
        import imageio

        gif_path = os.path.join(output_dir, f"{base}.gif")
        imageio.mimsave(gif_path, frames_for_gif, fps=24)

    if out_mode == "mp4" and output_format == "image":
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            print("ffmpeg not found; install it or use --video-out frames/gif")
            return

        pattern = os.path.join(
            output_dir, f"O_h_{bg_brightness}_f_{scale_factor}_{base}_%05d.png"
        )
        out_path = os.path.join(output_dir, f"{base}.mp4")
        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            "24",
            "-i",
            pattern,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            out_path,
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"ffmpeg failed with exit code {exc.returncode}")


def print_divider():
    print("\n_________________________________________________")


def loader(total=None, **kwargs):
    """Return a progress bar object.

    Uses :mod:`tqdm` when available, otherwise falls back to printing the
    percentage to stdout similar to the previous ``loader`` implementation.
    """

    if tqdm is None:
        return _DummyLoader(total)

    return tqdm(total=total, **kwargs)
