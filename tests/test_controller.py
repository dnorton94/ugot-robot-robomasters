import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from drive_circle import WheelSpeedPI, wheel_targets


class CircleControllerTests(unittest.TestCase):
    def test_left_circle_outer_wheels_are_faster(self):
        fl, fr, rl, rr = wheel_targets(0.2, 0.45, 0.18, 0.05, "left")
        self.assertAlmostEqual(fl, rl)
        self.assertAlmostEqual(fr, rr)
        self.assertGreater(abs(fr), abs(fl))

    def test_right_circle_outer_wheels_are_faster(self):
        fl, fr, rl, rr = wheel_targets(0.2, 0.45, 0.18, 0.05, "right")
        self.assertGreater(abs(fl), abs(fr))
        self.assertAlmostEqual(fl, rl)
        self.assertAlmostEqual(fr, rr)

    def test_impossible_radius_is_rejected(self):
        with self.assertRaises(ValueError):
            wheel_targets(0.2, 0.18, 0.18, 0.05)

    def test_pi_output_is_normalized(self):
        controller = WheelSpeedPI(kp=10.0, ki=10.0)
        output = controller.update([100.0] * 4, [0.0] * 4, 0.01)
        self.assertEqual(output, [1.0] * 4)


if __name__ == "__main__":
    unittest.main()
