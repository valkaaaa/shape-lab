"""Плавающая подсказка."""
import tkinter as tk

__all__ = ["Tooltip"]


class Tooltip:
    def __init__(self, root, offset=(16, 16)):
        self.root = root
        self.offset = offset
        self.win = None
        self.label = None
        self._last_text = None

    def show(self, x_root, y_root, text):
        if self.win is None:
            self.win = tk.Toplevel(self.root)
            self.win.wm_overrideredirect(True)
            try:
                self.win.attributes("-topmost", True)
            except tk.TclError:
                pass
            self.label = tk.Label(
                self.win, background="#fffde7", foreground="#222",
                relief="solid", borderwidth=1,
                font=("Consolas", 9), justify="left", padx=6, pady=4)
            self.label.pack()
        if text != self._last_text:
            self.label.config(text=text)
            self._last_text = text
        self.win.wm_geometry(f"+{x_root + self.offset[0]}+{y_root + self.offset[1]}")

    def hide(self):
        if self.win is not None:
            self.win.destroy()
            self.win = None
            self.label = None
            self._last_text = None