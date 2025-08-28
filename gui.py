import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

import ascii as ascii_mod


def _default_output_dir():
    return "./assets/output"


class AsciiGui(tk.Tk):
    """Simple Tkinter based interface for the ASCII converter."""

    def __init__(self):
        super().__init__()
        self.title("ASCII Converter")
        self.geometry("600x400")

        self.input_path = tk.StringVar()
        self.scale = tk.DoubleVar(value=0.2)
        self.brightness = tk.IntVar(value=30)
        self.format_var = tk.StringVar(value="image")
        self.dynamic_set = tk.BooleanVar()
        self.output_dir = tk.StringVar(value=_default_output_dir())
        self.preview = None

        # Input file controls
        tk.Label(self, text="Input image:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self, textvariable=self.input_path, width=40).grid(
            row=0, column=1, padx=5, pady=5, sticky="we"
        )
        tk.Button(self, text="Browse", command=self.browse).grid(
            row=0, column=2, padx=5, pady=5
        )

        # Scale slider
        tk.Label(self, text="Scale:").grid(row=1, column=0, sticky="w", padx=5)
        tk.Scale(
            self,
            from_=0.05,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.scale,
        ).grid(row=1, column=1, columnspan=2, sticky="we", padx=5)

        # Brightness slider
        tk.Label(self, text="Brightness:").grid(row=2, column=0, sticky="w", padx=5)
        tk.Scale(
            self,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self.brightness,
        ).grid(row=2, column=1, columnspan=2, sticky="we", padx=5)

        # Output format
        tk.Label(self, text="Format:").grid(row=3, column=0, sticky="w", padx=5)
        tk.OptionMenu(
            self, self.format_var, "image", "text", "html"
        ).grid(row=3, column=1, sticky="w", padx=5)

        # Dynamic set checkbox
        tk.Checkbutton(
            self, text="Dynamic character set", variable=self.dynamic_set
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=5)

        # Output directory entry
        tk.Label(self, text="Output dir:").grid(row=5, column=0, sticky="w", padx=5)
        tk.Entry(self, textvariable=self.output_dir, width=40).grid(
            row=5, column=1, padx=5, pady=5, sticky="we"
        )
        tk.Button(self, text="Browse", command=self.browse_output).grid(
            row=5, column=2, padx=5, pady=5
        )

        # Convert button
        tk.Button(self, text="Convert", command=self.convert).grid(
            row=6, column=0, columnspan=3, pady=10
        )

        # Preview label
        self.preview_label = tk.Label(self)
        self.preview_label.grid(row=7, column=0, columnspan=3, pady=5)

        self.columnconfigure(1, weight=1)

    def browse(self):
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
            ("All files", "*.*"),
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.input_path.set(filename)

    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def convert(self):
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an image file")
            return

        ascii_mod.load_char_array(dynamic=self.dynamic_set.get())
        out_paths = ascii_mod.convert_image(
            self.input_path.get(),
            scale_factor=self.scale.get(),
            bg_brightness=self.brightness.get(),
            output_dir=self.output_dir.get(),
            output_format=self.format_var.get(),
        )
        if not out_paths:
            messagebox.showerror("Error", "Conversion failed")
            return

        if self.format_var.get() == "image":
            img = Image.open(out_paths[0])
            self.preview = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self.preview)
        else:
            self.preview_label.configure(text="Conversion complete")
        messagebox.showinfo("Success", f"Saved to {', '.join(out_paths)}")


def main():
    app = AsciiGui()
    app.mainloop()


if __name__ == "__main__":
    main()
