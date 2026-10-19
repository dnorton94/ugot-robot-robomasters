# Arduino-style sketches

Edit `sketches/user_sketch.py`, then run:

```powershell
python tools/run_sketch.py
```

The sketch has two familiar entry points:

```python
def setup(robot):
    # Runs once at startup and after every fall/reset.
    pass

def loop(robot):
    # Runs every physics step.
    robot.drive(forward=0.20, left=0.0, turn=0.45)
```

## Robot API

- `robot.drive(forward, left, turn)` — chassis velocities in m/s, m/s, rad/s.
- `robot.set_wheels(fl, fr, rl, rr)` — direct wheel targets in rad/s.
- `robot.stop()` — command zero wheel speed.
- `robot.millis()` — milliseconds since startup or the last fall reset.
- `robot.pose` — current `(x, y, z)` position in metres.
- `robot.reset_count` — number of automatic fall resets.

This resembles the Arduino `setup()`/`loop()` workflow while remaining ordinary
Python. Saving does not hot-reload a running model; close and rerun it after an
edit. This API controls the simulation only and must not be connected directly
to hardware without a separate, safety-reviewed transport and motor layer.
