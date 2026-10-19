"""Edit this file, then run: python tools/run_sketch.py"""


def setup(robot):
    """Called at startup and again after the robot falls and resets."""
    robot.stop()


def loop(robot):
    """Called every simulation step (currently every 2 milliseconds)."""
    robot.drive(forward=0.20, left=0.0, turn=0.45)
