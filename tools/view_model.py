#!/usr/bin/env python3
"""Open the generated UGOT mecanum model in MuJoCo's interactive viewer."""
from pathlib import Path

import mujoco.viewer


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model" / "ugot_mecanum.xml"


if __name__ == "__main__":
    if not MODEL.is_file():
        raise SystemExit(f"Model not found: {MODEL}")
    mujoco.viewer.launch_from_path(str(MODEL))
