import tempfile
import unittest
from pathlib import Path

from tools.experiments.oem_reproduction import summary


class ExperimentHelperTests(unittest.TestCase):
    def test_summary_reads_squashfs_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.squashfs"
            source = Path(directory) / "source"
            source.mkdir()
            (source / "hello").write_text("hello\n")
            import subprocess
            subprocess.run(["mksquashfs", str(source), str(image), "-noappend", "-comp", "xz", "-no-progress", "-processors", "1"], check=True, capture_output=True)
            result = summary(image)
            self.assertGreater(result["bytes_used"], 0)
            self.assertEqual(result["compression"], "xz")
            self.assertEqual(result["inodes"], 2)


if __name__ == "__main__":
    unittest.main()
