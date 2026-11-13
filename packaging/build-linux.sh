#!/usr/bin/env bash
# Build the one-click Linux binary: dist/swarscribe
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pip install --user pyinstaller
python3 -m PyInstaller packaging/swarscribe.spec --noconfirm
echo "Built: dist/swarscribe"
./dist/swarscribe clean "um this is the installer smoke test"
