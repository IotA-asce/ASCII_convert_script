import os
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, scrolledtext

from ascii import convert_image


class App(tk.Tk):
    """Simple Tkinter interface for converting images to ASCII art."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ASCII Converter")
        self.geometry("800x600")

        self.file_path = None
        self.temp_dir = tempfile.mkdtemp()

        controls = tk.Frame(self)
        controls.pack(fill="x")

        tk.Button(controls, text="Select Image", command=self.select_file).pack(side="left")

        tk.Label(controls, text="Scale").pack(side="left", padx=(10, 0))
        self.scale_var = tk.DoubleVar(value=0.2)
        tk.Scale(
            controls,
            from_=0.1,
            to=1.0,
            orient="horizontal",
            resolution=0.05,
            variable=self.scale_var,
            command=lambda _evt: self.update_preview(),
        ).pack(side="left")

        tk.Label(controls, text="Brightness").pack(side="left", padx=(10, 0))
        self.brightness_var = tk.IntVar(value=30)
        tk.Scale(
            controls,
            from_=0,
            to=255,
            orient="horizontal",
            variable=self.brightness_var,
            command=lambda _evt: self.update_preview(),
        ).pack(side="left")

        self.preview = scrolledtext.ScrolledText(self, wrap="none")
        self.preview.pack(expand=True, fill="both")

    def select_file(self) -> None:
        """Prompt for an input image and refresh the preview."""
        path = filedialog.askopenfilename()
        if path:
            self.file_path = path
            self.update_preview()

    def update_preview(self) -> None:
        """Run conversion and display ASCII art in the preview box."""
        if not self.file_path:
            return
        scale = self.scale_var.get()
        brightness = self.brightness_var.get()
        base = Path(self.file_path).stem
        convert_image(
            self.file_path,
            scale_factor=scale,
            bg_brightness=brightness,
            output_dir=self.temp_dir,
            output_format="text",
            base_name=base,
        )
        out_file = os.path.join(self.temp_dir, f"O_h_{brightness}_f_{scale}_{base}.txt")
        try:
            with open(out_file, "r", encoding="utf-8") as fh:
                content = fh.read()
        except FileNotFoundError:
            return
        self.preview.delete("1.0", tk.END)
        self.preview.insert(tk.END, content)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
