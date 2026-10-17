import unittest

from main import MISSIONS
from physics import (CodeError, Obstacle, Settings, Target, flight_to,
                     motion_data, obstacle_hit_time, position, read_code)


class PhysicsTests(unittest.TestCase):
    def test_python_assignments_and_comments(self):
        self.assertEqual(read_code("# launch!\nspeed = 8\nup = 10.0\ngravity = 10"),
                         Settings(8, 10, 10))

    def test_unsafe_code_is_never_executed(self):
        for code in ("import os\nspeed=8\nup=10\ngravity=10",
                     "speed=__import__('os').system('echo bad')\nup=10\ngravity=10",
                     "speed=8\nup=10\ngravity=10\nprint('bad')"):
            with self.assertRaises(CodeError):
                read_code(code)

    def test_invalid_values(self):
        for code in ("speed=0\nup=10\ngravity=10",
                     "speed=8\nup=10\ngravity=0",
                     "speed=8\nup=10"):
            with self.assertRaises(CodeError):
                read_code(code)

    def test_ten_missions_are_solvable_and_start_unsolved(self):
        solutions = (
            Settings(8, 15, 10), Settings(12, 10, 10), Settings(12, 12.5, 10),
            Settings(10, 14, 10), Settings(16, 8, 8), Settings(10, 6, 2),
            Settings(10, 13, 6), Settings(12, 12, 8), Settings(7, 20, 10),
            Settings(10, 15, 6),
        )
        self.assertEqual(len(MISSIONS), 10)
        for mission, settings in zip(MISSIONS, solutions):
            with self.subTest(mission=mission["name"]):
                starter = read_code(mission["starter"])
                obstacles = mission["obstacles"]
                self.assertTrue(flight_to(starter, mission["target"], obstacles).blocked)
                self.assertTrue(flight_to(settings, mission["target"], obstacles).hit)

    def test_gravity_changes_range(self):
        earth = flight_to(Settings(8, 10, 10), Target(16, 0, 1))
        moon = flight_to(Settings(8, 10, 2), Target(40, 25, 1))
        self.assertGreater(moon.range, earth.range)
        self.assertEqual(position(Settings(8, 10, 10), 1), (8, 5))

    def test_live_motion_data_changes_during_flight(self):
        settings = Settings(8, 10, 10)
        launch_speed, launch_height, gravity = motion_data(settings, 0)
        top_speed, top_height, top_gravity = motion_data(settings, 1)
        self.assertGreater(launch_speed, top_speed)
        self.assertEqual((top_speed, top_height, top_gravity), (8, 5, 10))
        self.assertEqual((launch_height, gravity), (0, 10))

    def test_obstacle_detection_and_event_order(self):
        settings = Settings(30, 10, 10)
        thin_wall = Obstacle(10, 10.01, 2, 3)
        self.assertIsNotNone(obstacle_hit_time(settings, thin_wall, 2))
        target = Target(8, 5, 1)
        later_gate = Obstacle(11, 12, 0, 10, "gate")
        self.assertTrue(flight_to(Settings(8, 10, 10), target, (later_gate,)).hit)


if __name__ == "__main__":
    unittest.main()
