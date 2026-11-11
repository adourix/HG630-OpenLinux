import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CTL = ROOT / "build/experimental/openlinux-overlay/rootfs/usr/sbin/openlinuxctl"


class OpenLinuxUserspaceTests(unittest.TestCase):
    def run_ctl(self, root: Path, command: str):
        env = os.environ.copy()
        env["OPENLINUX_ROOT"] = str(root)
        env["OPENLINUX_LOG"] = str(root / "var/log/test.log")
        return subprocess.run(
            ["sh", str(CTL), command], env=env, text=True,
            capture_output=True, check=False,
        )

    def write_config(self, root: Path, text: str):
        config = root / "etc/openlinux/openlinux.conf"
        config.parent.mkdir(parents=True)
        config.write_text(text)

    def test_valid_config_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root, "SERVICE_NETWORK=disabled\nSERVICE_SSH=enabled\n")
            result = self.run_ctl(root, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("network disabled", result.stdout)
            self.assertIn("ssh enabled", result.stdout)

    def test_invalid_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root, "SERVICE_NETWORK=maybe\n")
            result = self.run_ctl(root, "validate")
            self.assertNotEqual(result.returncode, 0)

    def test_boot_is_opt_in_and_logs_absent_service(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root, "SERVICE_SSH=enabled\n")
            result = self.run_ctl(root, "boot")
            self.assertEqual(result.returncode, 0, result.stderr)
            log = (root / "var/log/test.log").read_text()
            self.assertIn("ssh enabled but implementation is absent", log)
            self.assertIn("network disabled", log)


if __name__ == "__main__":
    unittest.main()
