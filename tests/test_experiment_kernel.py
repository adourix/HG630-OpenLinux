import tempfile
import unittest
from pathlib import Path

from tools.experiments.kernel_xz_inspect import inspect


class KernelInspectionTests(unittest.TestCase):
    def test_reports_xz_stream_headers_and_conservative_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            image = base / "image"
            image.write_bytes(b"hsqs" + (1).to_bytes(4, "little") + b"\0\0\0\0" + (131072).to_bytes(4, "little") + b"\0\0\x04\0" + b"\0" * 64 + b"\xfd7zXZ\0" + b"\0" * 20)
            kernel = base / "kernel"
            kernel.write_bytes(b"squashfs_xz_init\0xz_dec_init\0")
            result = inspect(image, kernel)
            self.assertEqual(result["squashfs"]["block_size"], 131072)
            self.assertEqual(result["squashfs"]["xz_magic_count"], 1)
            self.assertFalse(result["claims"]["bcj_registration_proven"])


if __name__ == "__main__":
    unittest.main()
