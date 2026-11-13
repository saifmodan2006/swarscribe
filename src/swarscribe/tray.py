"""System tray app: SwarScribe living in the tray, hotkey in hand.

Requires the desktop extra (pystray, Pillow). The tray icon uses the
brand PNG from assets/. Menu: Dictate now, Open dashboard, Quit.
Dictation itself runs through desktop.run_desktop in a thread so the
tray stays responsive.
"""

from __future__ import annotations

import threading
from pathlib import Path


def run_tray(pipeline, backend, hotkey: str = "ctrl+win"):  # pragma: no cover
    try:
        import pystray
        from PIL import Image
    except ImportError as error:
        raise RuntimeError(
            "Tray app needs the desktop extra: "
            'pip install "swarscribe[desktop]"') from error

    icon_path = (Path(__file__).resolve().parent.parent.parent
                 / "assets" / "logo.png")
    image = Image.open(icon_path) if icon_path.exists() else None

    def on_dictate(icon, item):
        from .desktop import run_desktop
        threading.Thread(target=run_desktop,
                         args=(pipeline, backend),
                         kwargs={"hotkey": hotkey},
                         daemon=True).start()

    def on_dashboard(icon, item):
        import webbrowser

        import uvicorn
        server = threading.Thread(
            target=uvicorn.run, args=("swarscribe.api:app",),
            kwargs={"port": 8765, "log_level": "error"}, daemon=True)
        server.start()
        page = (Path(__file__).resolve().parent.parent.parent
                / "web" / "dashboard.html")
        webbrowser.open(page.as_uri() if page.exists()
                        else "http://127.0.0.1:8765/docs")

    def on_quit(icon, item):
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Dictate (hold hotkey)", on_dictate),
        pystray.MenuItem("Open dashboard", on_dashboard),
        pystray.MenuItem("Quit", on_quit))
    icon = pystray.Icon("swarscribe", image, "SwarScribe", menu)
    icon.run()
