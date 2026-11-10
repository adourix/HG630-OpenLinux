import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from tools.firmware_inspect import parse_uimage, inspect, UIMAGE_MAGIC

class FirmwareInspectorTests(unittest.TestCase):
    def make_uimage(self, payload=b"test-kernel"):
        fields = [UIMAGE_MAGIC, 0, 0, len(payload), 0x81208000, 0x81208000,
                  zlib.crc32(payload) & 0xffffffff, 5, 2, 2, 3, b"Linux-test"]
        header = bytearray(struct.pack(">7I4B32s", *fields))
        fields[1] = zlib.crc32(header) & 0xffffffff
        return struct.pack(">7I4B32s", *fields) + payload

    def test_uimage_checksums(self):
        result = parse_uimage(self.make_uimage(), 0)
        self.assertTrue(result["header_crc_valid"])
        self.assertTrue(result["data_crc_valid"])
        self.assertEqual(result["payload_size"], len(b"test-kernel"))

    def test_uimage_rejects_truncated_payload(self):
        with self.assertRaises(ValueError):
            parse_uimage(self.make_uimage()[:-2], 0)

    def test_inspect_hash_and_uimage(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test.bin"
            path.write_bytes(self.make_uimage())
            result = inspect(path)
            self.assertEqual(result["size_bytes"], path.stat().st_size)
            self.assertEqual(len(result["uimage"]), 1)

if __name__ == "__main__":
    unittest.main()
