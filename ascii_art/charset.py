"""Utilities for generating brightness-ranked character arrays.

This module exposes ``generate_char_array`` which renders each character and
computes how much of the glyph is "inked". The characters are then sorted from
least filled (lightest) to most filled (darkest). The resulting array can be
used to map grayscale values to characters in the ASCII art converter.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

# Base characters used to build the mapping. These are ordered arbitrarily and
# will be sorted by brightness percentage.
BASE_CHARS: list[str] = [
    " ",
    "!",
    "*",
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "[",
    "]",
    "^",
    "_",
    "`",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "{",
    "|",
    "}",
    "~",
    "¡",
    "¢",
    "£",
    "¤",
    "¥",
    "¦",
    "§",
    "¨",
    "©",
    "ª",
    "«",
    "¬",
    "®",
    "¯",
    "·",
    "¸",
    "¹",
    "º",
    "»",
    "¼",
    "½",
    "¾",
    "¿",
    "À",
    "Á",
    "Â",
    "Ã",
    "Ä",
    "Å",
    "Æ",
    "Ç",
    "È",
    "É",
    "Ê",
    "Ë",
    "Ì",
    "Í",
    "Î",
    "Ï",
    "Ð",
    "Ñ",
    "Ò",
    "Ó",
    "Ô",
    "Õ",
    "Ö",
    "×",
    "Ø",
    "Ù",
    "Ú",
    "Û",
    "Ü",
    "Ý",
    "Þ",
    "ß",
    "à",
    "á",
    "â",
    "ã",
    "ä",
    "å",
    "æ",
    "ç",
    "è",
    "é",
    "ê",
    "ë",
    "ì",
    "í",
    "î",
    "ï",
    "ð",
    "ñ",
    "ò",
    "ó",
    "ô",
    "õ",
    "ö",
    "÷",
    "ø",
    "ù",
    "ú",
    "û",
    "ü",
    "ý",
    "þ",
    "ÿ",
    "Ā",
    "ā",
    "Ă",
    "ă",
    "Ą",
    "ą",
    "Ć",
    "ć",
    "Ĉ",
    "ĉ",
    "Ċ",
    "ċ",
    "Č",
    "č",
    "Ď",
    "ď",
    "Đ",
    "đ",
    "Ē",
    "ē",
    "Ĕ",
    "ĕ",
    "Ė",
    "ė",
    "Ę",
    "ę",
    "Ě",
    "ě",
    "Ĝ",
    "ĝ",
    "Ğ",
    "ğ",
    "Ġ",
    "ġ",
    "Ģ",
    "ģ",
    "Ĥ",
    "ĥ",
    "Ħ",
    "ħ",
    "Ĩ",
    "ĩ",
    "Ī",
    "ī",
    "Ĭ",
    "ĭ",
    "Į",
    "į",
    "İ",
    "ı",
    "Ĳ",
    "ĳ",
    "Ĵ",
    "ĵ",
    "Ķ",
    "ķ",
    "ĸ",
    "Ĺ",
    "ĺ",
    "Ļ",
    "ļ",
    "Ľ",
    "ľ",
    "Ŀ",
    "ŀ",
    "Ł",
    "ł",
    "Ń",
    "ń",
    "Ņ",
    "ņ",
    "Ň",
    "ň",
    "ŉ",
    "Ŋ",
]


def _default_font_path() -> str:
    """Return a monospaced font path available on the current system."""
    windows_font = r"C:\\Windows\\Fonts\\lucon.ttf"
    linux_font = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    if os.path.exists(windows_font):
        return windows_font
    if os.path.exists(linux_font):
        return linux_font
    # Pillow's default bitmap font
    return ""


def _ink_percentage(ch: str, font: ImageFont.FreeTypeFont) -> float:
    """Return the ratio of white pixels for ``ch`` rendered with ``font``."""
    canvas = Image.new("L", (200, 250), color=0)
    draw = ImageDraw.Draw(canvas)
    draw.text((25, 5), ch, font=font, fill=255)
    width, height = canvas.size
    pixels = canvas.load()
    white = 0
    for y in range(height):
        for x in range(width):
            if pixels[x, y] > 100:
                white += 1
    return white / float(width * height)


CACHE_FILE = Path(__file__).with_name("char_cache.json")


def _load_cache() -> dict[str, list[str]]:
    if CACHE_FILE.exists():
        with CACHE_FILE.open("r", encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return {}
    return {}


def _write_cache(cache: dict[str, list[str]]) -> None:
    with CACHE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=2)


def generate_char_array(
    font_path: str | None = None, *, refresh_cache: bool = False
) -> list[str]:
    """Return characters sorted by how much of the glyph is filled.

    ``font_path`` may be supplied to point to a TTF font. When ``None`` the
    function attempts to locate a system monospace font. Results are cached in
    ``char_cache.json`` keyed by font path.
    """
    font_path = font_path or _default_font_path()
    cache_key = font_path or "default"
    cache: dict[str, list[str]] = {} if refresh_cache else _load_cache()
    if not refresh_cache and cache_key in cache:
        return cache[cache_key]

    if font_path:
        font = ImageFont.truetype(font_path, 250)
    else:
        font = ImageFont.load_default()
    percentages = [_ink_percentage(ch, font) for ch in BASE_CHARS]
    result = [ch for _, ch in sorted(zip(percentages, BASE_CHARS))]

    cache[cache_key] = result
    _write_cache(cache)
    return result


def parse_args(args: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate brightness-ranked character arrays"
    )
    parser.add_argument("--font-path", help="Optional path to a TTF font")
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Recompute the character array even if cached",
    )
    return parser.parse_args(list(args) if args is not None else None)


if __name__ == "__main__":  # pragma: no cover - manual usage
    _args = parse_args()
    print(generate_char_array(_args.font_path, refresh_cache=_args.refresh_cache))
