import argparse
import os
import sys
import math
from html import escape

from PIL import Image, ImageDraw, ImageFont

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


CHAR_LENGTH = len(char_array)   # The number of characters in the char_array
INTERVAL = CHAR_LENGTH / 256    

ONE_CHAR_WIDTH = 10
ONE_CHAR_HEIGHT = 18

OUTPUT_IMAGE_PREFIX = "FrameOut"  # output image file name prefix
INPUT_FILE_PREFIX = "Frame"  # input file name prefix

LOADER_STATE = False

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


def convert_image(input_name, scale_factor=0.2, bg_brightness=30, output_format="image"):
    """
    Converts an image file to an ASCII art representation. Depending on
    ``output_format`` the result can be an image, plain text or a HTML file.

    Args:
        input_name (str):
            The name of the image file to be converted, including the file
            extension.
        scale_factor (float):
            The scaling factor for the output image. Default is 0.2, which
            means the output image will be 20% of the size of the input image
            times the width and height of one character.
        bg_brightness (int):
            The brightness level of the output image background. Default is
            30, which is close to medium gray. Only used when
            ``output_format`` is ``"image"``.
        output_format (str):
            Output format: ``"image"`` (default), ``"text"`` or ``"html"``.

    Returns:
        None. The output file is written to ``./assets/output/``.
    """

    _im = Image.open("./assets/input/" + input_name)

    # Try to load a monospaced font from common locations. Fallback to the
    # default Pillow font if none of the paths exist.
    def _load_font():
        windows_font = r"C:\\Windows\\Fonts\\lucon.ttf"
        linux_font = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        if os.path.exists(windows_font):
            return ImageFont.truetype(windows_font, ONE_CHAR_HEIGHT)
        if os.path.exists(linux_font):
            return ImageFont.truetype(linux_font, ONE_CHAR_HEIGHT)
        return ImageFont.load_default()

    fnt = _load_font()

    width, height = _im.size
    _im = _im.resize(
        (
            int(scale_factor * width), 
            int(scale_factor * height * (ONE_CHAR_WIDTH / ONE_CHAR_HEIGHT))
        ),
        Image.NEAREST
    )
    width, height = _im.size
    pix = _im.load()

    os.makedirs("./assets/output", exist_ok=True)

    output_name = f"./assets/output/O_h_{str(bg_brightness)}_f_{str(scale_factor)}_{input_name}"

    if output_format == "image":
        output_image = Image.new(
            'RGB',
            (ONE_CHAR_WIDTH * width, ONE_CHAR_HEIGHT * height),
            color=(bg_brightness, bg_brightness, bg_brightness)
        )  # (0,0,0) for polychromatic images

        _d = ImageDraw.Draw(output_image)

        LOADER_STATE = True
        for i in range(height):
            for j in range(width):
                loader(((i * width) + j), (height * width))
                _r, _g, _b = pix[j, i]
                _h = int(_r / 3 + _g / 3 + _b / 3)
                pix[j, i] = (_h, _h, _h)
                _d.text((j * ONE_CHAR_WIDTH, i * ONE_CHAR_HEIGHT),
                       get_char(_h), font=fnt, fill=(_r, _g, _b))

        output_image.save(output_name)
    else:
        ascii_rows = []
        LOADER_STATE = True
        for i in range(height):
            row = []
            for j in range(width):
                loader(((i * width) + j), (height * width))
                _r, _g, _b = pix[j, i]
                _h = int(_r / 3 + _g / 3 + _b / 3)
                row.append((get_char(_h), _r, _g, _b))
            ascii_rows.append(row)

        if output_format == "text":
            with open(output_name + ".txt", "w", encoding="utf-8") as f:
                for row in ascii_rows:
                    f.write("".join(ch for ch, _, _, _ in row) + "\n")
        elif output_format == "html":
            html_lines = []
            for row in ascii_rows:
                html_line = "".join(
                    f'<span style="color:rgb({r},{g},{b})">{escape(ch)}</span>'
                    for ch, r, g, b in row
                )
                html_lines.append(html_line)
            html_content = (
                "<!DOCTYPE html><html><body><pre style=\"font-family:monospace;\">"
                + "\n".join(html_lines)
                + "</pre></body></html>"
            )
            with open(output_name + ".html", "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            raise ValueError("Invalid output format: " + output_format)

def print_divider():
    print("\n_________________________________________________")

def loader(count, total):
    sys.stdout.write(f"\rprocessing - {str((count / total) * 100)}\t%")

def __main():
    parser = argparse.ArgumentParser(description="Convert images to ASCII art")
    parser.add_argument(
        "--format",
        choices=["image", "text", "html"],
        default="image",
        help="Output format",
    )
    args = parser.parse_args()

    image_name = list_files_from_assets()

    print(image_name)
    print_divider()
    print("Factor : higher factor will lead to larger image size and greater render time")
    factor = float(input("Factor input [0-1] - "))
    print_divider()
    print("BG color will be black if not modified")
    choice = input("If it is required to change the output [y/N] - ")
    print()
    if choice.capitalize() == "Y":
        bg_brightness = int(input("Enter brightness factor [range-range] - "))
        convert_image(image_name, factor, bg_brightness, args.format)
    else:
        convert_image(image_name, factor, output_format=args.format)

__main()
