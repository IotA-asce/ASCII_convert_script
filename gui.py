import io
import contextlib
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext

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

        self.preview_label = scrolledtext.ScrolledText(self, wrap="none")
        self.preview_label.pack(expand=True, fill="both")

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
        buffer = io.BytesIO()
        with contextlib.redirect_stdout(
            io.TextIOWrapper(buffer, encoding="utf-8", write_through=True)
        ):
            convert_image(
                self.input_path,
                scale_factor=scale,
                bg_brightness=brightness,
                output_format="ansi",
                mono=True,
            )
        content = buffer.getvalue().decode("utf-8")
        content = re.sub(r"\x1b\[[0-9;]*m", "", content).lstrip("\n")
        self.preview_label.delete("1.0", tk.END)
        self.preview_label.insert(tk.END, content)


def main() -> None:
    app = AsciiGui()
    app.mainloop()


if __name__ == "__main__":
    main()
