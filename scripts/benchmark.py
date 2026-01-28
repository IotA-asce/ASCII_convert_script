import argparse
import statistics
import time
import tempfile
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark ASCII conversion")
    p.add_argument("--input", required=True, help="Path to an input image")
    p.add_argument(
        "--format",
        choices=["image", "text", "html"],
        default="image",
        help="Output format to benchmark",
    )
    p.add_argument("--runs", type=int, default=3, help="Number of runs")
    p.add_argument("--scale", type=float, default=0.2)
    p.add_argument("--brightness", type=int, default=30)
    p.add_argument("--mono", action="store_true")
    p.add_argument(
        "--grayscale",
        choices=["avg", "luma601", "luma709"],
        default="avg",
    )
    p.add_argument(
        "--dither",
        choices=["none", "floyd-steinberg", "atkinson"],
        default="none",
    )
    p.add_argument("--cell-width", type=int, default=10)
    p.add_argument("--cell-height", type=int, default=18)
    p.add_argument("--dynamic-set", action="store_true")
    p.add_argument("--font", help="Optional .ttf font path")
    return p.parse_args()


def _compute_dims(
    *,
    in_w: int,
    in_h: int,
    scale: float,
    cell_width: int,
    cell_height: int,
) -> tuple[int, int, int, int]:
    out_w = max(1, int(scale * in_w))
    out_h = max(1, int(scale * in_h * (cell_width / cell_height)))
    out_px_w = out_w * cell_width
    out_px_h = out_h * cell_height
    return out_w, out_h, out_px_w, out_px_h


def main() -> int:
    args = _parse_args()

    from PIL import Image

    from ascii_art import converter

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Missing input file: {input_path}")

    with Image.open(input_path) as im:
        in_w, in_h = im.size

    out_w, out_h, out_px_w, out_px_h = _compute_dims(
        in_w=in_w,
        in_h=in_h,
        scale=float(args.scale),
        cell_width=int(args.cell_width),
        cell_height=int(args.cell_height),
    )

    print(f"Input:  {input_path} ({in_w}x{in_h}px)")
    print(f"Output: ~{out_w}x{out_h} chars")
    if args.format == "image":
        print(f"Image:  ~{out_px_w}x{out_px_h}px")
    print(
        "Params:",
        f"format={args.format}",
        f"scale={args.scale}",
        f"brightness={args.brightness}",
        f"mono={bool(args.mono)}",
        f"grayscale={args.grayscale}",
        f"dither={args.dither}",
        f"cell={args.cell_width}x{args.cell_height}",
    )

    converter.load_char_array(dynamic=bool(args.dynamic_set), font_path=args.font)

    times: list[float] = []
    with tempfile.TemporaryDirectory() as td:
        for i in range(int(args.runs)):
            t0 = time.perf_counter()
            converter.convert_image(
                str(input_path),
                scale_factor=float(args.scale),
                bg_brightness=int(args.brightness),
                output_dir=td,
                output_format=str(args.format),
                base_name=f"bench_{i}",
                mono=bool(args.mono),
                font_path=args.font,
                grayscale_mode=str(args.grayscale),
                dither=str(args.dither),
                cell_width=int(args.cell_width),
                cell_height=int(args.cell_height),
            )
            t1 = time.perf_counter()
            times.append(t1 - t0)

    if not times:
        print("No runs")
        return 1

    mean_s = statistics.mean(times)
    min_s = min(times)
    max_s = max(times)
    print(
        f"Timing: mean={mean_s:.4f}s min={min_s:.4f}s max={max_s:.4f}s (runs={len(times)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
