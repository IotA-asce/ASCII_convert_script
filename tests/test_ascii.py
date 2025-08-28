import os
from pathlib import Path

from PIL import Image

import ascii as ascii_mod


def test_get_char_range():
    assert ascii_mod.get_char(0) == ascii_mod.char_array[0]
    assert ascii_mod.get_char(255) == ascii_mod.char_array[-1]


def test_parse_args_defaults():
    args = ascii_mod.parse_args([])
    assert args.input is None
    assert args.scale is None
    assert args.brightness is None
    assert args.output_dir == "./assets/output"


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
