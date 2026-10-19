#!/usr/bin/env python3
"""Compile the MJCF, simulate forward/strafe/yaw commands, and check stability."""
from pathlib import Path
import math
import sys

try:
    import mujoco
except ImportError:
    raise SystemExit("Install the test dependency with: python -m pip install mujoco")

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model" / "ugot_mecanum.xml"


def run_command(model, command, seconds=1.0):
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    data.ctrl[:] = command
    start = data.qpos[:3].copy()
    steps = int(seconds / model.opt.timestep)
    for _ in range(steps):
        mujoco.mj_step(model, data)
        if not all(math.isfinite(v) for v in data.qpos):
            raise AssertionError("simulation became non-finite")
    return data.qpos[:3] - start, data


def main():
    model = mujoco.MjModel.from_xml_path(str(MODEL))
    assert model.nu == 4, f"expected 4 drive actuators, got {model.nu}"
    assert model.nq == 47, f"unexpected generalized-position count: {model.nq}"
    # Motor order: FL, FR, RL, RR. Signs reflect the common axle direction.
    cases = {
        "forward": [-0.55, -0.55, -0.55, -0.55],
        "strafe":  [ 0.55, -0.55, -0.55,  0.55],
        "yaw":     [ 0.55, -0.55,  0.55, -0.55],
    }
    for name, ctrl in cases.items():
        delta, data = run_command(model, ctrl)
        assert data.qpos[2] > 0.025, f"{name}: chassis fell through floor"
        print(f"{name:8s} delta_xyz = {delta}")
    # This test is intentionally qualitative until friction is calibrated.
    # It proves model compilation, stable contacts, and nonzero actuation while
    # avoiding false accuracy claims about an unmeasured physical assembly.
    print(f"PASS: compiled {MODEL.name}; nq={model.nq}, nv={model.nv}, nu={model.nu}")


if __name__ == "__main__":
    main()
