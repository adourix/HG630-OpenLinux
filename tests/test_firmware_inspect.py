import importlib.util
import struct
import unittest
import zlib
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "firmware_inspect", Path(__file__).parents[1] / "tools" / "firmware_inspect.py"
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FirmwareInspectTests(unittest.TestCase):
    @staticmethod
    def make_uimage(payload: bytes, name: bytes = b"test-kernel") -> bytes:
        fields = [
            0x27051956, 0, 0, len(payload), 0x81208000, 0x81208000,
            zlib.crc32(payload) & 0xFFFFFFFF, 5, 2, 2, 3,
            name.ljust(32, b"\0")[:32],
        ]
        header = bytearray(struct.pack(">7I4B32s", *fields))
        fields[1] = zlib.crc32(header) & 0xFFFFFFFF
        return struct.pack(">7I4B32s", *fields) + payload

    def test_uimage_crc_and_metadata(self):
        result = module.parse_uimage(self.make_uimage(b"HG630 test payload"), 0)
        self.assertTrue(result["header_crc_valid"])
        self.assertTrue(result["data_crc_valid"])
        self.assertEqual(result["payload_size"], len(b"HG630 test payload"))
        self.assertEqual(result["name"], "test-kernel")

    def test_truncated_uimage_rejected(self):
        with self.assertRaisesRegex(ValueError, "extends beyond"):
            module.parse_uimage(self.make_uimage(b"0123456789")[:-3], 0)

    def test_signature_scan(self):
        data = b"abc" + module.SQUASHFS_MAGIC + b"xyz" + module.SQUASHFS_MAGIC
        self.assertEqual(module.find_all(data, module.SQUASHFS_MAGIC), [3, 10])


if __name__ == "__main__":
    unittest.main()
