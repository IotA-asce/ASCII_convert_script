import io
import contextlib
import re
import threading
import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
from pathlib import Path

from PIL import ImageGrab
from tkinterdnd2 import DND_FILES, TkinterDnD

from ascii import convert_image, load_char_array


CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
DEFAULTS = {
    "input_paths": [],
    "scale": 0.2,
    "brightness": 30,
    "format": "image",
    "dynamic_set": False,
    "output_dir": "./assets/output",
    "font_path": None,
    "theme": "light",
}

THEMES = {
    "light": {"bg": "#ffffff", "fg": "#000000", "accent": "#007fff"},
    "dark": {"bg": "#2e2e2e", "fg": "#f0f0f0", "accent": "#4f9dff"},
}


class AsciiGui(TkinterDnD.Tk):
    """Simple Tkinter interface for converting images to ASCII art."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ASCII Converter")
        self.geometry("800x600")

        self.input_paths: list[str] = []
        self._update_job = None
        self.output_dir = DEFAULTS["output_dir"]
        self.font_path = DEFAULTS["font_path"]

        self.menubar = tk.Menu(self)
        self.opts = tk.Menu(self.menubar, tearoff=0)
        self.opts.add_command(label="Reset to defaults", command=self.reset_defaults)
        self.theme_var = tk.StringVar(value=DEFAULTS["theme"])
        self.theme_menu = tk.Menu(self.opts, tearoff=0)
        self.theme_menu.add_radiobutton(
            label="Light",
            value="light",
            variable=self.theme_var,
            command=self.apply_theme,
        )
        self.theme_menu.add_radiobutton(
            label="Dark",
            value="dark",
            variable=self.theme_var,
            command=self.apply_theme,
        )
        self.opts.add_cascade(label="Theme", menu=self.theme_menu)
        self.menubar.add_cascade(label="Options", menu=self.opts)
        self.config(menu=self.menubar)

        # allow dropping files onto the main window
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

        self.file_frame = tk.Frame(self)
        self.file_frame.pack(fill="x")
        self.file_list = tk.Listbox(self.file_frame, selectmode="browse")
        self.file_list.pack(side="left", fill="both", expand=True)
        self.btn_frame = tk.Frame(self.file_frame)
        self.btn_frame.pack(side="left", padx=(5, 0))
        tk.Button(self.btn_frame, text="Add", command=self.add_files).pack(fill="x")
        tk.Button(self.btn_frame, text="Remove", command=self.remove_selected).pack(
            fill="x", pady=(5, 0)
        )

        self.controls = tk.Frame(self)
        self.controls.pack(fill="x")

        tk.Label(self.controls, text="Scale").pack(side="left", padx=(10, 0))
        self.scale_var = tk.DoubleVar(value=DEFAULTS["scale"])
        self.scale = tk.Scale(
            self.controls,
            from_=0.1,
            to=1.0,
            orient="horizontal",
            resolution=0.05,
            variable=self.scale_var,
        )
        self.scale.pack(side="left")
        self.scale.bind("<Motion>", self.schedule_preview)
        self.scale.bind("<ButtonRelease>", self.schedule_preview)

        tk.Label(self.controls, text="Brightness").pack(side="left", padx=(10, 0))
        self.brightness_var = tk.IntVar(value=DEFAULTS["brightness"])
        self.brightness = tk.Scale(
            self.controls,
            from_=0,
            to=255,
            orient="horizontal",
            variable=self.brightness_var,
        )
        self.brightness.pack(side="left")
        self.brightness.bind("<Motion>", self.schedule_preview)
        self.brightness.bind("<ButtonRelease>", self.schedule_preview)

        tk.Label(self.controls, text="Format").pack(side="left", padx=(10, 0))
        self.format_var = tk.StringVar(value=DEFAULTS["format"])
        self.format_menu = tk.OptionMenu(
            self.controls, self.format_var, "image", "text", "html"
        )
        self.format_menu.pack(side="left")

        self.dynamic_var = tk.BooleanVar(value=DEFAULTS["dynamic_set"])
        tk.Checkbutton(
            self.controls,
            text="Dynamic set",
            variable=self.dynamic_var,
            command=self.schedule_preview,
        ).pack(side="left", padx=(10, 0))

        tk.Button(self.controls, text="Font...", command=self.select_font).pack(
            side="left", padx=(10, 0)
        )
        self.font_var = tk.StringVar(value="System font")
        tk.Label(self.controls, textvariable=self.font_var).pack(side="left")

        tk.Button(
            self.controls, text="Output Dir", command=self.select_output_dir
        ).pack(
            side="left", padx=(10, 0)
        )

        tk.Button(self.controls, text="Convert", command=self.convert_files).pack(
            side="left", padx=(10, 0)
        )
        self.copy_button = tk.Button(
            self.controls, text="Copy to Clipboard", command=self.copy_image
        )
        self.copy_button.pack(side="left")
        self.copy_button.pack_forget()

        self.preview_label = scrolledtext.ScrolledText(self, wrap="none")
        self.preview_label.pack(expand=True, fill="both")

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x")
        self.progress.pack_forget()

        self.style = ttk.Style(self)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.load_config()

    def add_files(self) -> None:
        """Prompt for input images and refresh the preview."""
        paths = filedialog.askopenfilenames()
        for path in paths:
            if path and path not in self.input_paths:
                self.input_paths.append(path)
                self.file_list.insert(tk.END, path)
        if self.input_paths:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(0)
            self.update_preview()

    def remove_selected(self) -> None:
        sel = list(self.file_list.curselection())
        for index in reversed(sel):
            path = self.file_list.get(index)
            self.input_paths.remove(path)
            self.file_list.delete(index)
        if not self.input_paths:
            self.preview_label.delete("1.0", tk.END)
        else:
            self.file_list.selection_set(0)
            self.update_preview()

    def select_font(self) -> None:
        """Prompt for a TTF font and refresh the preview."""
        path = filedialog.askopenfilename(
            filetypes=[("TrueType Font", "*.ttf"), ("All Files", "*.*")]
        )
        if path:
            self.font_path = path
            self.font_var.set(Path(path).name)
            self.schedule_preview()

    def select_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir = path

    def _on_drop(self, event) -> str:
        """Handle a file being dropped onto the window."""
        paths = self.tk.splitlist(event.data)
        added = False
        for path in paths:
            if path and path not in self.input_paths:
                self.input_paths.append(path)
                self.file_list.insert(tk.END, path)
                added = True
        if added:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(0)
            self.update_preview()
        return event.action

    def schedule_preview(self, _event=None) -> None:
        """Debounce preview updates when sliders are moved."""
        if self._update_job is not None:
            self.after_cancel(self._update_job)
        self._update_job = self.after(200, self.update_preview)

    def update_preview(self) -> None:
        """Run conversion and display ASCII art in the preview box."""
        if not self.input_paths:
            return
        if self._update_job is not None:
            self.after_cancel(self._update_job)
            self._update_job = None
        sel = self.file_list.curselection()
        if sel:
            path = self.file_list.get(sel[0])
        else:
            path = self.input_paths[0]
            self.file_list.selection_set(0)
        scale = self.scale_var.get()
        brightness = self.brightness_var.get()
        self.progress["value"] = 0
        self.progress.pack(fill="x")

        def _progress(done, total):
            self.after(0, lambda: self._update_progress(done, total))

        def _worker():
            load_char_array(dynamic=self.dynamic_var.get(), font_path=self.font_path)
            buffer = io.BytesIO()
            try:
                with contextlib.redirect_stdout(
                    io.TextIOWrapper(buffer, encoding="utf-8", write_through=True)
                ):
                    convert_image(
                        path,
                        scale_factor=scale,
                        bg_brightness=brightness,
                        output_dir=self.output_dir,
                        output_format="ansi",
                        mono=True,
                        font_path=self.font_path,
                        progress_callback=_progress,
                    )
                content = buffer.getvalue().decode("utf-8")
            except Exception:
                content = None
            self.after(0, lambda: self._finish_preview(content))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_progress(self, done: int, total: int) -> None:
        self.progress["maximum"] = total
        self.progress["value"] = done

    def _finish_preview(self, content: str | None) -> None:
        self.progress.pack_forget()
        if content is None:
            return
        content = re.sub(r"\x1b\[[0-9;]*m", "", content).lstrip("\n")
        self.preview_label.delete("1.0", tk.END)
        self.preview_label.insert(tk.END, content)

    def convert_files(self) -> None:
        if not self.input_paths:
            return
        scale = self.scale_var.get()
        brightness = self.brightness_var.get()
        fmt = self.format_var.get()
        files = list(self.input_paths)
        total = len(files)
        self.progress["value"] = 0
        self.progress["maximum"] = total
        self.progress.pack(fill="x")

        def _worker():
            load_char_array(dynamic=self.dynamic_var.get(), font_path=self.font_path)
            for i, path in enumerate(files, 1):
                convert_image(
                    path,
                    scale_factor=scale,
                    bg_brightness=brightness,
                    output_dir=self.output_dir,
                    output_format=fmt,
                    font_path=self.font_path,
                )
                self.after(0, lambda done=i: self._update_progress(done, total))
            self.after(0, lambda: self._finish_convert(files, fmt, brightness, scale))

        threading.Thread(target=_worker, daemon=True).start()

    def _finish_convert(self, files, fmt, brightness, scale) -> None:
        self.progress.pack_forget()
        first = files[0]
        base = Path(first).stem
        file_stem = f"O_h_{brightness}_f_{scale}_{base}"
        ext = {"image": ".png", "text": ".txt", "html": ".html"}[fmt]
        output_path = Path(self.output_dir) / (file_stem + ext)
        if fmt in ("text", "html"):
            try:
                with open(output_path, "r", encoding="utf-8") as fh:
                    data = fh.read()
                self.clipboard_clear()
                self.clipboard_append(data)
            except OSError:
                pass
            self.copy_button.pack_forget()
        else:
            self.copy_button.pack(side="left")
        if messagebox.askyesno("Preview", "Preview first result?"):
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(0)
            self.update_preview()

    def copy_image(self) -> None:
        x = self.preview_label.winfo_rootx()
        y = self.preview_label.winfo_rooty()
        w = self.preview_label.winfo_width()
        h = self.preview_label.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        output = io.BytesIO()
        img.save(output, format="PNG")
        data = output.getvalue()
        self.clipboard_clear()
        try:
            self.clipboard_append(data, type="image/png")
        except tk.TclError:
            import base64
            self.clipboard_append(base64.b64encode(data).decode("ascii"))

    def apply_theme(self) -> None:
        theme = THEMES.get(self.theme_var.get(), THEMES["light"])
        bg = theme["bg"]
        fg = theme["fg"]

        # configure ttk styles
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background=bg, foreground=fg)
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.configure("TMenubutton", background=bg, foreground=fg)
        self.style.configure(
            "Theme.TProgressbar",
            background=theme["accent"],
            troughcolor=bg,
        )
        self.progress.configure(style="Theme.TProgressbar")

        # tk widgets
        self.configure(bg=bg)

        def _recurse(widget):
            for child in widget.winfo_children():
                try:
                    child.configure(bg=bg, fg=fg)
                except tk.TclError:
                    try:
                        child.configure(bg=bg)
                    except tk.TclError:
                        pass
                _recurse(child)

        _recurse(self)

        self.preview_label.configure(insertbackground=fg)
        self.file_list.configure(
            selectbackground=theme["accent"], selectforeground=fg
        )
        # menus need explicit configuration
        for menu in [self.menubar, self.opts, self.theme_menu, self.format_menu["menu"]]:
            try:
                menu.configure(bg=bg, fg=fg)
            except tk.TclError:
                pass

    def load_config(self) -> None:
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}
        paths = data.get("input_paths") or []
        if not paths and data.get("input_path"):
            paths = [data.get("input_path")]
        self.input_paths = []
        for p in paths:
            if p:
                self.input_paths.append(p)
                self.file_list.insert(tk.END, p)
        if self.input_paths:
            self.file_list.selection_set(0)
            self.update_preview()
        self.scale_var.set(data.get("scale", DEFAULTS["scale"]))
        self.brightness_var.set(data.get("brightness", DEFAULTS["brightness"]))
        self.format_var.set(data.get("format", DEFAULTS["format"]))
        self.dynamic_var.set(data.get("dynamic_set", DEFAULTS["dynamic_set"]))
        self.output_dir = data.get("output_dir", DEFAULTS["output_dir"])
        self.font_path = data.get("font_path") or None
        if self.font_path:
            self.font_var.set(Path(self.font_path).name)
        self.theme_var.set(data.get("theme", DEFAULTS["theme"]))
        self.apply_theme()

    def save_config(self) -> None:
        data = {
            "input_paths": self.input_paths,
            "scale": self.scale_var.get(),
            "brightness": self.brightness_var.get(),
            "format": self.format_var.get(),
            "dynamic_set": self.dynamic_var.get(),
            "output_dir": self.output_dir,
            "font_path": self.font_path,
            "theme": self.theme_var.get(),
        }
        try:
            CONFIG_PATH.write_text(json.dumps(data, indent=2))
        except OSError:
            pass

    def on_close(self) -> None:
        self.save_config()
        self.destroy()

    def reset_defaults(self) -> None:
        self.input_paths = []
        self.file_list.delete(0, tk.END)
        self.scale_var.set(DEFAULTS["scale"])
        self.brightness_var.set(DEFAULTS["brightness"])
        self.format_var.set(DEFAULTS["format"])
        self.dynamic_var.set(DEFAULTS["dynamic_set"])
        self.output_dir = DEFAULTS["output_dir"]
        self.font_path = DEFAULTS["font_path"]
        self.font_var.set("System font")
        self.preview_label.delete("1.0", tk.END)
        self.theme_var.set(DEFAULTS["theme"])
        self.apply_theme()
        try:
            CONFIG_PATH.unlink()
        except OSError:
            pass


def main() -> None:
    app = AsciiGui()
    app.mainloop()


if __name__ == "__main__":
    main()
