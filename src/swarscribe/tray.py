"""Windows tray wrapper around the shared desktop worker."""

from __future__ import annotations

import socket
import threading
import time
import webbrowser

from .config import Config


def run_tray(config: Config):  # pragma: no cover -- interactive platform integration
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Install 'swarscribe[desktop]' for the tray.") from exc
    from .desktop import run_desktop

    shutdown = threading.Event()
    image = Image.new("RGBA", (64, 64), "#171b21")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((23, 8, 41, 38), radius=8, fill="#ff5a36")
    draw.arc((17, 16, 47, 46), 0, 180, fill="#faf5ec", width=4)
    draw.line((32, 46, 32, 56), fill="#faf5ec", width=4)
    status = "Starting…"
    server = None
    worker = None
    dashboard_thread = None

    def report(message):
        nonlocal status
        status = message.replace("\n", " ")[:100]
        icon.title = ("SwarScribe: " + status)[:63]
        icon.update_menu()

    def listen():
        try:
            run_desktop(config, shutdown=shutdown, on_status=report)
        except Exception as exc:
            report(str(exc))

    def setup(icon):
        nonlocal worker
        icon.visible = True
        worker = threading.Thread(target=listen, daemon=True)
        worker.start()

    def serve():
        nonlocal server
        try:
            import uvicorn
            from .api import app
        except ImportError:
            report("Install 'swarscribe[api]' to open the dashboard.")
            return
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(app, port=port, log_level="warning",
                                                   access_log=False, proxy_headers=False))
            thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
            thread.start()
            try:
                deadline = time.monotonic() + 10
                while not server.started and thread.is_alive() and time.monotonic() < deadline:
                    shutdown.wait(0.05)
                    if shutdown.is_set():
                        return
                if not server.started:
                    report("The local dashboard could not start.")
                    return
                webbrowser.open(f"http://127.0.0.1:{port}/")
                shutdown.wait()
            finally:
                server.should_exit = True
                thread.join(timeout=3)

    def dashboard(icon, item):
        nonlocal dashboard_thread
        if dashboard_thread and dashboard_thread.is_alive():
            if server and server.started:
                port = server.servers[0].sockets[0].getsockname()[1]
                webbrowser.open(f"http://127.0.0.1:{port}/")
            return
        dashboard_thread = threading.Thread(target=serve, daemon=True)
        dashboard_thread.start()

    def quit_tray(icon, item):
        shutdown.set()
        icon.stop()

    icon = pystray.Icon("swarscribe", image, "SwarScribe", pystray.Menu(
        pystray.MenuItem(lambda _: status, None, enabled=False),
        pystray.MenuItem("Open dashboard", dashboard),
        pystray.MenuItem("Quit", quit_tray)))
    try:
        icon.run(setup=setup)
    finally:
        shutdown.set()
        if worker:
            worker.join(timeout=2)
        if dashboard_thread:
            dashboard_thread.join(timeout=4)
