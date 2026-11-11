import os
import stat
import tempfile
import unittest
from pathlib import Path

from tools.build_rootfs import (
    _apply_overlay_entry,
    _overlay_path_allowed,
    _assert_no_symlink_parents,
    build,
    copy_rootfs,
)
from tools.validate_rootfs import validate


class RootFsCopyTests(unittest.TestCase):
    def test_copy_preserves_hardlinks_symlinks_fifo_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            staged = base / "staged"
            source.mkdir()
            first = source / "first"
            first.write_bytes(b"same inode")
            os.chmod(first, 0o640)
            os.link(first, source / "second")
            (source / "link").symlink_to("first")
            os.mkfifo(source / "control", 0o620)

            copy_rootfs(source, staged)

            self.assertEqual((staged / "first").read_bytes(), b"same inode")
            self.assertEqual(os.stat(staged / "first").st_ino, os.stat(staged / "second").st_ino)
            self.assertTrue((staged / "link").is_symlink())
            self.assertEqual(os.readlink(staged / "link"), "first")
            self.assertTrue(stat.S_ISFIFO((staged / "control").lstat().st_mode))
            self.assertEqual(stat.S_IMODE((staged / "first").stat().st_mode), 0o640)
            self.assertEqual((staged / "first").stat().st_uid, first.stat().st_uid)
            self.assertEqual((staged / "first").stat().st_gid, first.stat().st_gid)

    def test_socket_is_rejected_instead_of_silently_lost(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            source.mkdir()
            socket_path = source / "service.sock"
            sock = __import__("socket").socket(__import__("socket").AF_UNIX)
            try:
                sock.bind(str(socket_path))
                with self.assertRaisesRegex(ValueError, "unsupported RootFS entry"):
                    copy_rootfs(source, base / "staged")
            finally:
                sock.close()

    def test_output_inside_source_is_rejected_before_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "keep").write_text("do not remove")
            with self.assertRaisesRegex(ValueError, "inside the source RootFS"):
                build(source, [], source / "output")
            self.assertTrue((source / "keep").exists())


class RootFsBuildTests(unittest.TestCase):
    def test_tiny_image_build_is_extractable(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            output = base / "output"
            source.mkdir()
            (source / "etc").mkdir()
            (source / "etc" / "release").write_text("HG630 test\n")
            report = build(source, [], output, processors=1)
            self.assertEqual(report["squashfs_size"], (output / "rootfs.squashfs").stat().st_size)

    def test_padding_is_deterministic_and_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "file").write_text("payload")
            output = Path(directory) / "output"
            report = build(source, [], output, processors=1, pad_to=131072)
            self.assertGreater(report["squashfs_padding"], 0)
            self.assertEqual(report["squashfs_size"], 131072)
            self.assertEqual((output / "rootfs.squashfs").stat().st_size, 131072)
            self.assertTrue((output / "build-report.json").exists())
            comparison = validate(output / "rootfs.squashfs", source)
            self.assertTrue(comparison["match"])



class OverlaySafetyTests(unittest.TestCase):
    def test_allowlist_glob_allows_only_matching_paths_and_ancestors(self):
        patterns = ["usr/libexec/openlinux-services/*", "usr/sbin/openlinuxctl"]
        self.assertTrue(_overlay_path_allowed("usr", patterns))
        self.assertTrue(_overlay_path_allowed("usr/libexec", patterns))
        self.assertTrue(_overlay_path_allowed("usr/libexec/openlinux-services", patterns))
        self.assertTrue(_overlay_path_allowed("usr/libexec/openlinux-services/network", patterns))
        self.assertTrue(_overlay_path_allowed("usr/sbin/openlinuxctl", patterns))
        self.assertFalse(_overlay_path_allowed("etc/passwd", patterns))
        self.assertFalse(_overlay_path_allowed("../outside", patterns))

    def test_allowlist_rejects_unsafe_patterns(self):
        with self.assertRaisesRegex(ValueError, "unsafe overlay allowlist"):
            _overlay_path_allowed("usr/bin/tool", ["../*"])

    def test_existing_oem_directory_metadata_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "overlay-dir"
            target = base / "oem-dir"
            source.mkdir()
            target.mkdir()
            os.chmod(source, 0o700)
            os.chmod(target, 0o755)
            _apply_overlay_entry(source, target)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o755)

    def test_overlay_directory_replaces_conflicting_file(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "overlay-dir"
            target = base / "target"
            source.mkdir()
            target.write_text("old")
            _apply_overlay_entry(source, target)
            self.assertTrue(target.is_dir())

    def test_overlay_cannot_traverse_vendor_symlink_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            stage = base / "stage"
            outside = base / "outside"
            stage.mkdir()
            outside.mkdir()
            (stage / "etc").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink parent"):
                _assert_no_symlink_parents(stage, Path("etc/openlinux/config"))

    def test_overlay_build_requires_explicit_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            overlay = base / "overlay"
            source.mkdir()
            overlay.mkdir()
            (overlay / "file").write_text("payload")
            with self.assertRaisesRegex(ValueError, "explicit path allowlist"):
                build(source, [overlay], base / "output")


if __name__ == "__main__":
    unittest.main()
