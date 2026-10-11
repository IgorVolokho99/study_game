import unittest

from physics import CodeError, Settings, Target, flight_to, motion_data, position, read_code


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

    def test_all_missions_have_clear_solutions(self):
        cases = (
            (Settings(8, 10, 10), Target(16, 0, 1.15)),
            (Settings(8, 10, 2), Target(40, 25, 2.2)),
            (Settings(12, 12, 6), Target(36, 9, 1.8)),
            (Settings(8, 20, 10), Target(24, 15, 1.5)),
            (Settings(10, 20, 12), Target(30, 6, 1.6)),
        )
        for settings, target in cases:
            with self.subTest(target=target):
                self.assertTrue(flight_to(settings, target).hit)

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


if __name__ == "__main__":
    unittest.main()
