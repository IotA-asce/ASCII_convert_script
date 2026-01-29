# IMPROVEMENT ITERATION IDEAS

This is a list of small-to-medium iterations (performance, quality, UX, and new features).
Each section is a self-contained checklist.

## 1) Grayscale / luma modes (quality feature)
- [x] Add `--grayscale {avg,luma601,luma709}` (and GUI equivalent)
- [x] Keep default as current behavior (`avg`) for backward compatibility
- [x] Add docs with side-by-side outputs and a short "when to use" note
- [x] Add unit tests that lock down expected mapping for each mode

## 2) Optional dithering (quality feature)
- [x] Add `--dither {none,floyd-steinberg,atkinson}` (GUI toggle)
- [x] Keep it off by default
- [x] Add deterministic tests on a tiny synthetic gradient
- [x] Document best use cases (gradients, low-contrast scenes)

## 3) Configurable character cell size (feature)
- [x] Add `--cell-width` and `--cell-height` (defaults 10x18)
- [x] Apply to aspect correction and output canvas sizing consistently
- [x] Add an "Advanced" section in the GUI for these settings
- [x] Add a smoke test for non-default cell sizes

## 4) Faster `format=image` rendering (performance)
- [x] Cache per-character glyph masks for the chosen font + size
- [x] Replace per-character `ImageDraw.text` calls with batched compositing
- [x] Add `scripts/benchmark.py` (time + output dimensions)
- [x] Track regressions with an optional benchmark job in CI

## 5) Animated outputs (feature)
- [x] Add `--assemble` for animated input images (GIF/WebP) to write an animated GIF
- [x] Add `--gif-fps` / `--gif-loop` options
- [x] Add `--video-out {frames,gif,mp4}` (mp4 via ffmpeg if available)
- [x] Document limitations (palette, file size, fps)

## 6) Compact HTML output (feature + performance)
- [x] Add `--html {spans,compact}`
- [x] Implement palette quantization + CSS classes to shrink file size
- [x] Optionally group repeated runs of identical style
- [x] Add an example HTML output in `docs/examples/`

## 7) New output formats (feature)
- [ ] Add `--format md` (markdown with fenced code blocks)
- [ ] Add `--format svg` (vector output with `<text>` / `<tspan>`)
- [ ] Add `--format json` (matrix of chars + optional colors)
- [ ] Add focused tests for each new format

## 8) Library-first API (feature)
- [ ] Add `ascii_art/api.py` that returns strings / PIL images without file IO
- [ ] Keep `ascii_art/converter.py` as the low-level engine
- [ ] Document usage examples (importable API)
- [ ] Add unit tests that call the API directly

## 9) CLI preview / inspect mode (UX feature)
- [ ] Add `--preview` to print a small text preview to stdout
- [ ] Add `--info` to print computed dimensions (chars, output pixels)
- [ ] Add `--dry-run` to validate inputs and show what would be written
- [ ] Document common workflows

## 10) Better color handling (feature)
- [ ] Add `--colors N` palette quantization for image/html/ansi outputs
- [ ] Add `--ansi-palette {truecolor,256,16}`
- [ ] Add `--mono` + `--grayscale` interactions documentation
- [ ] Add a test asserting unique colors <= N (where applicable)

## 11) Charsets and presets (feature)
- [ ] Add presets: `standard`, `ascii-only`, `blocks`, `dense`, `unicode-lite`
- [ ] Add `--charset preset` and `--charset-file path.txt`
- [ ] Add a GUI charset picker + preview
- [ ] Add tests for parsing and empty/invalid charset files

## 12) Tone controls (feature)
- [ ] Add `--invert` (flip mapping)
- [ ] Add `--contrast`, `--gamma`, and optional `--brightness-offset`
- [ ] Ensure values are clamped and documented
- [ ] Add tiny fixture tests demonstrating each control

## 13) Improve input path behavior (UX)
- [ ] Make CLI accept relative paths outside `assets/input/`
- [ ] Use `pathlib.Path` consistently for file handling
- [ ] Improve error messages (show resolved path)
- [ ] Add tests for relative and absolute path cases

## 14) Video/webcam robustness (feature)
- [ ] Guard optional deps (`cv2`, `imageio`) with clear install hints
- [ ] Add `--max-frames` and `--fps` controls
- [ ] Add a webcam mode with graceful shutdown and a frame limit
- [ ] Add unit tests for dependency error messages

## 15) Parallel processing (performance feature)
- [ ] Add `--workers N` (image batch + video)
- [ ] Keep output ordering stable
- [ ] Document when multiprocessing helps (and when it hurts)
- [ ] Add a small benchmark for batch conversion

## 16) Streamlit UX improvements (feature)
- [ ] Add a "Reset to defaults" button
- [ ] Add a side-by-side view: input vs output, zoom, and scroll sync
- [ ] Add a ZIP download option for batch outputs
- [ ] Add tooltips that mirror CLI docs for each control

## 17) Live mode creative controls (feature)
- [ ] Add audio mapping modes: inverse-scale (current), direct-scale, threshold, beat-detect
- [ ] Add smoothing / attack-release sliders for audio response
- [ ] Add an optional "reduce colors when loud" mode
- [ ] Add a record button to export a short GIF/MP4 clip
- [x] Stabilize live output size (avoid webcam display jitter when audio changes scale)

## 18) Testing improvements (quality)
- [ ] Add deterministic snapshot tests for text outputs
- [ ] Add a tiny golden-image test for PNG output (tolerant / hashed)
- [ ] Add `python -m compileall ascii_art` to CI
- [ ] Keep tests fast and hermetic (use `tmp_path`)

## 19) Tooling and CI (maintenance)
- [ ] Add GitHub Actions workflow for Python 3.10-3.13
- [ ] Add optional `ruff` (lint + format) when ready
- [ ] Add `pre-commit` config (optional)
- [ ] Document contributor setup steps

## 20) Packaging and distribution (feature)
- [ ] Add `pyproject.toml` for packaging
- [ ] Provide console scripts: `ascii-art` and `ascii-art-gui`
- [ ] Add a Dockerfile for one-command demo runs (optional)
- [ ] Publish a versioned release workflow (tags + changelog)
