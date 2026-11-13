@echo off
REM Build the one-click Windows binary: dist\swarscribe.exe
REM Optional: wrap it with Inno Setup using packaging\swarscribe.iss
cd /d %~dp0..
py -m pip install pyinstaller
py -m PyInstaller packaging\swarscribe.spec --noconfirm
echo Built: dist\swarscribe.exe
dist\swarscribe.exe clean "um this is the installer smoke test"
