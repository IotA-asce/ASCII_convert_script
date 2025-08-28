import argparse
import configparser
import html
import os
import sys
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

from computeUnicode import generate_char_array

try:
    from tqdm import tqdm
except ModuleNotFoundError:  # pragma: no cover - fallback when tqdm is missing
    tqdm = None

# Default character array – can be replaced by a dynamically generated one
char_array = [
    ' ', '`', '¨', '·', '¸', '.', '-', "'", ',', '¹', ':', '_', '¯', '~',
    '¬', '¦', ';', '¡', '!', '÷', '*', '*', 'ı', '|', '+', '<', '>', '/',
    '=', '»', '«', 'ì', 'í', 'ï', 'i', '^', 'º', '_r', 'L', 'ª', '®', 'ī',
    'ĩ', 'î', 'ĭ', 'l', '¿', 'J', '×', 'v', '?', 'c', 'į', ')', 'Ĺ', 'Ŀ',
    '(', 'Y', 'T', 'Ļ', 'Ľ', 'ĺ', '7', '¤', 't', 'ľ', 'ŀ', 'Ł', '}', '{',
    'F', 'ċ', 'ļ', 's', 'ĸ', 'Ý', '[', 'x', 'ć', 'z', 'ç', '1', 'I', ']',
    'ł', 'j', 'Ĵ', 'C', 'y', 'V', '£', '5', '2', 'f', '3', 'ĉ', 'č', 'n',
    'Ì', 'Í', 'İ', '¢', 'ĵ', 'U', 'X', 'Ć', 'Z', 'Ċ', 'S', 'u', 'Ï', 'Þ',
    'P', 'Į', 'Ç', 'K', 'A', 'o', 'ÿ', 'ý', 'a', 'e', '4', 'Ĭ', 'E', 'Î',
    'Č', 'Ĉ', 'Ī', 'Ĩ', 'Ú', 'Ù', 'ń', 'ņ', 'ŉ', 'k', 'Ü', 'Á', 'À', 'ù',
    'ú', 'ü', '¥', 'ė', 'w', 'H', 'È', 'É', 'Ä', 'Å', 'ö', 'Ė', 'ò', 'G',
    'ó', 'Ķ', 'ä', 'Û', 'á', 'à', 'Ą', 'ë', 'é', 'è', '_h', 'ą', 'ę', 'Ë',
    'å', 'ñ', 'ň', 'Ę', 'O', 'Ă', '$', 'Â', 'û', 'Ĕ', 'Ā', 'Ě', 'Ê', 'Ã',
    'Æ', 'R', 'ā', 'D', 'ē', 'ķ', 'õ', '½', 'Ē', 'p', 'ã', 'ô', 'ă', 'Ġ',
    'â', 'ĕ', '9', '6', 'ê', 'ě', 'q', '¼', 'Ĳ', 'm', 'N', '%', '0', 'Ģ',
    'ħ', '_b', 'Ò', 'Ó', '#', 'ø', '_d', 'Ö', 'Ĥ', 'Ğ', '§', 'Ĝ', 'W', 'M',
    'B', 'æ', 'Ð', 'Đ', 'Q', 'Ô', '©', 'Ń', 'Ħ', '8', 'ĥ', 'Õ', '_g', 'Ď',
    'Ņ', 'ĳ', 'đ', 'ß', 'þ', 'Ň', 'ð', '@', 'Ŋ', 'Ñ', '¾', 'ġ', 'Ø', 'ģ',
    'ď', 'ğ', '&', 'ĝ'
]


def _recompute_interval():
    global CHAR_LENGTH, INTERVAL
    CHAR_LENGTH = len(char_array)
    INTERVAL = CHAR_LENGTH / 256


_recompute_interval()

ONE_CHAR_WIDTH = 10
ONE_CHAR_HEIGHT = 18

OUTPUT_IMAGE_PREFIX = "FrameOut"  # output image file name prefix
INPUT_FILE_PREFIX = "Frame"  # input file name prefix

LOADER_STATE = False


def load_char_array(dynamic=False, font_path=None):
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


def get_char(input_int):
    """
    Returns a character from the `char_array` list based on the given `input_int` 
    which represents the brightness value of the pixel at hand

    Args:
        input_int (int): The brightness value (grayscale) of a pixel that is being worked on

    Returns:
        A character (string) from the `char_array` list
    """
    return char_array[math.floor(input_int * INTERVAL)]




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
    input_name,
    scale_factor=0.2,
    bg_brightness=30,
    output_dir="./assets/output",
    output_format="image",
    base_name=None,
    mono=False,
    font_path=None,
    progress_callback=None,
):
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

    if isinstance(input_name, Image.Image):
        _im = input_name
        if base_name is None:
            base_name = "frame"
    else:
        input_name = os.fspath(input_name)
        input_path = (
            input_name
            if os.path.isabs(input_name) or os.path.exists(input_name)
            else os.path.join("./assets/input", input_name)
        )
        try:
            _im = Image.open(input_path)
        except FileNotFoundError:
            print(f"Input file '{input_name}' not found")
            return
        if base_name is None:
            base_name = Path(input_name).stem

    # Try to load a monospaced font from common locations. Fallback to the
    # default Pillow font if none of the paths exist. ``font_path`` may point
    # to a custom TTF font to use if it can be loaded.
    def _load_font(user_font):
        windows_font = r"C:\\Windows\\Fonts\\lucon.ttf"
        linux_font = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        if user_font:
            try:
                return ImageFont.truetype(user_font, ONE_CHAR_HEIGHT)
            except OSError:
                print(f"Could not load font '{user_font}', falling back to defaults")
        if os.path.exists(windows_font):
            return ImageFont.truetype(windows_font, ONE_CHAR_HEIGHT)
        if os.path.exists(linux_font):
            return ImageFont.truetype(linux_font, ONE_CHAR_HEIGHT)
        return ImageFont.load_default()

    fnt = _load_font(font_path)

    ascii_grid = []
    frames = [_im]
    if getattr(_im, "is_animated", False):
        frames = [frame.copy() for frame in ImageSequence.Iterator(_im)]

    for frame_index, frame in enumerate(frames):
        width, height = frame.size
        frame = frame.resize(
            (
                max(1, int(scale_factor * width)),
                max(1, int(scale_factor * height * (ONE_CHAR_WIDTH / ONE_CHAR_HEIGHT))),
            ),
            Image.NEAREST,
        )
        width, height = frame.size
        pix = frame.load()

        if output_format == "image":
            output_image = Image.new(
                "RGB",
                (ONE_CHAR_WIDTH * width, ONE_CHAR_HEIGHT * height),
                color=(bg_brightness, bg_brightness, bg_brightness),
            )
            draw = ImageDraw.Draw(output_image)

        ascii_lines = []
        progress = None if progress_callback else loader(
            total=height * width,
            desc=f"Frame {frame_index + 1}/{len(frames)}" if len(frames) > 1 else "Pixels",
        )
        if progress_callback:
            progress_callback(0, height)
        for i in range(height):
            line = []
            for j in range(width):
                if progress:
                    progress.update(1)
                _r, _g, _b = pix[j, i]
                _h = int(_r / 3 + _g / 3 + _b / 3)
                pix[j, i] = (_h, _h, _h)
                ch = get_char(_h)
                if output_format == "image":
                    color = (_h, _h, _h) if mono else (_r, _g, _b)
                    draw.text(
                        (j * ONE_CHAR_WIDTH, i * ONE_CHAR_HEIGHT),
                        ch,
                        font=fnt,
                        fill=color,
                    )
                elif output_format == "text":
                    line.append(ch)
                elif output_format == "html":
                    color = (_h, _h, _h) if mono else (_r, _g, _b)
                    line.append((ch, color))
                elif output_format == "ansi":
                    if mono:
                        line.append(f"\x1b[38;2;{_h};{_h};{_h}m{ch}")
                    else:
                        line.append(f"\x1b[38;2;{_r};{_g};{_b}m{ch}")
            if output_format in ("text", "html", "ansi"):
                ascii_lines.append(line)
            if progress_callback:
                progress_callback(i + 1, height)
        if progress:
            progress.close()

        if output_format != "ansi":
            os.makedirs(output_dir, exist_ok=True)
            file_stem = f"O_h_{bg_brightness}_f_{scale_factor}_{base_name}"
            if len(frames) > 1:
                file_stem += f"_{frame_index}"

            if output_format == "image":
                output_image.save(os.path.join(output_dir, file_stem + ".png"))
            elif output_format == "text":
                lines = ["".join(l) for l in ascii_lines]
                with open(
                    os.path.join(output_dir, file_stem + ".txt"), "w", encoding="utf-8"
                ) as fh:
                    fh.write("\n".join(lines))
            elif output_format == "html":
                html_lines = []
                for line in ascii_lines:
                    html_line = ''.join(
                        f'<span style="color:rgb({r},{g},{b})">{html.escape(ch)}</span>'
                        for ch, (r, g, b) in line
                    )
                    html_lines.append(html_line)
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
            sys.stdout.write("\n")
            for line in ascii_lines:
                sys.stdout.write("".join(line) + "\x1b[0m\n")


def convert_video(
    video_path=None,
    scale_factor=0.2,
    bg_brightness=30,
    output_dir="./assets/output",
    output_format="image",
    assemble=False,
    mono=False,
    font_path=None,
):
    """Convert a video or webcam stream to ASCII using ``convert_image`` for each frame.

    Args:
        video_path: Path to a video file. If ``None`` the default webcam is used.
        scale_factor: Scaling factor for each frame.
        bg_brightness: Background brightness for the output.
        output_dir: Directory to store generated frames.
        output_format: Output format passed to ``convert_image``.
        assemble: If ``True`` and ``output_format`` is ``image``, frames are
            assembled into an animated GIF using ``imageio``.
        mono: Render frames in grayscale instead of colour.
        font_path: Optional path to a TTF font used for rendering.
    """

    import cv2
    import imageio

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
        )
        if assemble and output_format == "image":
            out_path = os.path.join(
                output_dir,
                f"O_h_{bg_brightness}_f_{scale_factor}_{frame_name}.png",
            )
            frames_for_gif.append(imageio.imread(out_path))
        frame_index += 1
        progress.update(1)

    cap.release()
    progress.close()

    if assemble and frames_for_gif:
        gif_path = os.path.join(output_dir, f"{base}.gif")
        imageio.mimsave(gif_path, frames_for_gif, fps=24)

def print_divider():
    print("\n_________________________________________________")


def loader(total=None, **kwargs):
    """Return a progress bar object.

    Uses :mod:`tqdm` when available, otherwise falls back to printing the
    percentage to stdout similar to the previous ``loader`` implementation.
    """

    if tqdm is None:
        class _DummyLoader:
            def __init__(self, total):
                self.total = total or 0
                self.count = 0

            def update(self, n=1):
                if not self.total:
                    return
                self.count += n
                percent = (self.count / self.total) * 100
                sys.stdout.write(f"\rprocessing - {percent}\t%")

            def close(self):
                if self.total:
                    sys.stdout.write("\n")

        return _DummyLoader(total)

    return tqdm(total=total, **kwargs)


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Convert images to ASCII art")
    parser.add_argument("--input", help="Name of the input image file")
    parser.add_argument("--batch", help="Convert all images in the given directory")
    parser.add_argument(
        "--scale",
        type=float,
        help="Scaling factor for the output image",
    )
    parser.add_argument(
        "--brightness",
        type=int,
        help="Background brightness of the output image",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to store the generated image",
    )
    parser.add_argument(
        "--format",
        choices=["image", "text", "html", "ansi"],
        help="Output format",
    )
    parser.add_argument(
        "--dynamic-set",
        action="store_true",
        help="Generate character set dynamically using computeUnicode",
    )
    parser.add_argument(
        "--font",
        help="Path to a TTF font to use for rendering",
    )
    parser.add_argument("--video", help="Path to a video file to convert")
    parser.add_argument(
        "--webcam",
        action="store_true",
        help="Use webcam for live capture",
    )
    parser.add_argument(
        "--mono",
        action="store_true",
        help="Render ASCII art in grayscale instead of colour",
    )
    return parser.parse_args(args)


def main():
    config = configparser.ConfigParser()
    config.read(Path(__file__).with_name("config.ini"))

    scale_cfg = config.getfloat("scale", "value", fallback=0.2)
    brightness_cfg = config.getint("brightness", "value", fallback=30)
    output_dir_cfg = config.get("output_dir", "path", fallback="./assets/output")
    format_cfg = config.get("format", "type", fallback="image")

    args = parse_args()
    load_char_array(dynamic=args.dynamic_set, font_path=args.font)

    def _validate_scale(val: float) -> float:
        if not 0 < val <= 1:
            raise ValueError("Scale factor must be between 0 and 1")
        return val

    def _validate_brightness(val: int) -> int:
        if not 0 <= val <= 255:
            raise ValueError("Brightness must be between 0 and 255")
        return val

    factor = args.scale if args.scale is not None else scale_cfg
    factor = _validate_scale(factor)

    bg_brightness = (
        args.brightness if args.brightness is not None else brightness_cfg
    )
    bg_brightness = _validate_brightness(bg_brightness)

    output_dir = args.output_dir if args.output_dir is not None else output_dir_cfg
    output_format = args.format if args.format is not None else format_cfg

    if args.video and args.webcam:
        print("Choose either --video or --webcam, not both")
        return

    if args.video or args.webcam:
        source = None if args.webcam else args.video
        convert_video(
            source,
            scale_factor=factor,
            bg_brightness=bg_brightness,
            output_dir=output_dir,
            output_format=output_format,
            mono=args.mono,
            font_path=args.font,
        )
    elif args.batch:
        names = [
            os.path.join(args.batch, n)
            for n in os.listdir(args.batch)
            if os.path.isfile(os.path.join(args.batch, n))
        ]
        progress = loader(total=len(names), desc="Images")
        for full_path in names:
            convert_image(
                full_path,
                factor,
                bg_brightness,
                output_dir,
                output_format,
                mono=args.mono,
                font_path=args.font,
            )
            progress.update(1)
        progress.close()
    else:
        image_name = args.input
        if image_name is None:
            image_name = list_files_from_assets()
        elif not os.path.isfile(os.path.join("./assets/input", image_name)):
            print(f"Input file '{image_name}' not found")
            return
        convert_image(
            image_name,
            factor,
            bg_brightness,
            output_dir,
            output_format,
            mono=args.mono,
            font_path=args.font,
        )


if __name__ == "__main__":
    main()
