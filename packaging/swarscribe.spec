# PyInstaller spec: builds a single-file `swarscribe` executable.
# Build:  pyinstaller packaging/swarscribe.spec
# Standalone text CLI. Use the Python installation for speech and dashboard.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(ROOT, "packaging", "entry.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=[],
    datas=[(os.path.join(ROOT, "assets", "logo.png"), "assets")],
    hiddenimports=[],
    hookspath=[],
    excludes=["nemo", "torch", "faster_whisper", "ctranslate2", "av", "onnxruntime",
              "numpy", "fastapi", "uvicorn", "sounddevice", "pystray", "comtypes"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="swarscribe",
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon=os.path.join(ROOT, "assets", "logo.png"),
)
