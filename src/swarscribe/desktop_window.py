"""Native status window for the Windows tray process."""

from __future__ import annotations

from collections.abc import Callable


def create_window(hotkey: str, toggle: bool, open_workspace: Callable[[], None]):
    import tkinter as tk
    from tkinter import font

    paper, surface, ink = "#f7f4ed", "#fffdfa", "#231f1a"
    muted, accent, line = "#625b51", "#b5381c", "#ded7cb"
    root = tk.Tk()
    root.title("SwarScribe")
    root.configure(bg=paper)
    root.minsize(420, 395)
    root.geometry("540x425")
    root.protocol("WM_DELETE_WINDOW", root.withdraw)
    root.bind("<Escape>", lambda _: root.withdraw())
    font.nametofont("TkDefaultFont").configure(family="Segoe UI", size=10)

    layout = tk.Frame(root, background=paper)
    layout.pack(fill="both", expand=True, padx=24, pady=20)

    brand = tk.Frame(layout, background=paper)
    brand.pack(fill="x")
    mark = tk.Canvas(brand, width=34, height=34, bg="#292520", highlightthickness=0)
    mark.pack(side="left", padx=(0, 10))
    for x, height in ((9, 8), (14, 15), (19, 20), (24, 12)):
        mark.create_line(x, 17 - height / 2, x, 17 + height / 2, fill="#ffab85",
                         width=3, capstyle="round")
    tk.Label(brand, text="SwarScribe", font=("Segoe UI", 14, "bold"),
             fg=ink, bg=paper).pack(side="left")

    tk.Label(layout, text="Desktop dictation", font=("Georgia", 25),
             fg=ink, bg=paper).pack(anchor="w", pady=(20, 3))
    tk.Label(layout, text="Focus the editor where you want your text to appear.",
             fg=muted, bg=paper, justify="left", wraplength=370).pack(anchor="w")

    card = tk.Frame(layout, background=surface, highlightbackground=line,
                    highlightthickness=1)
    card.pack(fill="both", expand=True, pady=16)
    shortcut = "  +  ".join(part.strip().upper() for part in hotkey.split("+"))
    instruction = "Tap to start or stop" if toggle else "Hold to record"
    tk.Label(card, text=f"{instruction}    {shortcut}", font=("Segoe UI", 11, "bold"),
             fg=ink, bg=surface, wraplength=350, justify="left").pack(anchor="w", padx=14, pady=(10, 2))
    phase = tk.Label(card, text="Starting…", font=("Segoe UI", 10, "bold"), fg=accent, bg=surface)
    phase.pack(anchor="w", padx=14, pady=(4, 0))
    message = tk.Label(card, text="Connecting the tray listener.", fg=muted, bg=surface,
                       wraplength=350, justify="left")
    message.pack(anchor="w", padx=14, pady=(0, 10))

    actions = tk.Frame(layout, background=paper)
    actions.pack(fill="x")
    primary = tk.Button(actions, text="Open workspace", command=open_workspace,
                        fg="white", bg=accent, activeforeground="white",
                        activebackground="#923019", padx=12, pady=7, relief="flat")
    primary.pack(side="left")
    tk.Button(actions, text="Hide to tray", command=root.withdraw, fg=ink, bg=surface,
              activebackground="#eee3d6", padx=12, pady=7, relief="flat").pack(side="left", padx=8)
    tk.Label(layout, text="Esc cancels dictation. Use the tray menu to reopen this window.",
             fg=muted, bg=paper, justify="left", wraplength=370).pack(anchor="w", pady=(10, 0))

    def update(status: str) -> None:
        if status.startswith(("Recording ·", "Transcribing ·")):
            title, _, detail = status.partition(" · ")
        elif status.startswith("Ready:"):
            title, detail = "Ready", "Use the shortcut in your editor."
        else:
            title, detail = "Dictation status", status
        phase.configure(text=title)
        message.configure(text=detail[:220])

    return root, update
