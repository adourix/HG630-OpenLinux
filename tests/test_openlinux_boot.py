import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.simulate_openlinux_boot import simulate


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "build/experimental/openlinux-overlay/rootfs"


class OpenLinuxBootSimulationTests(unittest.TestCase):
    def make_root(self, config=True):
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        (root / "etc/init.d").mkdir(parents=True)
        (root / "usr/sbin").mkdir(parents=True)
        (root / "var/log").mkdir(parents=True)
        (root / "etc/inittab").write_text("::sysinit:/etc/init.d/rcS\n::respawn:-/bin/sh\n")
        (root / "etc/init.d/rcS").write_text("#!/bin/sh\necho OEM-RCS\n")
        (root / "etc/init.d/rcS").chmod(0o755)
        shutil.copy2(OVERLAY / "etc/init.d/openlinux", root / "etc/init.d/openlinux")
        shutil.copy2(OVERLAY / "usr/sbin/openlinuxctl", root / "usr/sbin/openlinuxctl")
        if config:
            config_path = root / "etc/openlinux/openlinux.conf"
            config_path.parent.mkdir()
            config_path.write_text("SERVICE_NETWORK=disabled\nSERVICE_DNS=disabled\nSERVICE_SSH=disabled\nSERVICE_FIREWALL=disabled\nSERVICE_WEB=disabled\nLOG_MAX_BYTES=128\n")
        return directory, root

    def test_oem_only_and_disabled_modes(self):
        directory, root = self.make_root()
        with directory:
            result = simulate(root, False)
            self.assertEqual(result["oem_returncode"], 0)
            self.assertFalse(result["openlinux_attempted"])
            result = simulate(root, True)
            self.assertEqual(result["oem_returncode"], 0)
            self.assertEqual(result["openlinux_returncode"], 0)
            self.assertTrue(result["oem_failure_isolated"])

    def test_missing_and_invalid_configuration_are_nonfatal(self):
        directory, root = self.make_root(config=False)
        with directory:
            result = simulate(root, True)
            self.assertEqual(result["openlinux_returncode"], 0)
        directory, root = self.make_root()
        with directory:
            (root / "etc/openlinux/openlinux.conf").write_text("SERVICE_NETWORK=bad\n")
            result = simulate(root, True)
            self.assertEqual(result["openlinux_returncode"], 0)

    def fake_ctl(self, root, boot_body):
        ctl = root / "fake-ctl"
        ctl.write_text("#!/bin/sh\nif [ \"$1\" = validate ]; then exit 0; fi\n" + boot_body + "\n")
        ctl.chmod(0o755)
        return ctl

    def test_supervisor_failure_timeout_and_missing_binary_are_isolated(self):
        directory, root = self.make_root()
        with directory:
            ctl = self.fake_ctl(root, "exit 7")
            result = simulate(root, True, ctl=ctl)
            self.assertEqual(result["openlinux_returncode"], 0)
            ctl = self.fake_ctl(root, "sleep 3")
            result = simulate(root, True, timeout=1, ctl=ctl)
            self.assertEqual(result["openlinux_returncode"], 0)
            result = simulate(root, True, ctl=root / "does-not-exist")
            self.assertEqual(result["openlinux_returncode"], 0)

    def test_logging_failure_is_nonfatal(self):
        directory, root = self.make_root()
        with directory:
            env = os.environ.copy()
            env.update({"OPENLINUX_ROOT": str(root), "OPENLINUX_LOG": "/dev/full"})
            result = subprocess.run(["/bin/sh", str(root / "etc/init.d/openlinux")], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
