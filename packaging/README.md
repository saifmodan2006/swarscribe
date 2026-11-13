# One-click installers

SwarScribe should not need a Python course to install. These packaging
files build a single-file executable of the CLI and desktop core:

- **Linux:** `./packaging/build-linux.sh` produces `dist/swarscribe`.
  Verified: the Linux binary is built and smoke-tested in this repo's
  development environment.
- **Windows:** `packaging\build-windows.bat` produces
  `dist\swarscribe.exe`; compile `packaging/swarscribe.iss` with
  Inno Setup 6 to get a proper `SwarScribe-Setup.exe` with Start Menu
  entries. Build it on any Windows machine in about two minutes.
- **macOS:** the same PyInstaller spec works
  (`python3 -m PyInstaller packaging/swarscribe.spec`); wrap the result
  in a .app/dmg with your usual tooling. Not yet code-signed, so
  Gatekeeper will ask once.

Speech models are not bundled (they are hundreds of MB); the app
downloads the chosen model on first use, exactly like the pip install.
Everything else, cleanup, dictionary, Code Mode, bots and the API,
travels inside the single file.
