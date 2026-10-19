#!/usr/bin/env python3
"""MuJoCo-style Python viewer with an editable Sketch sidebar section."""
from __future__ import annotations

import importlib.util
import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import mujoco
from PIL import Image, ImageTk

from drive_circle import WheelSpeedPI, WHEELS
from run_sketch import Robot

ROOT = Path(__file__).resolve().parents[1]
SKETCH = ROOT / "sketches" / "user_sketch.py"
MODEL = ROOT / "model" / "ugot_mecanum.xml"
CONFIG = ROOT / "config" / "ugot_mecanum.json"


def import_sketch():
    spec = importlib.util.spec_from_file_location("ugot_sidebar_sketch", SKETCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "loop", None)):
        raise TypeError("Sketch must define loop(robot)")
    return module


class CollapsibleSection(tk.Frame):
    def __init__(self, parent, title, content_builder=None, initially_open=False):
        super().__init__(parent, bg="#353535")
        self.open = initially_open
        self.content = tk.Frame(self, bg="#303030")
        self.button = tk.Button(
            self, text="", anchor="w", relief="flat", bd=0,
            bg="#6f2428", activebackground="#8b3035", fg="white",
            activeforeground="white", font=("Segoe UI", 10), command=self.toggle,
        )
        self.title = title
        self.button.pack(fill="x", pady=(0, 2))
        if content_builder:
            content_builder(self.content)
        self._refresh()

    def toggle(self):
        self.open = not self.open
        self._refresh()

    def _refresh(self):
        self.button.configure(text=f"{self.title}{'  ▲' if self.open else '  ◀'}")
        if self.open:
            self.content.pack(fill="x", pady=(0, 4))
        else:
            self.content.pack_forget()


class SidebarStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MuJoCo : UGOT mecanum car")
        self.geometry("1280x760")
        self.minsize(980, 620)
        self.configure(bg="#3b3b3b")
        self.running = True
        self.renderer = self.photo = None
        self._build_simulation()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(16, self.tick)

    def _build_simulation(self):
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        dim = {k: v["value"] for k, v in cfg["dimensions"].items()}
        self.reset_height = cfg["environment"]["fall_reset_height_m"]["value"]
        self.model = mujoco.MjModel.from_xml_path(str(MODEL))
        self.data = mujoco.MjData(self.model)
        mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
        self.robot = Robot(self.model, self.data, dim["wheel_radius_m"],
                           (dim["wheelbase_m"] + dim["track_width_m"]) / 2)
        self.controller = WheelSpeedPI()
        self.dofs = [self.model.jnt_dofadr[mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{name}_joint")] for name in WHEELS]
        self.sketch = import_sketch()
        setup = getattr(self.sketch, "setup", None)
        if callable(setup):
            setup(self.robot)
        self.renderer = mujoco.Renderer(self.model, height=480, width=640)
        self.camera = mujoco.MjvCamera()
        self.camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.camera.distance, self.camera.azimuth, self.camera.elevation = 1.0, 135.0, -38.0

    def _build_ui(self):
        self.sidebar = tk.Frame(self, width=270, bg="#353535")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.viewport = tk.Label(self, bg="#111820", fg="#aeb9c4", text="Loading simulation…")
        self.viewport.pack(side="left", fill="both", expand=True)

        for title in ("File", "Option"):
            CollapsibleSection(self.sidebar, title).pack(fill="x", padx=3, pady=1)
        CollapsibleSection(self.sidebar, "Simulation", self._simulation_controls, True).pack(fill="x", padx=3, pady=1)
        for title in ("Watch", "Physics", "Rendering", "Visualisation", "Group enable", "Logging"):
            CollapsibleSection(self.sidebar, title).pack(fill="x", padx=3, pady=1)
        CollapsibleSection(self.sidebar, "Sketch", self._sketch_controls).pack(fill="x", padx=3, pady=1)

    def _simulation_controls(self, parent):
        row = tk.Frame(parent, bg="#303030")
        row.pack(fill="x", padx=7, pady=7)
        self.pause_button = tk.Button(row, text="Pause", command=self.toggle_run, width=9)
        self.pause_button.pack(side="left", padx=(0, 5))
        tk.Button(row, text="Reset", command=self.reset_robot, width=9).pack(side="left")

    def _sketch_controls(self, parent):
        tk.Label(parent, text="setup(robot) / loop(robot)", anchor="w",
                 bg="#303030", fg="#d7d7d7", font=("Segoe UI", 9)).pack(fill="x", padx=7, pady=(6, 2))
        self.editor = tk.Text(parent, height=17, wrap="none", undo=True,
                              bg="#11171d", fg="#e6edf3", insertbackground="white",
                              font=("Cascadia Mono", 9), relief="flat", padx=7, pady=6)
        self.editor.pack(fill="x", padx=7)
        self.editor.insert("1.0", SKETCH.read_text(encoding="utf-8"))
        controls = tk.Frame(parent, bg="#303030")
        controls.pack(fill="x", padx=7, pady=7)
        tk.Button(controls, text="Save & rerun", bg="#257044", fg="white",
                  activebackground="#318c57", activeforeground="white",
                  command=self.save_and_rerun).pack(side="left", fill="x", expand=True)
        tk.Button(controls, text="Reload", command=self.reload_editor).pack(side="left", padx=(5, 0))
        self.sketch_status = tk.StringVar(value="Ready")
        tk.Label(parent, textvariable=self.sketch_status, anchor="w",
                 bg="#303030", fg="#aeb9c4", font=("Segoe UI", 8)).pack(fill="x", padx=7, pady=(0, 7))

    def toggle_run(self):
        self.running = not self.running
        self.pause_button.configure(text="Pause" if self.running else "Run")

    def reset_robot(self, automatic=False):
        if automatic:
            self.robot.reset_count += 1
        mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
        self.robot.stop()
        self.controller.reset()
        setup = getattr(self.sketch, "setup", None)
        if callable(setup):
            setup(self.robot)

    def reload_editor(self):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", SKETCH.read_text(encoding="utf-8"))
        self.sketch_status.set("Reloaded saved sketch")

    def save_and_rerun(self):
        source = self.editor.get("1.0", "end-1c").rstrip("\n") + "\n"
        try:
            compile(source, str(SKETCH), "exec")
            SKETCH.write_text(source, encoding="utf-8")
            self.sketch = import_sketch()
            self.reset_robot()
            self.running = True
            self.pause_button.configure(text="Pause")
            self.sketch_status.set("Saved, reloaded, and restarted")
        except Exception as error:
            self.sketch_status.set(f"Error: {error}")
            messagebox.showerror("Sketch error", str(error))

    def tick(self):
        try:
            if self.running:
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
            image.thumbnail((max(320, self.viewport.winfo_width()), max(240, self.viewport.winfo_height())), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image=image)
            self.viewport.configure(image=self.photo, text="")
        except Exception as error:
            self.running = False
            self.sketch_status.set(f"Runtime error: {error}")
        self.after(16, self.tick)

    def close(self):
        if self.renderer:
            self.renderer.close()
        self.destroy()


if __name__ == "__main__":
    SidebarStudio().mainloop()
