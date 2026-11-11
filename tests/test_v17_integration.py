import tempfile
import unittest
from pathlib import Path

from tools.integrate_v17_rootfs import integrate, manifest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "build/runtime"


class V17RootfsIntegrationTests(unittest.TestCase):
    def test_manifest_records_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "file").write_text("evidence")
            (root / "link").symlink_to("file")
            result = manifest(root)
            self.assertEqual(result["file"]["type"], "file")
            self.assertEqual(result["link"]["target"], "file")

    @unittest.skipUnless(__import__("shutil").which("mksquashfs") and __import__("shutil").which("unsquashfs"),
                         "SquashFS tools are required for integration test")
    def test_additive_candidate_preserves_oem_entries_and_fits(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            source = temp / "oem-rootfs"
            (source / "etc").mkdir(parents=True)
            (source / "etc/vendor.conf").write_text("owned by Huawei\n")
            (source / "etc/vendor-link").symlink_to("vendor.conf")
            source_image = temp / "source.squashfs"
            source_image.write_bytes(b"placeholder source identity")
            output = temp / "integration"
            report = integrate(source, source_image, RUNTIME, output)
            self.assertTrue(report["oem_preservation"]["preserved"])
            self.assertFalse(report["oem_preservation"]["changed_original_paths"])
            self.assertFalse(report["oem_preservation"]["missing_original_paths"])
            self.assertTrue(report["squashfs"]["fits_reserved_span"])
            self.assertIn("opt/openlinux/bin/openlinux-ssh-check", report["overlay_paths"])
            self.assertFalse(report["auto_start_hook_added"])
            self.assertTrue((output / "before-manifest.json").is_file())
            self.assertTrue((output / "after-manifest.json").is_file())

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); output = temp / "existing"; output.mkdir()
            marker = output / "keep"; marker.write_text("preserve")
            with self.assertRaisesRegex(ValueError, "unique and absent"):
                integrate(temp, temp / "source.squashfs", RUNTIME, output)
            self.assertEqual(marker.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
