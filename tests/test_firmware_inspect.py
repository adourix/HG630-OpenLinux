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

    def test_hg630_component_table(self):
        data = bytearray(0x736950)
        data[:4] = module.HUAWEI_PACKAGE_MAGIC
        records = [
            (2, 17, 0x5CF, 0x20000, b"HG630V2V100R001C298B010"),
            (2, 3, 0x205CF, 0x10000, b"v1.0"),
            (2, 1, 0x305CF, 0x5A8000, b"HG630V2V100R001C298B010"),
            (2, 2, 0x5D85CF, 0x15E228, b"HG630V2V100R001C298B010"),
        ]
        for index, (kind, component_id, offset, size, name) in enumerate(records):
            struct.pack_into(
                ">HHII32s", data, 0x7C + index * 44,
                kind, component_id, offset, size, name.ljust(32, b"\\\\0"),
            )
        parsed = module.parse_hg630_component_table(bytes(data))
        self.assertEqual(parsed["record_count"], 4)
        self.assertEqual(parsed["records"][2]["payload_offset"], 0x305CF)
        self.assertEqual(parsed["records"][2]["payload_size"], 0x5A8000)
        self.assertEqual(parsed["records"][3]["payload_offset"], 0x5D85CF)
        self.assertEqual(parsed["trailing_bytes_after_components"], 345)

    def test_hg630_component_table_rejects_non_contiguous_records(self):
        data = bytearray(0x736950)
        data[:4] = module.HUAWEI_PACKAGE_MAGIC
        records = [
            (2, 17, 0x5CF, 0x20000, b"first"),
            (2, 3, 0x205D0, 0xFFFF, b"second"),
            (2, 1, 0x305CF, 0x5A8000, b"rootfs"),
            (2, 2, 0x5D85CF, 0x15E228, b"kernel"),
        ]
        for index, (kind, component_id, offset, size, name) in enumerate(records):
            struct.pack_into(
                ">HHII32s", data, 0x7C + index * 44,
                kind, component_id, offset, size, name.ljust(32, b"\\\\0"),
            )
        with self.assertRaisesRegex(ValueError, "not contiguous"):
            module.parse_hg630_component_table(bytes(data))


if __name__ == "__main__":
    unittest.main()
