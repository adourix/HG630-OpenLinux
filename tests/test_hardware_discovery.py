import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/hardware_discovery.sh"


class HardwareDiscoveryTests(unittest.TestCase):
    def test_shell_syntax(self):
        result = subprocess.run(["sh", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_script_is_read_only(self):
        text = SCRIPT.read_text()
        for forbidden in ("flash_erase", "nandwrite", "fw_setenv", "mtd write", "reboot", "poweroff", "upg "):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"(^|[;&|\s])(dd|cp|mv|rm|touch|mkdir|mknod|insmod|rmmod)([\s;&|]|$)")
        self.assertIn("/proc/mtd", text)
        self.assertIn("/proc/cmdline", text)
        self.assertIn("/proc/meminfo", text)

    def test_collection_runs_without_writes(self):
        result = subprocess.run(["sh", str(SCRIPT)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("READ_ONLY_COLLECTION_COMPLETE", result.stdout)


if __name__ == "__main__":
    unittest.main()
