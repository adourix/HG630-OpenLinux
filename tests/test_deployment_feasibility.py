import tempfile
import unittest
from pathlib import Path

from tools.analyze_deployment_feasibility import rootfs_evidence


class DeploymentFeasibilityTests(unittest.TestCase):
    def test_inventory_preserves_init_and_static_startup_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "etc/init.d").mkdir(parents=True)
            (root / "etc/inittab").write_text("::sysinit:/etc/init.d/rcS\n")
            (root / "etc/init.d/rcS").write_text("#!/bin/sh\nPATH=/bin\n")
            (root / "etc/profile").write_text("mount -t proc /proc /proc\nstartbsp\n")
            (root / "bin").mkdir()
            (root / "bin/busybox").write_bytes(b"fixture")
            (root / "init").symlink_to("./bin/busybox")
            result = rootfs_evidence(root)
            self.assertTrue(result["init"]["is_symlink"])
            self.assertIn("mount -t proc /proc /proc", result["startup_markers"])
            self.assertIn("startbsp", result["startup_markers"])

    def test_missing_rootfs_startup_files_is_not_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            result = rootfs_evidence(Path(temp))
            self.assertEqual(result["status"], "PARTIALLY VERIFIED")
            self.assertFalse(result["init"]["exists"])


if __name__ == "__main__":
    unittest.main()
