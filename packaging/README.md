# Optional standalone text CLI

Build from a clean Python environment. The executable runs text cleanup, rule commands, Code Mode and other text-only CLI tools. Use the full Python installation described in the [quick start](../README.md#quick-start) for microphone recording, inference, the tray, and the dashboard.

```powershell
python -m pip install -e . pyinstaller
python -m PyInstaller packaging/swarscribe.spec --noconfirm
.\dist\swarscribe.exe clean "um hello world"
```

The Windows artifact is unsigned. If Windows Application Control blocks it, use the Python entry point or an approved environment. The optional Inno Setup definition installs the text CLI; it does not install Python speech dependencies or model weights. On Linux, use `python3 -m PyInstaller packaging/swarscribe.spec --noconfirm` from the project directory.
