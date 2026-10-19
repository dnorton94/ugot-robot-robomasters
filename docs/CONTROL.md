# Control contract

## Frames

- Right-handed frame: +X forward, +Y left, +Z up.
- Wheel order: front-left (`FL`), front-right (`FR`), rear-left (`RL`),
  rear-right (`RR`).
- The four actuator controls are normalised torque commands in `[-1, 1]`.
  A magnitude of 1 maps to the published approximate maximum of 0.196133 N·m.

## Inverse kinematics

For desired chassis velocity `(vx, vy, wz)`, wheel radius `r`, half-wheelbase
`L`, and half-track `W`, the conventional mecanum wheel angular speeds are:

```text
FL = (vx - vy - (L + W) wz) / r
FR = (vx + vy + (L + W) wz) / r
RL = (vx + vy - (L + W) wz) / r
RR = (vx - vy + (L + W) wz) / r
```

The MJCF joint-axis orientation may require a global sign inversion when these
velocities are converted to motor torques. Verify signs on a lifted robot before
hardware use.

## Important limitation

The passive-roller model produces mecanum behaviour through actual contacts. It
is more realistic but more numerically demanding than a planar-force plugin.
Floor material, solver timestep, roller friction, and contact softness strongly
affect lateral motion. Calibrate those parameters against measured trajectories.

