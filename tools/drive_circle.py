#!/usr/bin/env python3
"""Drive the UGOT mecanum model around a commanded circle.

The MJCF exposes normalized torque controls, so this script closes a PI loop
around the four wheel-joint velocities. It is a simulation controller, not a
hardware controller for the physical UGOT.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time

import mujoco


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "model" / "ugot_mecanum.xml"
CONFIG_PATH = ROOT / "config" / "ugot_mecanum.json"
WHEELS = ("front_left", "front_right", "rear_left", "rear_right")


def wheel_targets(speed: float, radius: float, half_span: float, wheel_radius: float,
                  direction: str = "left") -> tuple[float, float, float, float]:
    """Return FL, FR, RL, RR wheel rates in model joint coordinates (rad/s)."""
    if speed <= 0:
        raise ValueError("speed must be positive")
    if radius <= half_span:
        raise ValueError(f"radius must exceed L+W ({half_span:.3f} m)")
    turn_sign = 1.0 if direction == "left" else -1.0
    yaw_rate = turn_sign * speed / radius
    conventional = (
        (speed - half_span * yaw_rate) / wheel_radius,
        (speed + half_span * yaw_rate) / wheel_radius,
        (speed - half_span * yaw_rate) / wheel_radius,
        (speed + half_span * yaw_rate) / wheel_radius,
    )
    # The generated model's +Y wheel axes and roller handedness map positive
    # wheel velocity to the documented +X chassis-forward direction.
    return conventional


class WheelSpeedPI:
    def __init__(self, kp: float = 0.11, ki: float = 0.55, integral_limit: float = 1.0):
        self.kp = kp
        self.ki = ki
        self.integral_limit = integral_limit
        self.integral = [0.0] * 4

    def update(self, targets, measured, dt):
        controls = []
        for i, (target, actual) in enumerate(zip(targets, measured)):
            error = target - actual
            self.integral[i] = max(-self.integral_limit, min(self.integral_limit,
                                                              self.integral[i] + error * dt))
            command = self.kp * error + self.ki * self.integral[i]
            controls.append(max(-1.0, min(1.0, command)))
        return controls


def yaw_from_quaternion(qw, qx, qy, qz):
    return math.atan2(2.0 * (qw*qz + qx*qy), 1.0 - 2.0 * (qy*qy + qz*qz))


def run(args):
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    dims = {key: datum["value"] for key, datum in config["dimensions"].items()}
    half_span = (dims["wheelbase_m"] + dims["track_width_m"]) / 2.0
    targets = wheel_targets(args.speed, args.radius, half_span,
                            dims["wheel_radius_m"], args.direction)

    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    dof_addresses = [model.jnt_dofadr[mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_JOINT, f"{name}_joint")] for name in WHEELS]
    controller = WheelSpeedPI(args.kp, args.ki)

    viewer = None
    if not args.headless:
        from mujoco import viewer as mj_viewer
        viewer = mj_viewer.launch_passive(model, data)
        viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        viewer.cam.trackbodyid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
        viewer.cam.distance = 0.85
        viewer.cam.azimuth = 135.0
        viewer.cam.elevation = -38.0

    start_wall = time.perf_counter()
    try:
        while data.time < args.duration and (viewer is None or viewer.is_running()):
            step_wall = time.perf_counter()
            measured = [data.qvel[address] for address in dof_addresses]
            data.ctrl[:] = controller.update(targets, measured, model.opt.timestep)
            mujoco.mj_step(model, data)
            if viewer is not None:
                viewer.sync()
                remaining = model.opt.timestep - (time.perf_counter() - step_wall)
                if remaining > 0:
                    time.sleep(remaining)
    finally:
        if viewer is not None:
            viewer.close()

    yaw = yaw_from_quaternion(*data.qpos[3:7])
    result = {
        "target_wheel_rad_s": dict(zip(WHEELS, targets)),
        "final_position_m": {"x": float(data.qpos[0]), "y": float(data.qpos[1]), "z": float(data.qpos[2])},
        "final_yaw_rad": yaw,
        "simulated_seconds": float(data.time),
        "wall_seconds": time.perf_counter() - start_wall,
    }
    print(json.dumps(result, indent=2))
    return result


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radius", type=float, default=0.45, help="centre-path radius in metres")
    parser.add_argument("--speed", type=float, default=0.20, help="forward chassis speed in m/s")
    parser.add_argument("--direction", choices=("left", "right"), default="left")
    parser.add_argument("--duration", type=float, default=12.0, help="simulation duration in seconds")
    parser.add_argument("--kp", type=float, default=0.11, help="wheel-speed proportional gain")
    parser.add_argument("--ki", type=float, default=0.55, help="wheel-speed integral gain")
    parser.add_argument("--headless", action="store_true", help="run without opening the viewer")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
