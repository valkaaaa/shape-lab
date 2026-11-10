"""ShapeLab — точка входа."""
import os
import sys
import tkinter as tk

from shapelab import App, __version__


def _resource(name: str) -> str:
    """Путь к ресурсу: работает и в dev, и в PyInstaller --onefile."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main():
    # Иконка на панели задач Windows
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                f"Valkaaaa.ShapeLab.{__version__}")
        except Exception:
            pass

    root = tk.Tk()

    # .ico — панель задач и заголовок на Windows
    try:
        root.iconbitmap(_resource(os.path.join("assets", "icon.ico")))
    except tk.TclError:
        pass

    # .png — заголовок на Linux/macOS, плюс fallback для Windows
    try:
        icon = tk.PhotoImage(file=_resource(os.path.join("assets", "icon.png")))
        root.iconphoto(True, icon)
        root._icon = icon       # защита от сборки мусора
    except tk.TclError:
        pass

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()