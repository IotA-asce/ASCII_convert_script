import os
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ascii_art as ascii_mod


def test_get_char_range():
    assert ascii_mod.get_char(0) == ascii_mod.char_array[0]
    assert ascii_mod.get_char(255) == ascii_mod.char_array[-1]


def test_parse_args_defaults():
    args = ascii_mod.parse_args([])
    assert args.input is None
    assert args.scale is None
    assert args.brightness is None
    assert args.output_dir is None
    assert args.video is None
    assert args.webcam is False
    assert args.mono is False
    assert args.font is None


def test_parse_args_ansi_format():
    args = ascii_mod.parse_args(["--format", "ansi"])
    assert args.format == "ansi"


def test_parse_args_video_flag():
    args = ascii_mod.parse_args(["--video", "movie.mp4"])
    assert args.video == "movie.mp4"
    assert args.webcam is False


def test_parse_args_webcam_flag():
    args = ascii_mod.parse_args(["--webcam"])
    assert args.webcam is True
    assert args.video is None


def test_parse_args_mono_flag():
    args = ascii_mod.parse_args(["--mono"])
    assert args.mono is True


def test_parse_args_font_flag(tmp_path):
    font_path = tmp_path / "fake.ttf"
    font_path.touch()
    args = ascii_mod.parse_args(["--font", str(font_path)])
    assert args.font == str(font_path)


def test_convert_image_text_output(tmp_path):
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    input_dir = Path("assets/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test.png"
    test_path = input_dir / test_name
    img.save(test_path)
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=tmp_path,
        output_format="text",
    )
    out_file = tmp_path / f"O_h_0_f_1.0_{test_path.stem}.txt"
    assert out_file.exists()


def test_convert_image_ansi_stdout(tmp_path, capsys):
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    input_dir = Path("assets/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test_ansi.png"
    test_path = input_dir / test_name
    img.save(test_path)
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=tmp_path,
        output_format="ansi",
    )
    assert list(tmp_path.iterdir()) == []
    captured = capsys.readouterr().out
    expected_char = ascii_mod.get_char(255)
    expected_line = f"\x1b[38;2;255;255;255m{expected_char}\x1b[0m"
    assert expected_line in captured


def test_convert_image_mono_ansi_stdout(tmp_path, capsys):
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    input_dir = Path("assets/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test_mono_ansi.png"
    test_path = input_dir / test_name
    img.save(test_path)
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=tmp_path,
        output_format="ansi",
        mono=True,
    )
    captured = capsys.readouterr().out
    expected_char = ascii_mod.get_char(85)
    expected_line = f"\x1b[38;2;85;85;85m{expected_char}\x1b[0m"
    assert expected_line in captured


def test_convert_image_pil_input(tmp_path):
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    ascii_mod.convert_image(
        img,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=tmp_path,
        output_format="text",
        base_name="pil_img",
    )
    out_file = tmp_path / "O_h_0_f_1.0_pil_img.txt"
    assert out_file.exists()


def test_convert_image_progress_callback(tmp_path):
    img = Image.new("RGB", (2, 2), color=(255, 255, 255))
    input_dir = Path("assets/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test_progress.png"
    test_path = input_dir / test_name
    img.save(test_path)
    calls = []

    def cb(done, total):
        calls.append((done, total))

    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=tmp_path,
        output_format="text",
        progress_callback=cb,
    )
    assert calls[0][0] == 0
    assert calls[-1][0] == calls[-1][1]
    assert calls[-1][1] > 0
