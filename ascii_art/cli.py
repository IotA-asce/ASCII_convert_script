import argparse
import configparser
from pathlib import Path
from typing import Sequence

from .converter import (
    convert_image,
    convert_video,
    list_files_from_assets,
    load_char_array,
    loader,
)


def _validate_scale(val: float) -> float:
    if not 0 < val <= 1:
        raise ValueError("Scale factor must be between 0 and 1")
    return val


def _validate_brightness(val: int) -> int:
    if not 0 <= val <= 255:
        raise ValueError("Brightness must be between 0 and 255")
    return val


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
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
        help="Generate character set dynamically using charset.generate_char_array",
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
    config.read(Path(__file__).resolve().parent.parent / "config.ini")

    scale_cfg = config.getfloat("scale", "value", fallback=0.2)
    brightness_cfg = config.getint("brightness", "value", fallback=30)
    output_dir_cfg = config.get("output_dir", "path", fallback="./assets/output")
    format_cfg = config.get("format", "type", fallback="image")

    args = parse_args()
    load_char_array(dynamic=args.dynamic_set, font_path=args.font)

    factor = args.scale if args.scale is not None else scale_cfg
    factor = _validate_scale(factor)

    bg_brightness = args.brightness if args.brightness is not None else brightness_cfg
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
        batch_dir = Path(args.batch)
        names = [str(p) for p in batch_dir.iterdir() if p.is_file()]
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
