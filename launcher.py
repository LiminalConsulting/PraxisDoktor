"""
PraxisDoktor Launcher
=====================
Tiny entry point compiled to PraxisDoktor.exe.
Finds the app source next to the EXE and runs it via uv.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
APP_DIR = BASE_DIR / "app"


def main():
    if not (APP_DIR / "main.py").exists():
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "PraxisDoktor",
            f"App-Verzeichnis nicht gefunden:\n{APP_DIR}\n\n"
            "Bitte PraxisDoktorSetup.exe erneut ausführen.",
        )
        root.destroy()
        sys.exit(1)

    subprocess.Popen(
        ["uv", "run", "python", "main.py"],
        cwd=str(APP_DIR),
    )


if __name__ == "__main__":
    main()
