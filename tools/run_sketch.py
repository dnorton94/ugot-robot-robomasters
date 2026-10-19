#!/usr/bin/env python3
"""Run an Arduino-style Python sketch against the UGOT MuJoCo model."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import time

import mujoco

from drive_circle import WheelSpeedPI, WHEELS

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "model" / "ugot_mecanum.xml"
CONFIG_PATH = ROOT / "config" / "ugot_mecanum.json"


def load_sketch(path: Path):
    spec = importlib.util.spec_from_file_location("ugot_user_sketch", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load sketch: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "loop", None)):
        raise TypeError("Sketch must define loop(robot)")
    return module


class Robot:
    """Small user-facing API inspired by an Arduino sketch runtime."""
    def __init__(self, model, data, wheel_radius, half_span):
        self.model, self.data = model, data
        self.wheel_radius, self.half_span = wheel_radius, half_span
        self.targets = [0.0] * 4
        self.boot_time = 0.0
        self.reset_count = 0

    def millis(self):
        return int((self.data.time - self.boot_time) * 1000)

    def drive(self, forward=0.0, left=0.0, turn=0.0):
        """Command chassis velocity in m/s, m/s, and rad/s."""
        k, r = self.half_span, self.wheel_radius
        self.targets[:] = [
            (forward - left - k*turn) / r,
            (forward + left + k*turn) / r,
            (forward + left - k*turn) / r,
            (forward - left + k*turn) / r,
        ]

    def set_wheels(self, front_left, front_right, rear_left, rear_right):
        self.targets[:] = [front_left, front_right, rear_left, rear_right]

    def stop(self):
        self.targets[:] = [0.0] * 4

    @property
    def pose(self):
        return tuple(float(value) for value in self.data.qpos[:3])


def run(args):
    sketch_path = Path(args.sketch).resolve()
    sketch = load_sketch(sketch_path)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    dim = {key: datum["value"] for key, datum in config["dimensions"].items()}
    reset_height = config["environment"]["fall_reset_height_m"]["value"]
    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    robot = Robot(model, data, dim["wheel_radius_m"],
                  (dim["wheelbase_m"] + dim["track_width_m"]) / 2)
    controller = WheelSpeedPI(args.kp, args.ki)
    dofs = [model.jnt_dofadr[mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_JOINT, f"{name}_joint")] for name in WHEELS]
    viewer = None
    if not args.headless:
        from mujoco import viewer as mj_viewer
        viewer = mj_viewer.launch_passive(model, data)
        viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        viewer.cam.trackbodyid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
        viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 1.0, 135.0, -42.0
    setup = getattr(sketch, "setup", None)
    if callable(setup):
        setup(robot)
    elapsed_sim = 0.0
    try:
        while (args.duration <= 0 or elapsed_sim < args.duration) and (viewer is None or viewer.is_running()):
            wall_start = time.perf_counter()
            sketch.loop(robot)
            measured = [data.qvel[address] for address in dofs]
            data.ctrl[:] = controller.update(robot.targets, measured, model.opt.timestep)
            mujoco.mj_step(model, data)
            elapsed_sim += model.opt.timestep
            if data.qpos[2] < reset_height:
                robot.reset_count += 1
                mujoco.mj_resetDataKeyframe(model, data, 0)
                robot.boot_time = 0.0
                robot.stop()
                controller.reset()
                if callable(setup):
                    setup(robot)
            if viewer is not None:
                viewer.sync()
                delay = model.opt.timestep - (time.perf_counter() - wall_start)
                if delay > 0:
                    time.sleep(delay)
    finally:
        if viewer is not None:
            viewer.close()
    print(json.dumps({"sketch": str(sketch_path), "fall_resets": robot.reset_count,
                      "final_pose_m": robot.pose}, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sketch", nargs="?", default=str(ROOT / "sketches" / "user_sketch.py"))
    parser.add_argument("--duration", type=float, default=0.0, help="seconds; 0 runs until viewer closes")
    parser.add_argument("--kp", type=float, default=0.11)
    parser.add_argument("--ki", type=float, default=0.55)
    parser.add_argument("--headless", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
