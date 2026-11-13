@echo off
REM Build the one-click Windows binary: dist\swarscribe.exe
REM Optional: wrap it with Inno Setup using packaging\swarscribe.iss
cd /d %~dp0..
py -m pip install -e . pyinstaller pillow || exit /b 1
py -m PyInstaller packaging\swarscribe.spec --noconfirm || exit /b 1
echo Built: dist\swarscribe.exe
dist\swarscribe.exe clean "um this is the installer smoke test"
