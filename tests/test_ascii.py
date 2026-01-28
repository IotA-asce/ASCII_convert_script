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
    assert args.grayscale is None
    assert args.dither is None
    assert args.cell_width is None
    assert args.cell_height is None
    assert args.assemble is False
    assert args.gif_fps is None
    assert args.gif_loop is None


def test_parse_args_grayscale_flag():
    args = ascii_mod.parse_args(["--grayscale", "luma601"])
    assert args.grayscale == "luma601"


def test_parse_args_dither_flag():
    args = ascii_mod.parse_args(["--dither", "floyd-steinberg"])
    assert args.dither == "floyd-steinberg"


def test_parse_args_cell_size_flags():
    args = ascii_mod.parse_args(["--cell-width", "8", "--cell-height", "16"])
    assert args.cell_width == 8
    assert args.cell_height == 16


def test_parse_args_assemble_flag():
    args = ascii_mod.parse_args(["--assemble"])
    assert args.assemble is True


def test_parse_args_gif_flags():
    args = ascii_mod.parse_args(["--gif-fps", "12", "--gif-loop", "2"])
    assert args.gif_fps == 12.0
    assert args.gif_loop == 2


def test_convert_image_dither_floyd_steinberg_tiny_gradient(tmp_path):
    import ascii_art.converter as conv

    original = list(conv.char_array)
    try:
        conv.char_array = [" ", "#"]
        conv._recompute_interval()

        # Use a 2x4 input so the converter's aspect correction produces a 2x2 output.
        img = Image.new("RGB", (2, 4), color=(128, 128, 128))
        test_path = tmp_path / "midgray.png"
        img.save(test_path)
        out_dir = tmp_path / "out"

        ascii_mod.convert_image(
            test_path,
            scale_factor=1.0,
            bg_brightness=0,
            output_dir=out_dir,
            output_format="text",
            dither="floyd-steinberg",
        )

        out_file = out_dir / f"O_h_0_f_1.0_{test_path.stem}.txt"
        content = out_file.read_text(encoding="utf-8")
        assert content == "# \n #"
    finally:
        conv.char_array = original
        conv._recompute_interval()


def test_convert_image_dither_atkinson_tiny_gradient(tmp_path):
    import ascii_art.converter as conv

    original = list(conv.char_array)
    try:
        conv.char_array = [" ", "#"]
        conv._recompute_interval()

        img = Image.new("RGB", (2, 4), color=(128, 128, 128))
        test_path = tmp_path / "midgray_atkinson.png"
        img.save(test_path)
        out_dir = tmp_path / "out"

        ascii_mod.convert_image(
            test_path,
            scale_factor=1.0,
            bg_brightness=0,
            output_dir=out_dir,
            output_format="text",
            dither="atkinson",
        )

        out_file = out_dir / f"O_h_0_f_1.0_{test_path.stem}.txt"
        content = out_file.read_text(encoding="utf-8")
        assert content == "# \n #"
    finally:
        conv.char_array = original
        conv._recompute_interval()


def test_convert_image_cell_size_affects_aspect(tmp_path):
    img = Image.new("RGB", (2, 4), color=(255, 255, 255))
    test_path = tmp_path / "aspect.png"
    img.save(test_path)
    out_dir = tmp_path / "out"

    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=out_dir,
        output_format="text",
        cell_width=1,
        cell_height=1,
    )

    out_file = out_dir / f"O_h_0_f_1.0_{test_path.stem}.txt"
    lines = out_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4
    assert all(len(line) == 2 for line in lines)


def test_convert_image_assemble_animated_gif(tmp_path):
    frame1 = Image.new("RGB", (2, 4), color=(255, 255, 255))
    frame2 = Image.new("RGB", (2, 4), color=(0, 0, 0))
    gif_path = tmp_path / "anim.gif"
    frame1.save(
        gif_path,
        save_all=True,
        append_images=[frame2],
        duration=[40, 40],
        loop=0,
    )

    out_dir = tmp_path / "out"
    ascii_mod.convert_image(
        gif_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=out_dir,
        output_format="image",
        assemble=True,
        gif_fps=20,
        gif_loop=2,
        cell_width=1,
        cell_height=1,
    )

    out_file = out_dir / f"O_h_0_f_1.0_{gif_path.stem}.gif"
    assert out_file.exists()

    with Image.open(out_file) as im:
        assert getattr(im, "is_animated", False)
        assert int(getattr(im, "n_frames", 1)) == 2
        assert int(im.info.get("loop", -1)) == 2


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
    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test.png"
    test_path = input_dir / test_name
    img.save(test_path)
    out_dir = tmp_path / "out"
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=out_dir,
        output_format="text",
    )
    out_file = out_dir / f"O_h_0_f_1.0_{test_path.stem}.txt"
    assert out_file.exists()


def test_convert_image_ansi_stdout(tmp_path, capsys):
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test_ansi.png"
    test_path = input_dir / test_name
    img.save(test_path)
    out_dir = tmp_path / "out"
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=out_dir,
        output_format="ansi",
    )
    assert not out_dir.exists() or list(out_dir.iterdir()) == []
    captured = capsys.readouterr().out
    expected_char = ascii_mod.get_char(255)
    expected_line = f"\x1b[38;2;255;255;255m{expected_char}\x1b[0m"
    assert expected_line in captured


def test_convert_image_mono_ansi_stdout(tmp_path, capsys):
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test_mono_ansi.png"
    test_path = input_dir / test_name
    img.save(test_path)
    out_dir = tmp_path / "out"
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=out_dir,
        output_format="ansi",
        mono=True,
    )
    captured = capsys.readouterr().out
    expected_char = ascii_mod.get_char(85)
    expected_line = f"\x1b[38;2;85;85;85m{expected_char}\x1b[0m"
    assert expected_line in captured


def test_convert_image_mono_ansi_grayscale_luma601(tmp_path, capsys):
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test_mono_ansi_luma601.png"
    test_path = input_dir / test_name
    img.save(test_path)
    out_dir = tmp_path / "out"
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=out_dir,
        output_format="ansi",
        mono=True,
        grayscale_mode="luma601",
    )
    captured = capsys.readouterr().out
    expected_char = ascii_mod.get_char(76)
    expected_line = f"\x1b[38;2;76;76;76m{expected_char}\x1b[0m"
    assert expected_line in captured


def test_convert_image_mono_ansi_grayscale_luma709(tmp_path, capsys):
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    test_name = "test_mono_ansi_luma709.png"
    test_path = input_dir / test_name
    img.save(test_path)
    out_dir = tmp_path / "out"
    ascii_mod.convert_image(
        test_path,
        scale_factor=1.0,
        bg_brightness=0,
        output_dir=out_dir,
        output_format="ansi",
        mono=True,
        grayscale_mode="luma709",
    )
    captured = capsys.readouterr().out
    expected_char = ascii_mod.get_char(53)
    expected_line = f"\x1b[38;2;53;53;53m{expected_char}\x1b[0m"
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
    input_dir = tmp_path / "input"
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
        output_dir=tmp_path / "out",
        output_format="text",
        progress_callback=cb,
    )
    assert calls[0][0] == 0
    assert calls[-1][0] == calls[-1][1]
    assert calls[-1][1] > 0
