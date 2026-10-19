#!/usr/bin/env python3
"""Tabbed native sketch editor and embedded UGOT MuJoCo simulator."""
from __future__ import annotations

import importlib.util
import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import mujoco
from PIL import Image, ImageTk

from drive_circle import WheelSpeedPI, WHEELS
from run_sketch import Robot

ROOT = Path(__file__).resolve().parents[1]
SKETCH = ROOT / "sketches" / "user_sketch.py"
MODEL = ROOT / "model" / "ugot_mecanum.xml"
CONFIG = ROOT / "config" / "ugot_mecanum.json"


def load_sketch(path: Path):
    spec = importlib.util.spec_from_file_location("ugot_studio_sketch", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load sketch: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "loop", None)):
        raise TypeError("Sketch must define loop(robot)")
    return module


class SketchStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UGOT Sketch Studio")
        self.geometry("1100x800")
        self.minsize(820, 600)
        self.configure(bg="#151a20")
        self.dirty = self.running = False
        self.model = self.data = self.robot = self.controller = None
        self.renderer = self.camera = self.sketch = None
        self.dofs, self.photo = [], None
        self.reset_height = -0.30
        self._build_ui()
        self.reload_sketch()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(16, self._simulation_tick)

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Toolbar.TFrame", background="#202832")
        style.configure("Studio.TButton", font=("Segoe UI", 10), padding=(14, 8))
        style.configure("Run.TButton", font=("Segoe UI Semibold", 10), padding=(18, 8), foreground="white", background="#138a52")
        style.map("Run.TButton", background=[("active", "#18a764")])
        style.configure("Stop.TButton", font=("Segoe UI Semibold", 10), padding=(18, 8), foreground="white", background="#a53a43")
        style.map("Stop.TButton", background=[("active", "#c44752")])
        style.configure("Studio.TNotebook", background="#151a20", borderwidth=0)
        style.configure("Studio.TNotebook.Tab", font=("Segoe UI Semibold", 10), padding=(18, 9))

        toolbar = ttk.Frame(self, style="Toolbar.TFrame", padding=10)
        toolbar.pack(fill="x")
        for text, command, style_name in (
            ("Save", self.save_sketch, "Studio.TButton"),
            ("Save & Run", self.save_and_run, "Run.TButton"),
            ("Stop", self.stop_simulation, "Stop.TButton"),
            ("Reset Robot", self.reset_robot, "Studio.TButton"),
            ("Reload", self.confirm_reload, "Studio.TButton"),
        ):
            ttk.Button(toolbar, text=text, command=command, style=style_name).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Insert circle example", command=self.insert_circle, style="Studio.TButton").pack(side="right")

        self.tabs = ttk.Notebook(self, style="Studio.TNotebook")
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.editor_tab, self.simulator_tab = tk.Frame(self.tabs, bg="#151a20"), tk.Frame(self.tabs, bg="#090d11")
        self.tabs.add(self.editor_tab, text="Sketch")
        self.tabs.add(self.simulator_tab, text="Simulator")

        header = tk.Frame(self.editor_tab, bg="#151a20")
        header.pack(fill="x", padx=6, pady=(8, 6))
        tk.Label(header, text="sketches/user_sketch.py", bg="#151a20", fg="#dce7f2", font=("Segoe UI Semibold", 12)).pack(side="left")
        tk.Label(header, text="Edit setup() and loop(), then choose Save & Run", bg="#151a20", fg="#8fa2b5", font=("Segoe UI", 10)).pack(side="right")
        editor_frame = tk.Frame(self.editor_tab, bg="#151a20")
        editor_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        scrollbar = ttk.Scrollbar(editor_frame)
        scrollbar.pack(side="right", fill="y")
        self.editor = tk.Text(editor_frame, undo=True, wrap="none", yscrollcommand=scrollbar.set, bg="#0e1318", fg="#e2e8ef", insertbackground="#f0f4f8", selectbackground="#245c85", relief="flat", padx=16, pady=14, font=("Cascadia Mono", 12), tabs=(32,))
        self.editor.pack(fill="both", expand=True)
        scrollbar.configure(command=self.editor.yview)
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<Control-s>", lambda _event: self.save_sketch())

        self.sim_image = tk.Label(self.simulator_tab, bg="#090d11", text="Choose Save & Run to start the embedded simulator", fg="#8fa2b5", font=("Segoe UI", 13))
        self.sim_image.pack(fill="both", expand=True)
        self.sim_info = tk.StringVar(value="Stopped")
        tk.Label(self.simulator_tab, textvariable=self.sim_info, anchor="w", bg="#151a20", fg="#b8c6d4", font=("Cascadia Mono", 10), padx=12, pady=7).pack(fill="x")
        self.status = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status, anchor="w", bg="#202832", fg="#b8c6d4", font=("Segoe UI", 10), padx=14, pady=9).pack(fill="x")

    def _on_modified(self, _event=None):
        if self.editor.edit_modified():
            self.dirty = True
            self.title("UGOT Sketch Studio *")
            self.editor.edit_modified(False)

    def reload_sketch(self):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", SKETCH.read_text(encoding="utf-8"))
        self.editor.edit_modified(False)
        self.dirty = False
        self.title("UGOT Sketch Studio")
        self.status.set(f"Loaded {SKETCH.name}")

    def confirm_reload(self):
        if not self.dirty or messagebox.askyesno("Discard changes?", "Discard editor changes?"):
            self.reload_sketch()

    def save_sketch(self):
        source = self.editor.get("1.0", "end-1c").rstrip("\n") + "\n"
        try:
            compile(source, str(SKETCH), "exec")
        except SyntaxError as error:
            self.status.set(f"Syntax error on line {error.lineno}: {error.msg}")
            messagebox.showerror("Sketch syntax error", f"Line {error.lineno}: {error.msg}")
            return False
        SKETCH.write_text(source, encoding="utf-8")
        self.dirty = False
        self.title("UGOT Sketch Studio")
        self.status.set("Saved successfully")
        return True

    def save_and_run(self):
        if not self.save_sketch():
            return
        try:
            self.stop_simulation(update_status=False)
            self.sketch = load_sketch(SKETCH)
            config = json.loads(CONFIG.read_text(encoding="utf-8"))
            dim = {key: datum["value"] for key, datum in config["dimensions"].items()}
            self.reset_height = config["environment"]["fall_reset_height_m"]["value"]
            self.model, self.data = mujoco.MjModel.from_xml_path(str(MODEL)), None
            self.data = mujoco.MjData(self.model)
            mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
            self.robot = Robot(self.model, self.data, dim["wheel_radius_m"], (dim["wheelbase_m"] + dim["track_width_m"]) / 2)
            self.controller = WheelSpeedPI()
            self.dofs = [self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{name}_joint")] for name in WHEELS]
            # MuJoCo's default offscreen framebuffer is 640x480. Render at that
            # native size, then scale the frame to the tab without another window.
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)
            self.camera = mujoco.MjvCamera()
            self.camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            self.camera.distance, self.camera.azimuth, self.camera.elevation = 1.0, 135.0, -42.0
            setup = getattr(self.sketch, "setup", None)
            if callable(setup):
                setup(self.robot)
            self.running = True
            self.tabs.select(self.simulator_tab)
            self.status.set("Running in the embedded Simulator tab")
        except Exception as error:
            self.stop_simulation(update_status=False)
            self.status.set(f"Could not start: {error}")
            messagebox.showerror("Simulation error", str(error))

    def reset_robot(self, automatic=False):
        if self.data is None:
            self.status.set("Start the simulator before resetting")
            return
        if automatic:
            self.robot.reset_count += 1
        mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
        self.robot.boot_time = 0.0
        self.robot.stop()
        self.controller.reset()
        setup = getattr(self.sketch, "setup", None)
        if callable(setup):
            setup(self.robot)
        self.status.set("Robot automatically reset after falling" if automatic else "Robot reset")

    def stop_simulation(self, update_status=True):
        self.running = False
        if self.renderer is not None:
            self.renderer.close()
        self.renderer = self.model = self.data = self.robot = self.controller = None
        self.photo = None
        self.sim_image.configure(image="", text="Choose Save & Run to start the embedded simulator")
        self.sim_info.set("Stopped")
        if update_status:
            self.status.set("Simulation stopped")

    def _simulation_tick(self):
        if self.running:
            try:
                for _ in range(8):
                    self.sketch.loop(self.robot)
                    measured = [self.data.qvel[address] for address in self.dofs]
                    self.data.ctrl[:] = self.controller.update(self.robot.targets, measured, self.model.opt.timestep)
                    mujoco.mj_step(self.model, self.data)
                    if self.data.qpos[2] < self.reset_height:
                        self.reset_robot(automatic=True)
                self.camera.lookat[:] = self.data.qpos[:3]
                self.renderer.update_scene(self.data, camera=self.camera)
                image = Image.fromarray(self.renderer.render())
                image.thumbnail((max(320, self.sim_image.winfo_width()), max(240, self.sim_image.winfo_height())), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(image=image)
                self.sim_image.configure(image=self.photo, text="")
                x, y, z = self.robot.pose
                self.sim_info.set(f"time {self.data.time:7.2f} s   pose ({x:+.2f}, {y:+.2f}, {z:+.2f}) m   fall resets {self.robot.reset_count}")
            except Exception as error:
                self.stop_simulation(update_status=False)
                self.status.set(f"Simulation stopped: {error}")
                messagebox.showerror("Sketch runtime error", str(error))
        self.after(16, self._simulation_tick)

    def insert_circle(self):
        example = '''"""UGOT circle sketch."""\n\n\ndef setup(robot):\n    robot.stop()\n\n\ndef loop(robot):\n    robot.drive(forward=0.20, left=0.0, turn=0.45)\n'''
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", example)
        self.dirty = True
        self.title("UGOT Sketch Studio *")
        self.tabs.select(self.editor_tab)
        self.status.set("Circle example inserted · choose Save & Run")

    def close(self):
        if self.dirty and not messagebox.askyesno("Unsaved changes", "Close without saving changes?"):
            return
        self.stop_simulation(update_status=False)
        self.destroy()


if __name__ == "__main__":
    SketchStudio().mainloop()
