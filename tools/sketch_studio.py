#!/usr/bin/env python3
"""Native editor and run controls for an UGOT simulation sketch."""
from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


ROOT = Path(__file__).resolve().parents[1]
SKETCH = ROOT / "sketches" / "user_sketch.py"
RUNNER = ROOT / "tools" / "run_sketch.py"


class SketchStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UGOT Sketch Studio")
        self.geometry("1000x720")
        self.minsize(720, 500)
        self.configure(bg="#151a20")
        self.process: subprocess.Popen | None = None
        self.dirty = False
        self._build_ui()
        self.reload_sketch()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(300, self._poll_process)

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Toolbar.TFrame", background="#202832")
        style.configure("Studio.TButton", font=("Segoe UI", 10), padding=(14, 8))
        style.configure("Run.TButton", font=("Segoe UI Semibold", 10), padding=(18, 8),
                        foreground="white", background="#138a52")
        style.map("Run.TButton", background=[("active", "#18a764")])
        style.configure("Stop.TButton", font=("Segoe UI Semibold", 10), padding=(18, 8),
                        foreground="white", background="#a53a43")
        style.map("Stop.TButton", background=[("active", "#c44752")])

        toolbar = ttk.Frame(self, style="Toolbar.TFrame", padding=10)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Save", command=self.save_sketch,
                   style="Studio.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Save & Run", command=self.save_and_run,
                   style="Run.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Stop", command=self.stop_simulation,
                   style="Stop.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Reload", command=self.confirm_reload,
                   style="Studio.TButton").pack(side="left")
        ttk.Button(toolbar, text="Insert circle example", command=self.insert_circle,
                   style="Studio.TButton").pack(side="right")

        header = tk.Frame(self, bg="#151a20")
        header.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(header, text="sketches/user_sketch.py", bg="#151a20", fg="#dce7f2",
                 font=("Segoe UI Semibold", 12)).pack(side="left")
        tk.Label(header, text="Edit setup() and loop(), then choose Save & Run",
                 bg="#151a20", fg="#8fa2b5", font=("Segoe UI", 10)).pack(side="right")

        editor_frame = tk.Frame(self, bg="#151a20")
        editor_frame.pack(fill="both", expand=True, padx=16)
        scrollbar = ttk.Scrollbar(editor_frame)
        scrollbar.pack(side="right", fill="y")
        self.editor = tk.Text(editor_frame, undo=True, wrap="none", yscrollcommand=scrollbar.set,
                              bg="#0e1318", fg="#e2e8ef", insertbackground="#f0f4f8",
                              selectbackground="#245c85", relief="flat", padx=16, pady=14,
                              font=("Cascadia Mono", 12), tabs=(32,))
        self.editor.pack(fill="both", expand=True)
        scrollbar.configure(command=self.editor.yview)
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<Control-s>", lambda _event: self.save_sketch())

        footer = tk.Frame(self, bg="#202832", height=38)
        footer.pack(fill="x", pady=(12, 0))
        self.status = tk.StringVar(value="Ready")
        tk.Label(footer, textvariable=self.status, anchor="w", bg="#202832", fg="#b8c6d4",
                 font=("Segoe UI", 10), padx=14, pady=9).pack(fill="x")

    def _on_modified(self, _event=None):
        if self.editor.edit_modified():
            self.dirty = True
            self._update_title()
            self.editor.edit_modified(False)

    def _update_title(self):
        self.title(f"UGOT Sketch Studio{' *' if self.dirty else ''}")

    def reload_sketch(self):
        text = SKETCH.read_text(encoding="utf-8")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_modified(False)
        self.dirty = False
        self._update_title()
        self.status.set(f"Loaded {SKETCH.name}")

    def confirm_reload(self):
        if self.dirty and not messagebox.askyesno("Discard changes?", "Reload the saved sketch and discard editor changes?"):
            return
        self.reload_sketch()

    def save_sketch(self):
        source = self.editor.get("1.0", "end-1c") + "\n"
        try:
            compile(source, str(SKETCH), "exec")
        except SyntaxError as error:
            self.status.set(f"Syntax error on line {error.lineno}: {error.msg}")
            messagebox.showerror("Sketch syntax error", f"Line {error.lineno}: {error.msg}")
            return False
        SKETCH.write_text(source, encoding="utf-8")
        self.dirty = False
        self._update_title()
        self.status.set("Saved successfully")
        return True

    def save_and_run(self):
        if not self.save_sketch():
            return
        self.stop_simulation(update_status=False)
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self.process = subprocess.Popen(
            [sys.executable, str(RUNNER), str(SKETCH)], cwd=str(ROOT),
            creationflags=flags,
        )
        self.status.set(f"Simulation running · process {self.process.pid}")

    def stop_simulation(self, update_status=True):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            if update_status:
                self.status.set("Simulation stopped")
        elif update_status:
            self.status.set("No simulation is running")
        self.process = None

    def _poll_process(self):
        if self.process is not None and self.process.poll() is not None:
            code = self.process.returncode
            self.process = None
            self.status.set("Simulation closed" if code == 0 else f"Simulation exited with code {code}")
        self.after(300, self._poll_process)

    def insert_circle(self):
        example = '''"""UGOT circle sketch."""\n\n\ndef setup(robot):\n    robot.stop()\n\n\ndef loop(robot):\n    robot.drive(forward=0.20, left=0.0, turn=0.45)\n'''
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", example)
        self.dirty = True
        self._update_title()
        self.status.set("Circle example inserted · choose Save & Run")

    def close(self):
        if self.dirty and not messagebox.askyesno("Unsaved changes", "Close without saving your sketch changes?"):
            return
        self.stop_simulation(update_status=False)
        self.destroy()


if __name__ == "__main__":
    SketchStudio().mainloop()
