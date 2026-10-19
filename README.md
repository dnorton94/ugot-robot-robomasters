# UGOT mecanum car digital twin

An engineering-grade **first-pass** model of the UBTECH UGOT mecanum-wheel car.
The repository is deliberately parameterised: published values are separated from
dimensions and inertial values that still need physical measurement.

## Included

- `model/ugot_mecanum.xml` — MuJoCo model with four driven wheels and nine
  passive 45-degree rollers per wheel.
- `model/ugot_mecanum.usda` — OpenUSD/UsdPhysics articulation for Isaac Sim.
- `config/ugot_mecanum.json` — the single source of dimensions and dynamics.
- `tools/generate.py` — regenerates both model files using only Python's
  standard library.
- `tools/smoke_test.py` — compiles the MJCF and performs a short dynamics test.
- `tests/test_structure.py` — dependency-free structural checks.
- `docs/PROVENANCE.md` — measured/published/estimated value ledger.
- `docs/CONTROL.md` — wheel ordering and mecanum inverse kinematics.

## Quick start

```powershell
python tools/generate.py
python -m unittest discover -s tests -v
python -m pip install mujoco
python tools/smoke_test.py
python -m mujoco.viewer --mjcf model/ugot_mecanum.xml
```

Run commands from this directory. The model uses metres, kilograms, seconds,
radians, and newtons.

## Model status

This is a functional simulation baseline, not yet a dimensional scan. UBTECH
publishes the motor envelope and performance but not the assembled mecanum
car's complete dimensions, mass distribution, wheel geometry, or CAD. Every
unverified value is marked `estimated` in the configuration and provenance
ledger. Replace those numbers with caliper/scale measurements, regenerate, and
rerun the tests before using the model for controller transfer or safety work.

The MuJoCo file is generated and structurally tested here. The USD file follows
UsdPhysics conventions but must receive its final acceptance test in the target
Isaac Sim version; Isaac Sim is not bundled with this deliverable.

## Calibration order

1. Wheel outer diameter, width, roller count, and roller angle.
2. Wheel-centre positions (wheelbase, track, and axle height).
3. Total mass and individual module masses.
4. Centre of mass using a two-scale or suspension test.
5. Wheel free speed and stall/continuous torque.
6. Roller friction and rolling resistance on the intended floor.

