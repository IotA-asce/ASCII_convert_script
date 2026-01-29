"""Streamlit GUI for converting images to ASCII art.

Launch:
  python -m ascii_art.gui

Or:
  streamlit run ascii_art/streamlit_gui.py
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


# Pillow changed resampling constants to an enum; use getattr for compatibility.
_RESAMPLE_NEAREST = getattr(getattr(Image, "Resampling", Image), "NEAREST")
_RESAMPLE_BILINEAR = getattr(getattr(Image, "Resampling", Image), "BILINEAR")
_RESAMPLE_BOX = getattr(getattr(Image, "Resampling", Image), "BOX")

# When Streamlit runs a script by path (e.g. `streamlit run ascii_art/streamlit_gui.py`)
# it adds the script directory (`ascii_art/`) to `sys.path`, not the repo root.
# Ensure the repo root is importable so `import ascii_art` works.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ascii_art import converter


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


DEFAULTS: dict[str, Any] = {
    "scale": 0.2,
    "brightness": 30,
    "grayscale": "avg",
    "dither": "none",
    "cell_width": converter.ONE_CHAR_WIDTH,
    "cell_height": converter.ONE_CHAR_HEIGHT,
    "format": "image",
    "dynamic_set": False,
    "output_dir": "./assets/output",
    "font_path": None,
}


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True)
class InputImage:
    name: str
    image: Image.Image


class _SharedAudioLevel:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rms = 0.0

    def set_rms(self, rms: float) -> None:
        with self._lock:
            self._rms = float(rms)

    def get_rms(self) -> float:
        with self._lock:
            return float(self._rms)


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_config(data: dict[str, Any]) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text).lstrip("\n")


def _open_uploaded_images(files: list[Any]) -> list[InputImage]:
    results: list[InputImage] = []
    for f in files:
        if not f:
            continue
        try:
            img = Image.open(io.BytesIO(f.getvalue())).convert("RGB")
        except Exception:
            continue
        results.append(InputImage(name=getattr(f, "name", "upload"), image=img))
    return results


def _materialize_uploaded_font(font_upload: Any) -> str | None:
    if not font_upload:
        return None
    try:
        suffix = (
            ".ttf"
            if str(getattr(font_upload, "name", "")).lower().endswith(".ttf")
            else ""
        )
        fh = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        fh.write(font_upload.getvalue())
        fh.close()
        return fh.name
    except Exception:
        return None


def _ansi_preview(
    img: Image.Image,
    *,
    scale: float,
    brightness: int,
    grayscale_mode: str,
    dither: str,
    cell_width: int,
    cell_height: int,
    dynamic_set: bool,
    font_path: str | None,
    progress_cb,
) -> str:
    converter.load_char_array(dynamic=dynamic_set, font_path=font_path)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        converter.convert_image(
            img,
            scale_factor=scale,
            bg_brightness=brightness,
            output_format="ansi",
            output_dir="./assets/output",
            mono=True,
            font_path=font_path,
            grayscale_mode=grayscale_mode,
            dither=dither,
            cell_width=int(cell_width),
            cell_height=int(cell_height),
            progress_callback=progress_cb,
            base_name="preview",
        )
    return _strip_ansi(buf.getvalue())


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _scale_from_audio_inverse(
    *,
    base_scale: float,
    audio_level_0_to_1: float,
    sensitivity: float,
    min_scale: float,
    max_scale: float,
) -> float:
    """Compute scale inversely proportional to audio level.

    Louder audio => smaller scale => less detail.
    """

    lvl = _clamp(audio_level_0_to_1 * sensitivity, 0.0, 1.0)
    scale = base_scale / (1.0 + lvl)
    return _clamp(scale, min_scale, max_scale)


def _render_ascii_image(
    img: Image.Image,
    *,
    scale_factor: float,
    detail_scale: float | None = None,
    bg_brightness: int,
    mono: bool,
    font_path: str | None,
    grayscale_mode: str,
    dither: str,
    cell_width: int,
    cell_height: int,
    font: ImageFont.ImageFont | None = None,
    char_map: list[str] | None = None,
) -> Image.Image:
    """Render a single frame to a PIL image (no file IO)."""

    def _load_font(
        user_font: str | None,
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        windows_font = r"C:\\Windows\\Fonts\\lucon.ttf"
        linux_font = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        if user_font:
            try:
                return ImageFont.truetype(user_font, int(cell_height))
            except OSError:
                pass
        if Path(windows_font).exists():
            return ImageFont.truetype(windows_font, int(cell_height))
        if Path(linux_font).exists():
            return ImageFont.truetype(linux_font, int(cell_height))
        return ImageFont.load_default()

    width, height = img.size
    detail_scale = float(scale_factor) if detail_scale is None else float(detail_scale)
    base_w = max(1, int(float(scale_factor) * width))
    base_h = max(
        1,
        int(float(scale_factor) * height * (float(cell_width) / float(cell_height))),
    )
    detail_w = max(1, int(detail_scale * width))
    detail_h = max(
        1,
        int(detail_scale * height * (float(cell_width) / float(cell_height))),
    )
    # Keep output size fixed (base_w/base_h). Modulate detail by downsampling the
    # input to (detail_w/detail_h) and scaling back up to the fixed grid.
    frame = img.convert("RGB")
    if (detail_w, detail_h) != (base_w, base_h):
        frame = frame.resize((detail_w, detail_h), _RESAMPLE_BOX).resize(
            (base_w, base_h), _RESAMPLE_BILINEAR
        )
    else:
        frame = frame.resize((base_w, base_h), _RESAMPLE_BILINEAR)
    pix = frame.load()

    out = Image.new(
        "RGB",
        (int(cell_width) * base_w, int(cell_height) * base_h),
        color=(bg_brightness, bg_brightness, bg_brightness),
    )
    draw = ImageDraw.Draw(out)
    if font is None:
        font = _load_font(font_path)
    if char_map is None:
        char_map = [converter.get_char(i) for i in range(256)]
    assert char_map is not None

    if grayscale_mode not in ("avg", "luma601", "luma709"):
        grayscale_mode = "avg"

    is_avg = grayscale_mode == "avg"
    wr = wg = wb = 0
    if not is_avg:
        if grayscale_mode == "luma601":
            wr, wg, wb = 77, 150, 29
        else:
            wr, wg, wb = 54, 183, 19

    if dither not in ("none", "floyd-steinberg", "atkinson"):
        dither = "none"

    levels = len(converter.char_array)
    levels_m1 = max(1, levels - 1)

    if dither == "none":
        for y in range(base_h):
            for x in range(base_w):
                r, g, b = pix[x, y]
                if is_avg:
                    h = (r + g + b) // 3
                else:
                    h = (wr * r + wg * g + wb * b) >> 8
                ch = char_map[h]
                color = (h, h, h) if mono else (r, g, b)
                draw.text(
                    (x * int(cell_width), y * int(cell_height)),
                    ch,
                    font=font,
                    fill=color,
                )
        return out

    if dither == "floyd-steinberg":
        err_curr = [0.0] * (base_w + 2)
        err_next = [0.0] * (base_w + 2)
        for y in range(base_h):
            err_curr, err_next = err_next, [0.0] * (base_w + 2)
            for x in range(base_w):
                r, g, b = pix[x, y]
                base = (r + g + b) // 3 if is_avg else (wr * r + wg * g + wb * b) >> 8
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

                ch = char_map[qh]
                color = (qh, qh, qh) if mono else (r, g, b)
                draw.text(
                    (x * int(cell_width), y * int(cell_height)),
                    ch,
                    font=font,
                    fill=color,
                )
        return out

    # atkinson
    err_curr = [0.0] * (base_w + 4)
    err_next = [0.0] * (base_w + 4)
    err_next2 = [0.0] * (base_w + 4)
    for y in range(base_h):
        err_curr, err_next, err_next2 = err_next, err_next2, [0.0] * (base_w + 4)
        for x in range(base_w):
            r, g, b = pix[x, y]
            base = (r + g + b) // 3 if is_avg else (wr * r + wg * g + wb * b) >> 8
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

            ch = char_map[qh]
            color = (qh, qh, qh) if mono else (r, g, b)
            draw.text(
                (x * int(cell_width), y * int(cell_height)),
                ch,
                font=font,
                fill=color,
            )

    return out


def _convert_and_collect_outputs(
    inputs: list[InputImage],
    *,
    scale: float,
    brightness: int,
    grayscale_mode: str,
    dither: str,
    cell_width: int,
    cell_height: int,
    output_format: str,
    output_dir: str,
    dynamic_set: bool,
    font_path: str | None,
) -> list[Path]:
    converter.load_char_array(dynamic=dynamic_set, font_path=font_path)
    out_dir = Path(output_dir)
    outputs: list[Path] = []
    for item in inputs:
        base = Path(item.name).stem
        converter.convert_image(
            item.image,
            scale_factor=scale,
            bg_brightness=brightness,
            output_dir=str(out_dir),
            output_format=output_format,
            mono=False,
            font_path=font_path,
            grayscale_mode=grayscale_mode,
            dither=dither,
            cell_width=int(cell_width),
            cell_height=int(cell_height),
            base_name=base,
        )

        ext = {"image": ".png", "text": ".txt", "html": ".html"}.get(output_format)
        if not ext:
            continue
        prefix = f"O_h_{brightness}_f_{scale}_{base}"
        outputs.extend(sorted(out_dir.glob(prefix + "*" + ext)))
    return outputs


def run_app() -> None:
    try:
        import streamlit as st
        import streamlit.components.v1 as components
    except ModuleNotFoundError:
        raise SystemExit(
            "Streamlit is not installed. Install it with: python -m pip install streamlit"
        )

    st.set_page_config(page_title="ASCII Converter", layout="wide")

    cfg = _load_config()

    st.title("ASCII Converter")
    st.caption(
        "Convert images into ASCII art (image/text/html), with a live webcam mode where audio inversely modulates detail."
    )

    with st.sidebar:
        st.header("Settings")

        scale = st.slider(
            "Scale",
            min_value=0.1,
            max_value=1.0,
            value=float(cfg.get("scale", DEFAULTS["scale"])),
            step=0.05,
        )
        brightness = st.slider(
            "Background brightness",
            min_value=0,
            max_value=255,
            value=int(cfg.get("brightness", DEFAULTS["brightness"])),
        )
        grayscale_mode = st.selectbox(
            "Grayscale mode",
            ["avg", "luma601", "luma709"],
            index=["avg", "luma601", "luma709"].index(
                str(cfg.get("grayscale", DEFAULTS["grayscale"]))
            )
            if str(cfg.get("grayscale", DEFAULTS["grayscale"]))
            in ("avg", "luma601", "luma709")
            else 0,
            help="Controls brightness mapping for character selection.",
        )

        dither = st.selectbox(
            "Dither",
            ["none", "floyd-steinberg", "atkinson"],
            index=["none", "floyd-steinberg", "atkinson"].index(
                str(cfg.get("dither", DEFAULTS["dither"]))
            )
            if str(cfg.get("dither", DEFAULTS["dither"]))
            in ("none", "floyd-steinberg", "atkinson")
            else 0,
            help="Error-diffusion dithering for smoother gradients (slower).",
        )

        with st.expander("Advanced", expanded=False):
            cell_width = st.number_input(
                "Cell width (px)",
                min_value=1,
                max_value=200,
                value=int(cfg.get("cell_width", DEFAULTS["cell_width"])),
                step=1,
                help="Character cell width in pixels (image output + aspect correction).",
            )
            cell_height = st.number_input(
                "Cell height (px)",
                min_value=1,
                max_value=200,
                value=int(cfg.get("cell_height", DEFAULTS["cell_height"])),
                step=1,
                help="Character cell height in pixels (image output + aspect correction).",
            )
        output_format = st.selectbox(
            "Output format",
            ["image", "text", "html"],
            index=["image", "text", "html"].index(
                str(cfg.get("format", DEFAULTS["format"]))
            )
            if str(cfg.get("format", DEFAULTS["format"])) in ("image", "text", "html")
            else 0,
        )
        dynamic_set = st.checkbox(
            "Dynamic character set",
            value=bool(cfg.get("dynamic_set", DEFAULTS["dynamic_set"])),
        )
        output_dir = st.text_input(
            "Output directory",
            value=str(cfg.get("output_dir", DEFAULTS["output_dir"])),
        )

        st.subheader("Font (optional)")
        font_path_text = st.text_input(
            "Font path (.ttf)",
            value=str(cfg.get("font_path") or ""),
            help="Optional path to a TTF font. Used for dynamic set generation and image rendering.",
        )
        font_upload = st.file_uploader(
            "Or upload a .ttf font",
            type=["ttf"],
            accept_multiple_files=False,
        )
        uploaded_font_path = _materialize_uploaded_font(font_upload)
        font_path = font_path_text.strip() or uploaded_font_path
        if uploaded_font_path and not font_path_text.strip():
            st.caption(
                f"Using uploaded font: {getattr(font_upload, 'name', 'font.ttf')}"
            )

        st.divider()
        save_defaults = st.button("Save as defaults")

    if save_defaults:
        _save_config(
            {
                "scale": scale,
                "brightness": brightness,
                "grayscale": grayscale_mode,
                "dither": dither,
                "cell_width": int(cell_width),
                "cell_height": int(cell_height),
                "format": output_format,
                "dynamic_set": dynamic_set,
                "output_dir": output_dir,
                "font_path": font_path_text.strip() or None,
            }
        )
        st.success("Saved to config.json")

    tabs = st.tabs(["Upload", "Live (Webcam + Audio)"])

    with tabs[0]:
        st.subheader("Inputs")
        uploads = st.file_uploader(
            "Upload one or more images",
            type=["png", "jpg", "jpeg", "gif", "bmp", "webp"],
            accept_multiple_files=True,
        )
        inputs = _open_uploaded_images(list(uploads or []))

        if not inputs:
            st.info("Upload images to start. Drag and drop works in the uploader.")
        else:
            col_left, col_right = st.columns([1, 1], gap="large")

            with col_left:
                st.subheader("Preview")
                names = [i.name for i in inputs]
                selected = st.selectbox("Select image", names)
                current = next(i for i in inputs if i.name == selected)
                st.image(current.image, caption=current.name, use_container_width=True)

            with col_right:
                st.subheader("ASCII preview")
                progress = st.progress(0)

                def _progress_cb(done: int, total: int) -> None:
                    if total <= 0:
                        progress.progress(0)
                        return
                    progress.progress(min(1.0, done / total))

                try:
                    preview_text = _ansi_preview(
                        current.image,
                        scale=scale,
                        brightness=brightness,
                        grayscale_mode=grayscale_mode,
                        dither=dither,
                        cell_width=int(cell_width),
                        cell_height=int(cell_height),
                        dynamic_set=dynamic_set,
                        font_path=font_path,
                        progress_cb=_progress_cb,
                    )
                finally:
                    progress.empty()

                st.code(preview_text, language=None)

            st.subheader("Convert")
            convert_all = st.button("Convert all uploads")
            if convert_all:
                with st.spinner("Converting..."):
                    outputs = _convert_and_collect_outputs(
                        inputs,
                        scale=scale,
                        brightness=brightness,
                        grayscale_mode=grayscale_mode,
                        dither=dither,
                        cell_width=int(cell_width),
                        cell_height=int(cell_height),
                        output_format=output_format,
                        output_dir=output_dir,
                        dynamic_set=dynamic_set,
                        font_path=font_path,
                    )
                if not outputs:
                    st.warning("No output files were created.")
                else:
                    st.success(f"Wrote {len(outputs)} file(s) to {output_dir}")

                    for out_path in outputs:
                        st.write(str(out_path))
                        try:
                            data = out_path.read_bytes()
                        except OSError:
                            continue
                        mime = {
                            ".png": "image/png",
                            ".txt": "text/plain",
                            ".html": "text/html",
                        }.get(out_path.suffix.lower(), "application/octet-stream")
                        st.download_button(
                            label=f"Download {out_path.name}",
                            data=data,
                            file_name=out_path.name,
                            mime=mime,
                        )
                        if out_path.suffix.lower() == ".png":
                            st.image(
                                data,
                                caption=out_path.name,
                                use_container_width=True,
                            )
                        elif out_path.suffix.lower() == ".txt":
                            st.code(
                                data.decode("utf-8", errors="replace"),
                                language=None,
                            )
                        elif out_path.suffix.lower() == ".html":
                            with st.expander(f"Preview HTML: {out_path.name}"):
                                components.html(
                                    data.decode("utf-8", errors="replace"),
                                    height=600,
                                    scrolling=True,
                                )

    with tabs[1]:
        st.subheader("Live webcam ASCII")
        st.caption(
            "Audio (microphone) inversely modulates detail: louder sound -> lower detail."
        )

        try:
            import numpy as np
            import av
            from streamlit_webrtc import (
                AudioProcessorBase,
                VideoProcessorBase,
                WebRtcMode,
                webrtc_streamer,
            )
        except ModuleNotFoundError:
            st.error(
                "Install live-mode deps: python -m pip install streamlit-webrtc numpy"
            )
            return

        if "_shared_audio" not in st.session_state:
            st.session_state["_shared_audio"] = _SharedAudioLevel()
        shared_audio: _SharedAudioLevel = st.session_state["_shared_audio"]

        if "_live_key" not in st.session_state:
            st.session_state["_live_key"] = 0
        if st.button("Restart webcam"):
            st.session_state["_live_key"] += 1

        # Prepare global charset once for the live processors.
        converter.load_char_array(dynamic=dynamic_set, font_path=font_path)
        max_charset = len(converter.char_array)

        live_base_scale = st.slider(
            "Base scale",
            min_value=0.05,
            max_value=0.5,
            value=float(min(0.25, scale)),
            step=0.01,
        )
        min_scale = st.slider("Min scale", 0.03, 0.3, 0.06, 0.01)
        max_scale = st.slider("Max scale", 0.05, 0.7, 0.25, 0.01)
        audio_gain = st.slider(
            "Audio gain",
            min_value=0.5,
            max_value=50.0,
            value=12.0,
            step=0.5,
            help="Scales microphone RMS into a 0..1 level.",
        )
        audio_sensitivity = st.slider(
            "Inverse strength",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            help="Higher = louder sound reduces detail more.",
        )
        live_mono = st.checkbox("Mono (grayscale)", value=True)

        mod_charset = st.checkbox("Also reduce charset when loud", value=False)
        charset_min = 4
        charset_strength = 0.0
        if mod_charset:
            charset_min = st.slider(
                "Min charset size", 2, max_charset, min(16, max_charset)
            )
            charset_strength = st.slider(
                "Charset reduction strength", 0.0, 10.0, 3.0, 0.1
            )

        class _AudioProc(AudioProcessorBase):
            def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
                samples = frame.to_ndarray()
                if samples.size == 0:
                    return frame
                x = samples
                if x.dtype.kind in "iu":
                    denom = float(np.iinfo(x.dtype).max) or 1.0
                    x = x.astype(np.float32) / denom
                else:
                    x = x.astype(np.float32)
                rms = float(np.sqrt(np.mean(x * x)))
                shared_audio.set_rms(rms)
                return frame

        class _VideoProc(VideoProcessorBase):
            def __init__(self) -> None:
                self._font = ImageFont.load_default()
                self._char_key: tuple[int, int] | None = None
                self._char_map: list[str] | None = None

            def _ensure_font(self) -> None:
                if font_path:
                    try:
                        self._font = ImageFont.truetype(font_path, int(cell_height))
                    except OSError:
                        self._font = ImageFont.load_default()
                else:
                    self._font = ImageFont.load_default()

            def _build_char_map(self, size: int) -> list[str]:
                chars = converter.char_array[
                    : max(2, min(size, len(converter.char_array)))
                ]
                interval = len(chars) / 256.0
                out: list[str] = []
                for i in range(256):
                    idx = int(i * interval)
                    if idx >= len(chars):
                        idx = len(chars) - 1
                    out.append(chars[idx])
                return out

            def _ensure_char_map(self, size: int) -> None:
                key = (id(converter.char_array), int(size))
                if self._char_key != key or self._char_map is None:
                    self._char_map = self._build_char_map(int(size))
                    self._char_key = key

            def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
                self._ensure_font()

                rms = shared_audio.get_rms()
                level = _clamp(rms * float(audio_gain), 0.0, 1.0)

                charset_size = len(converter.char_array)
                if mod_charset and charset_strength > 0:
                    charset_size = int(
                        _clamp(
                            len(converter.char_array)
                            / (1.0 + level * charset_strength),
                            float(charset_min),
                            float(len(converter.char_array)),
                        )
                    )
                self._ensure_char_map(charset_size)

                dyn_scale = _scale_from_audio_inverse(
                    base_scale=float(live_base_scale),
                    audio_level_0_to_1=float(level),
                    sensitivity=float(audio_sensitivity),
                    min_scale=float(min_scale),
                    max_scale=float(max_scale),
                )

                pil = Image.fromarray(frame.to_ndarray(format="rgb24"))
                out = _render_ascii_image(
                    pil,
                    scale_factor=float(live_base_scale),
                    detail_scale=float(dyn_scale),
                    bg_brightness=int(brightness),
                    mono=bool(live_mono),
                    font_path=font_path,
                    grayscale_mode=grayscale_mode,
                    dither=dither,
                    cell_width=int(cell_width),
                    cell_height=int(cell_height),
                    font=self._font,
                    char_map=self._char_map,
                )
                out_np = np.array(out, dtype=np.uint8)
                return av.VideoFrame.from_ndarray(out_np, format="rgb24")

        webrtc_streamer(
            key=f"ascii-live-{st.session_state['_live_key']}",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": True, "audio": True},
            video_processor_factory=_VideoProc,
            audio_processor_factory=_AudioProc,
            async_processing=True,
        )


if __name__ == "__main__":
    run_app()
