"""Local PyInstaller build script — run with: uv run python build.py"""
import subprocess
import sys

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--name", "PraxisDoktor",
    "--add-data", "static:static",
    "--add-data", "vocab_default.json:.",
    "main.py",
]

print("Building PraxisDoktor.exe ...")
result = subprocess.run(cmd)
if result.returncode == 0:
    print("\nBuild successful! Executable is at dist/PraxisDoktor (or dist/PraxisDoktor.exe on Windows)")
else:
    print("\nBuild failed.")
    sys.exit(result.returncode)
