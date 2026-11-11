import tempfile
import unittest
from pathlib import Path

from tools.analyze_mtd_write_path import strings as mtd_strings
from tools.analyze_upgrade_security import file_strings


class UpgradeAnalysisTests(unittest.TestCase):
    def test_security_string_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blob"
            path.write_bytes(b"xx/etc/root.pem\0\xffabc\0")
            self.assertEqual(file_strings(path)[0]["value"], "xx/etc/root.pem")

    def test_mtd_string_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blob"
            path.write_bytes(b"/dev/mtd0\0/dev/mtd15\0")
            self.assertEqual([x["value"] for x in mtd_strings(path)], ["/dev/mtd0", "/dev/mtd15"])
