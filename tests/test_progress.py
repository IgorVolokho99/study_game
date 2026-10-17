import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import load_progress, save_progress


class ProgressTests(unittest.TestCase):
    def test_legacy_progress_keeps_only_the_three_retained_levels(self):
        with tempfile.TemporaryDirectory() as directory:
            save_file = Path(directory) / "progress.json"
            save_file.write_text("[0, 4, 5, 7]", encoding="utf-8")
            with patch("main.SAVE_FILE", save_file):
                self.assertEqual(load_progress(), {0, 2})
                save_progress({0, 2, 9})
                self.assertEqual(load_progress(), {0, 2, 9})
            self.assertEqual(json.loads(save_file.read_text(encoding="utf-8")),
                             {"version": 2, "completed": [0, 2, 9]})


if __name__ == "__main__":
    unittest.main()
