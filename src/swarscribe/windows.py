"""Windows foreground and UI Automation checks, plus Unicode SendInput."""

from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
from dataclasses import dataclass
from pathlib import Path

UIA_TEXT = 10014
KEYUP = 0x0002
UNICODE = 0x0004


class MouseInput(c.Structure):
    _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD),
                ("dwFlags", w.DWORD), ("time", w.DWORD), ("extra", c.c_size_t)]


class KeyboardInput(c.Structure):
    _fields_ = [("vk", w.WORD), ("scan", w.WORD), ("flags", w.DWORD),
                ("time", w.DWORD), ("extra", c.c_size_t)]


class HardwareInput(c.Structure):
    _fields_ = [("message", w.DWORD), ("low", w.WORD), ("high", w.WORD)]


class InputData(c.Union):
    _fields_ = [("mouse", MouseInput), ("key", KeyboardInput), ("hardware", HardwareInput)]


class Input(c.Structure):
    _fields_ = [("type", w.DWORD), ("data", InputData)]


@dataclass
class Target:
    hwnd: int
    app: str


def foreground() -> Target:
    user = c.windll.user32
    kernel = c.windll.kernel32
    user.GetForegroundWindow.restype = w.HWND
    hwnd = user.GetForegroundWindow()
    pid = w.DWORD()
    user.GetWindowThreadProcessId(w.HWND(hwnd), c.byref(pid))
    kernel.OpenProcess.restype = w.HANDLE
    process = kernel.OpenProcess(0x1000, False, pid.value)
    name = ""
    if process:
        try:
            buffer = c.create_unicode_buffer(32768)
            size = w.DWORD(len(buffer))
            if kernel.QueryFullProcessImageNameW(w.HANDLE(process), 0, buffer, c.byref(size)):
                name = Path(buffer.value).stem.lower()
        finally:
            kernel.CloseHandle(w.HANDLE(process))
    return Target(hwnd, name)


class Focus:
    def __enter__(self):
        import comtypes
        from comtypes.client import CreateObject, GetModule

        comtypes.CoInitialize()
        self._comtypes = comtypes
        try:
            self.module = GetModule("UIAutomationCore.dll")
            self.automation = CreateObject(self.module.CUIAutomation,
                                           interface=self.module.IUIAutomation)
            self.element = self.automation.GetFocusedElement()
            if self.element.CurrentIsPassword:
                raise RuntimeError("Dictation is disabled in password fields.")
            if not self.element.CurrentIsEnabled:
                raise RuntimeError("The focused control is disabled.")
            return self
        except BaseException:
            comtypes.CoUninitialize()
            raise

    def __exit__(self, *args):
        self.element = self.automation = None
        self._comtypes.CoUninitialize()

    def selection(self) -> str | None:
        try:
            pattern = self.element.GetCurrentPattern(UIA_TEXT)
            if not pattern:
                return None
            pattern = pattern.QueryInterface(self.module.IUIAutomationTextPattern)
            ranges = pattern.GetSelection()
            if not ranges or ranges.Length != 1:
                return None
            return ranges.GetElement(0).GetText(16001)
        except (self._comtypes.COMError, ValueError, AttributeError):
            return None

    def writable(self) -> bool:
        if self.element.CurrentControlType in {50004, 50030}:  # Edit, Document
            return self.element.CurrentIsKeyboardFocusable
        return False


def send_text(text: str, expected: Target, selection: str | None = None,
              editor_id: tuple | None = None) -> str:
    """Send Unicode key events only to the checked foreground editable control."""
    if not expected.hwnd or foreground().hwnd != expected.hwnd:
        return "Focus changed. Text was not sent."
    if not text or len(text) > 16000 or "\x00" in text:
        return "Text is empty or too large for direct insertion."
    with Focus() as focus:
        if editor_id is not None and tuple(focus.element.GetRuntimeId()) != editor_id:
            return "The focused editor changed. Text was not sent."
        if not focus.writable():
            return "Focused control does not expose a supported editor. Text was not sent."
        current = focus.selection()
        if selection is not None and current != selection:
            return "The selected text changed. Text was not sent."
        if selection is None and current != "":
            return "Clear the selection, or use Command Mode to replace selected text."
        if foreground().hwnd != expected.hwnd:
            return "Focus changed. Text was not sent."
        if any(c.windll.user32.GetAsyncKeyState(key) & 0x8000
               for key in (0x10, 0x11, 0x12, 0x5B, 0x5C)):
            return "Release Ctrl, Alt, Shift and Windows before inserting text."
        keys = []
        encoded = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-16-le")
        for i in range(0, len(encoded), 2):
            code = int.from_bytes(encoded[i:i + 2], "little")
            # Keep tabs and newlines as text: physical Tab and Enter can navigate or submit.
            for flag in (UNICODE, UNICODE | KEYUP):
                keys.append(Input(1, InputData(key=KeyboardInput(0, code, flag, 0, 0))))
        inputs = (Input * len(keys))(*keys)
        sent = c.windll.user32.SendInput(len(inputs), inputs, c.sizeof(Input))
        if sent == len(inputs):
            return "Text sent to the editor."
        if sent:
            return "Windows accepted only part of the input. Check the editor before retrying."
        return "Windows blocked input. Check the editor or its privilege level."
