"""
PraxisDoktor Setup-Assistent
=============================
Doppelklicken zum Starten. Dieses Programm:
1. Installiert uv (Python-Paketmanager, ~10 MB)
2. Prüft ob Ollama installiert ist – lädt es herunter falls nötig
3. Zieht das KI-Modell (llama3.1:8b, ~4.7 GB) herunter
4. Startet PraxisDoktor automatisch im Browser

Kompilierung: pyinstaller --onefile --name PraxisDoktorSetup --noconsole installer_gui.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
import urllib.request
import webbrowser

BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
APP_DIR = BASE_DIR / "app"
OLLAMA_INSTALLER = BASE_DIR / "OllamaSetup.exe"
OLLAMA_URL = "https://ollama.com/download/OllamaSetup.exe"
UV_INSTALLER_URL = "https://github.com/astral-sh/uv/releases/latest/download/uv-installer.ps1"

# Colors
GREEN_DARK = "#3c5a46"
GREEN_LIGHT = "#eaf0ec"
WHITE = "#ffffff"
GREY = "#9e9e9e"
RED = "#e53935"


class SetupApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PraxisDoktor Setup")
        self.root.resizable(False, False)
        self.root.configure(bg=WHITE)

        w, h = 520, 460
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._build_ui()
        self.root.after(300, self._start_setup)

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=GREEN_DARK, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="Urologische Praxis — PraxisDoktor",
            fg=WHITE, bg=GREEN_DARK, font=("Segoe UI", 13, "bold"),
        ).place(relx=0.5, rely=0.4, anchor="center")
        tk.Label(
            hdr, text="Setup-Assistent",
            fg=WHITE, bg=GREEN_DARK, font=("Segoe UI", 9),
        ).place(relx=0.5, rely=0.75, anchor="center")

        body = tk.Frame(self.root, bg=WHITE, padx=30, pady=20)
        body.pack(fill="both", expand=True)

        self.steps_frame = tk.Frame(body, bg=WHITE)
        self.steps_frame.pack(fill="x", pady=(0, 16))

        steps = [
            ("step_uv",      "Python-Laufzeit installieren (uv)"),
            ("step_ollama",  "Ollama prüfen / installieren"),
            ("step_model",   "KI-Modell herunterladen  (~4.7 GB)"),
            ("step_app",     "PraxisDoktor starten"),
        ]
        self.step_labels: dict[str, tuple[tk.Label, tk.Label]] = {}
        for key, text in steps:
            row = tk.Frame(self.steps_frame, bg=WHITE)
            row.pack(fill="x", pady=4)
            icon = tk.Label(row, text="○", fg=GREY, bg=WHITE, font=("Segoe UI", 14), width=2)
            icon.pack(side="left")
            lbl = tk.Label(row, text=text, fg=GREY, bg=WHITE,
                           font=("Segoe UI", 10), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            self.step_labels[key] = (icon, lbl)

        log_frame = tk.Frame(body, bg=WHITE)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(
            log_frame, height=8, state="disabled",
            bg="#f4f6f5", relief="flat", font=("Consolas", 9),
            fg="#333333", wrap="word", padx=8, pady=6,
        )
        sb = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        self.btn = tk.Button(
            body, text="Starte Setup...", state="disabled",
            bg=GREEN_DARK, fg=WHITE, font=("Segoe UI", 10, "bold"),
            relief="flat", padx=20, pady=8, cursor="arrow",
        )
        self.btn.pack(pady=(12, 0), fill="x")

    def _log(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.root.update_idletasks()

    def _set_step(self, key: str, state: str):
        icon_lbl, text_lbl = self.step_labels[key]
        styles = {
            "pending": ("○", GREY,      GREY),
            "active":  ("●", GREEN_DARK, GREEN_DARK),
            "done":    ("✓", "#2e7d32", "#2e7d32"),
            "error":   ("✗", RED,       RED),
        }
        icon_char, icon_color, text_color = styles.get(state, styles["pending"])
        icon_lbl.configure(text=icon_char, fg=icon_color)
        text_lbl.configure(fg=text_color)
        self.root.update_idletasks()

    def _start_setup(self):
        threading.Thread(target=self._run_setup, daemon=True).start()

    def _run_setup(self):
        try:
            self._setup_uv()
            self._setup_app_deps()
            self._setup_ollama()
            self._setup_model()
            self._launch_app()
        except Exception as e:
            self._log(f"\nFehler: {e}")
            self._set_failure()

    # ---- Step 1: uv ----
    def _setup_uv(self):
        self._set_step("step_uv", "active")
        self._log("Prüfe uv (Python-Laufzeit)...")

        if self._uv_installed():
            self._log("  uv ist bereits installiert.")
            self._set_step("step_uv", "done")
            return

        self._log("  Installiere uv...")
        try:
            # uv's official Windows installer via PowerShell
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command",
                    "irm https://astral.sh/uv/install.ps1 | iex",
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr or "uv-Installation fehlgeschlagen")
        except subprocess.TimeoutExpired:
            raise RuntimeError("uv-Download hat zu lange gedauert. Bitte Internetverbindung prüfen.")

        if not self._uv_installed():
            raise RuntimeError("uv konnte nicht installiert werden.")

        self._log("  uv erfolgreich installiert.")
        self._set_step("step_uv", "done")

    def _uv_installed(self) -> bool:
        try:
            r = subprocess.run(["uv", "--version"], capture_output=True, timeout=10)
            return r.returncode == 0
        except Exception:
            # Also check common install location
            uv_path = Path(os.environ.get("USERPROFILE", "")) / ".local" / "bin" / "uv.exe"
            if uv_path.exists():
                # Add to PATH for this process
                os.environ["PATH"] = str(uv_path.parent) + os.pathsep + os.environ.get("PATH", "")
                return True
            return False

    def _uv_cmd(self) -> str:
        """Return 'uv' or full path to uv.exe."""
        try:
            subprocess.run(["uv", "--version"], capture_output=True, timeout=5, check=True)
            return "uv"
        except Exception:
            uv_path = Path(os.environ.get("USERPROFILE", "")) / ".local" / "bin" / "uv.exe"
            if uv_path.exists():
                return str(uv_path)
            # After fresh install uv may be in LOCALAPPDATA
            local = Path(os.environ.get("LOCALAPPDATA", "")) / "uv" / "bin" / "uv.exe"
            if local.exists():
                return str(local)
            return "uv"

    # ---- Step 1b: sync app deps ----
    def _setup_app_deps(self):
        if not APP_DIR.exists():
            raise RuntimeError(
                f"App-Verzeichnis nicht gefunden: {APP_DIR}\n"
                "Bitte stellen Sie sicher, dass PraxisDoktorSetup.exe "
                "im selben Ordner wie der 'app'-Ordner liegt."
            )
        self._log("Installiere App-Abhängigkeiten (einmalig, ~2 Min.)...")
        uv = self._uv_cmd()
        result = subprocess.run(
            [uv, "sync"],
            cwd=str(APP_DIR),
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"uv sync fehlgeschlagen:\n{result.stderr}")
        self._log("  Abhängigkeiten installiert.")

    # ---- Step 2: Ollama ----
    def _setup_ollama(self):
        self._set_step("step_ollama", "active")
        self._log("Prüfe Ollama...")

        if self._ollama_installed():
            self._log("  Ollama ist bereits installiert.")
            self._set_step("step_ollama", "done")
            return

        self._log("  Ollama nicht gefunden.")

        if OLLAMA_INSTALLER.exists():
            self._log("  Starte OllamaSetup.exe ...")
        else:
            self._log("  Lade OllamaSetup.exe herunter ...")
            self._download_with_progress(OLLAMA_URL, OLLAMA_INSTALLER)

        self._log("  Bitte den Ollama-Installer abschließen...")
        result = subprocess.run([str(OLLAMA_INSTALLER)], check=False)
        if result.returncode != 0:
            raise RuntimeError("Ollama-Installation fehlgeschlagen oder abgebrochen.")

        if not self._ollama_installed():
            raise RuntimeError("Ollama nicht gefunden nach Installation. Bitte manuell installieren.")

        self._log("  Ollama erfolgreich installiert.")
        self._set_step("step_ollama", "done")

    def _ollama_installed(self) -> bool:
        try:
            r = subprocess.run(["ollama", "--version"], capture_output=True, timeout=10)
            return r.returncode == 0
        except Exception:
            return False

    def _download_with_progress(self, url: str, dest: Path):
        def progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                pct = min(100, int(downloaded * 100 / total_size))
                mb = downloaded / 1024 / 1024
                total_mb = total_size / 1024 / 1024
                self.root.after(0, lambda p=pct, m=mb, t=total_mb: self.btn.configure(
                    text=f"Herunterladen... {p}%  ({m:.0f} / {t:.0f} MB)"
                ))
        urllib.request.urlretrieve(url, dest, reporthook=progress)
        self.root.after(0, lambda: self.btn.configure(text="Starte Setup...", state="disabled"))

    # ---- Step 3: Model ----
    def _setup_model(self):
        self._set_step("step_model", "active")
        self._log("Prüfe Modell llama3.1:8b ...")

        if self._model_available():
            self._log("  Modell bereits vorhanden.")
            self._set_step("step_model", "done")
            return

        self._log("  Lade llama3.1:8b herunter (ca. 4.7 GB)...")
        self._log("  Das kann einige Minuten dauern.")

        process = subprocess.Popen(
            ["ollama", "pull", "llama3.1:8b"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        for line in process.stdout:
            line = line.strip()
            if line:
                self._log("  " + line)

        process.wait()
        if process.returncode != 0:
            raise RuntimeError("Modell-Download fehlgeschlagen.")

        self._log("  Modell erfolgreich heruntergeladen.")
        self._set_step("step_model", "done")

    def _model_available(self) -> bool:
        try:
            r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=15)
            return "llama3.1:8b" in r.stdout
        except Exception:
            return False

    # ---- Step 4: Launch app ----
    def _launch_app(self):
        self._set_step("step_app", "active")
        self._log("Starte PraxisDoktor...")

        uv = self._uv_cmd()
        subprocess.Popen(
            [uv, "run", "python", "main.py"],
            cwd=str(APP_DIR),
        )

        import time
        time.sleep(3)
        webbrowser.open("http://localhost:8080")

        self._log("\nPraxisDoktor läuft!")
        self._log("Browser wurde geöffnet: http://localhost:8080")
        self._log("\nDieses Fenster kann geschlossen werden.")
        self._set_step("step_app", "done")

        self.root.after(0, lambda: self.btn.configure(
            text="Fertig — Browser öffnen",
            state="normal",
            bg=GREEN_DARK,
            cursor="hand2",
            command=lambda: webbrowser.open("http://localhost:8080"),
        ))

    def _set_failure(self):
        self.root.after(0, lambda: self.btn.configure(
            text="Fehler — Bitte Entwickler kontaktieren",
            state="normal",
            bg=RED,
            cursor="hand2",
        ))


def main():
    root = tk.Tk()
    SetupApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
