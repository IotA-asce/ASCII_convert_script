import io
import contextlib
import re
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
from pathlib import Path

from PIL import ImageGrab
from tkinterdnd2 import DND_FILES, TkinterDnD

from ascii import convert_image


class AsciiGui(TkinterDnD.Tk):
    """Simple Tkinter interface for converting images to ASCII art."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ASCII Converter")
        self.geometry("800x600")

        self.input_path = None
        self._update_job = None

        # allow dropping files onto the main window
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

        controls = tk.Frame(self)
        controls.pack(fill="x")

        tk.Button(controls, text="Select Image", command=self.select_file).pack(side="left")

        tk.Label(controls, text="Scale").pack(side="left", padx=(10, 0))
        self.scale_var = tk.DoubleVar(value=0.2)
        self.scale = tk.Scale(
            controls,
            from_=0.1,
            to=1.0,
            orient="horizontal",
            resolution=0.05,
            variable=self.scale_var,
        )
        self.scale.pack(side="left")
        self.scale.bind("<Motion>", self.schedule_preview)
        self.scale.bind("<ButtonRelease>", self.schedule_preview)

        tk.Label(controls, text="Brightness").pack(side="left", padx=(10, 0))
        self.brightness_var = tk.IntVar(value=30)
        self.brightness = tk.Scale(
            controls,
            from_=0,
            to=255,
            orient="horizontal",
            variable=self.brightness_var,
        )
        self.brightness.pack(side="left")
        self.brightness.bind("<Motion>", self.schedule_preview)
        self.brightness.bind("<ButtonRelease>", self.schedule_preview)

        tk.Label(controls, text="Format").pack(side="left", padx=(10, 0))
        self.format_var = tk.StringVar(value="image")
        tk.OptionMenu(controls, self.format_var, "image", "text", "html").pack(
            side="left"
        )

        tk.Button(controls, text="Convert", command=self.convert_file).pack(
            side="left", padx=(10, 0)
        )
        self.copy_button = tk.Button(
            controls, text="Copy to Clipboard", command=self.copy_image
        )
        self.copy_button.pack(side="left")
        self.copy_button.pack_forget()

        self.preview_label = scrolledtext.ScrolledText(self, wrap="none")
        self.preview_label.pack(expand=True, fill="both")

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x")
        self.progress.pack_forget()

    def select_file(self) -> None:
        """Prompt for an input image and refresh the preview."""
        path = filedialog.askopenfilename()
        if path:
            self.input_path = path
            self.update_preview()

    def _on_drop(self, event) -> str:
        """Handle a file being dropped onto the window."""
        paths = self.tk.splitlist(event.data)
        if paths:
            self.input_path = paths[0]
            self.update_preview()
        return event.action

    def schedule_preview(self, _event=None) -> None:
        """Debounce preview updates when sliders are moved."""
        if self._update_job is not None:
            self.after_cancel(self._update_job)
        self._update_job = self.after(200, self.update_preview)

    def update_preview(self) -> None:
        """Run conversion and display ASCII art in the preview box."""
        if not self.input_path:
            return
        if self._update_job is not None:
            self.after_cancel(self._update_job)
            self._update_job = None
        scale = self.scale_var.get()
        brightness = self.brightness_var.get()
        self.progress["value"] = 0
        self.progress.pack(fill="x")

        def _progress(done, total):
            self.after(0, lambda: self._update_progress(done, total))

        def _worker():
            buffer = io.BytesIO()
            try:
                with contextlib.redirect_stdout(
                    io.TextIOWrapper(buffer, encoding="utf-8", write_through=True)
                ):
                    convert_image(
                        self.input_path,
                        scale_factor=scale,
                        bg_brightness=brightness,
                        output_format="ansi",
                        mono=True,
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

    def convert_file(self) -> None:
        if not self.input_path:
            return
        scale = self.scale_var.get()
        brightness = self.brightness_var.get()
        fmt = self.format_var.get()
        convert_image(
            self.input_path,
            scale_factor=scale,
            bg_brightness=brightness,
            output_format=fmt,
        )
        base = Path(self.input_path).stem
        file_stem = f"O_h_{brightness}_f_{scale}_{base}"
        ext = {"image": ".png", "text": ".txt", "html": ".html"}[fmt]
        output_path = Path("./assets/output") / (file_stem + ext)
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


def main() -> None:
    app = AsciiGui()
    app.mainloop()


if __name__ == "__main__":
    main()
