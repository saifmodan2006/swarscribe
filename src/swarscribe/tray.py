"""Windows tray and native status window for the shared dictation worker."""

from __future__ import annotations

import socket
import sys
import threading
import time
import webbrowser
from queue import Empty, Queue

from .config import Config


def run_tray(config: Config, *, background: bool = False):  # pragma: no cover
    if sys.platform != "win32":
        raise RuntimeError("The SwarScribe tray is available on Windows.")
    try:
        import pystray
        from PIL import Image, ImageDraw

        from .desktop_window import create_window
    except ImportError as exc:
        raise RuntimeError("Install 'swarscribe[desktop]' to use the Windows tray.") from exc
    from .desktop import run_desktop

    shutdown = threading.Event()
    messages = Queue()
    status = "Starting…"
    image = Image.new("RGBA", (64, 64), "#292520")
    draw = ImageDraw.Draw(image)
    for x, height in ((14, 14), (24, 26), (34, 36), (44, 20)):
        draw.rounded_rectangle((x, 32 - height // 2, x + 6, 32 + height // 2),
                               radius=3, fill="#ffab85")
    server_lock = threading.Lock()
    dashboard_url = None
    dashboard_thread = None
    worker = None

    def report(message):
        messages.put(("status", message.replace("\n", " ")[:220]))

    def listen():
        try:
            run_desktop(config, shutdown=shutdown, on_status=report)
            if not shutdown.is_set():
                report("The hotkey listener stopped. Restart SwarScribe.")
        except Exception as exc:
            report(str(exc))

    def setup(tray_icon):
        nonlocal worker
        tray_icon.visible = True
        worker = threading.Thread(target=listen, daemon=True)
        worker.start()

    def serve():
        nonlocal dashboard_url
        try:
            import uvicorn
            from .api import app
        except ImportError:
            report("Install 'swarscribe[api]' to open the workspace.")
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
                    if shutdown.wait(0.05):
                        return
                if not server.started:
                    report("The local workspace could not start.")
                    return
                url = f"http://127.0.0.1:{port}/"
                with server_lock:
                    dashboard_url = url
                webbrowser.open(url)
                shutdown.wait()
            finally:
                with server_lock:
                    dashboard_url = None
                server.should_exit = True
                thread.join(timeout=3)

    def open_workspace():
        nonlocal dashboard_thread
        with server_lock:
            url = dashboard_url
            if url is None and (dashboard_thread is None or not dashboard_thread.is_alive()):
                dashboard_thread = threading.Thread(target=serve, daemon=True)
                dashboard_thread.start()
        if url:
            webbrowser.open(url)

    try:
        root, update_window = create_window(config.hotkey, config.toggle, open_workspace)
    except Exception as exc:
        raise RuntimeError("The desktop window could not start. Check the Python Tk installation.") from exc
    if background:
        root.withdraw()

    icon = pystray.Icon("swarscribe", image, "SwarScribe", pystray.Menu(
        pystray.MenuItem("Show SwarScribe", lambda *_: messages.put(("show", "")), default=True),
        pystray.MenuItem("Open workspace", lambda *_: open_workspace()),
        pystray.MenuItem(lambda _: status, None, enabled=False),
        pystray.MenuItem("Quit", lambda *_: messages.put(("quit", "")))))

    def poll():
        nonlocal status
        try:
            while True:
                event, value = messages.get_nowait()
                if event == "quit":
                    root.quit()
                    return
                if event == "show":
                    root.deiconify()
                    root.lift()
                if event == "status":
                    status = value
                    update_window(value)
                    icon.title = ("SwarScribe: " + value)[:63]
                    icon.update_menu()
        except Empty:
            root.after(100, poll)

    try:
        icon.run_detached(setup=setup)
        root.after(100, poll)
        root.mainloop()
    finally:
        shutdown.set()
        icon.stop()
        root.destroy()
        if worker:
            worker.join(timeout=2)
        if dashboard_thread:
            dashboard_thread.join(timeout=4)
