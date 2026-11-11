import unittest

from tools.build_firmware import assemble


class FirmwareAssemblyTests(unittest.TestCase):
    def test_same_span_preserves_prefix_kernel_and_suffix(self):
        original = b"PREFIX" + b"old-rootfs" + b"KERNEL" + b"SUFFIX"
        replacement = b"new-rootfs"
        result = assemble(original, replacement, 6, 16)
        self.assertEqual(result, b"PREFIX" + replacement + b"KERNEL" + b"SUFFIX")

    def test_rejects_size_change_that_moves_unknown_kernel_offset(self):
        with self.assertRaises(ValueError):
            assemble(b"PREFIXold-rootfsKERNEL", b"too-long-rootfs", 6, 16)

    def test_rejects_overlapping_components(self):
        with self.assertRaises(ValueError):
            assemble(b"0123456789", b"root", 8, 4)
