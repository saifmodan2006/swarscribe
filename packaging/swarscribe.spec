# PyInstaller spec: builds a single-file `swarscribe` executable.
# Build:  pyinstaller packaging/swarscribe.spec
# The binary bundles the cleanup/CLI core. Speech models stay external
# (they are large); the app downloads them on first use as usual.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(ROOT, "packaging", "entry.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=[],
    datas=[(os.path.join(ROOT, "assets", "logo.png"), "assets")],
    hiddenimports=[],
    hookspath=[],
    excludes=["nemo", "torch", "faster_whisper", "ctranslate2"],
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
