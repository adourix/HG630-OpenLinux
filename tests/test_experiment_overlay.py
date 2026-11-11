import tempfile
import unittest
from pathlib import Path

from tools.experiments.overlay_optimization_matrix import make_sort_file


class OverlayOptimizationTests(unittest.TestCase):
    def test_sort_file_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = make_sort_file(Path(directory), {"usr/sbin/openlinuxctl": -100, "etc/init.d/openlinux": 100})
            self.assertEqual(path.read_text(), "usr/sbin/openlinuxctl -100\netc/init.d/openlinux 100\n")


if __name__ == "__main__":
    unittest.main()
