import struct
import unittest
import zlib

from tools.rebuild_firmware import (
    KERNEL_OFFSET,
    OEM_SIZE,
    ROOTFS_OFFSET,
    ROOTFS_RESERVED,
    assemble,
)


def make_squashfs(bytes_used=96):
    fields = (
        0x73717368, 1, 1490771239, 1_048_576, 0,
        4, 20, 704, 1, 4, 0,
        0, bytes_used, 0, 0, 0, 0, 0,
    )
    return struct.pack("<5I6H2Q5Q", *fields) + b"\0" * 8


def make_uimage(payload=b"kernel-payload"):
    fields = [
        0x27051956, 0, 1490771170, len(payload),
        0x81208000, 0x81208000, zlib.crc32(payload) & 0xFFFFFFFF,
        5, 2, 2, 3, b"Linux-2.6.30".ljust(32, b"\0"),
    ]
    header = bytearray(struct.pack(">7I4B32s", *fields))
    fields[1] = zlib.crc32(header) & 0xFFFFFFFF
    return struct.pack(">7I4B32s", *fields) + payload


def make_package():
    package = bytearray(b"\xA5" * OEM_SIZE)
    package[:4] = b"\x10\x32\x54\x76"
    kernel = make_uimage()
    records = [
        (2, 17, 0x5CF, 0x20000, b"HG630V2V100R001C298B010"),
        (2, 3, 0x205CF, 0x10000, b"v1.0"),
        (2, 1, ROOTFS_OFFSET, ROOTFS_RESERVED, b"HG630V2V100R001C298B010"),
        (2, 2, KERNEL_OFFSET, len(kernel), b"HG630V2V100R001C298B010"),
    ]
    for index, (kind, component_id, offset, size, name) in enumerate(records):
        struct.pack_into(
            ">HHII32s", package, 0x7C + index * 44,
            kind, component_id, offset, size, name.ljust(32, b"\0"),
        )
    package[ROOTFS_OFFSET:ROOTFS_OFFSET + 96] = make_squashfs()
    package[KERNEL_OFFSET:KERNEL_OFFSET + len(kernel)] = kernel
    return bytes(package)


class FirmwareRebuildTests(unittest.TestCase):
    def test_replaces_only_rootfs_reserved_region(self):
        original = make_package()
        candidate = make_squashfs()
        rebuilt, report = assemble(
            original, candidate, expected_sha256=None, expected_size=OEM_SIZE
        )
        slot_end = ROOTFS_OFFSET + ROOTFS_RESERVED
        self.assertEqual(rebuilt[:ROOTFS_OFFSET], original[:ROOTFS_OFFSET])
        self.assertEqual(rebuilt[slot_end:], original[slot_end:])
        self.assertEqual(rebuilt[ROOTFS_OFFSET:ROOTFS_OFFSET + len(candidate)], candidate)
        self.assertEqual(len(rebuilt), len(original))
        self.assertFalse(report["flashable"])
        self.assertEqual(report["release_classification"], "EXPERIMENTAL_NON_FLASHABLE")
        self.assertTrue(report["preservation"]["uimage_header_crc_valid"])
        self.assertTrue(report["preservation"]["uimage_data_crc_valid"])

    def test_rejects_wrong_original_hash(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            assemble(make_package(), make_squashfs(), expected_sha256="0" * 64)

    def test_rejects_candidate_over_reserved_span(self):
        candidate = make_squashfs(ROOTFS_RESERVED + 1)
        with self.assertRaisesRegex(ValueError, "bytes_used"):
            assemble(
                make_package(), candidate,
                expected_sha256=None, expected_size=OEM_SIZE,
            )

    def test_rejects_invalid_original_kernel_crc(self):
        original = bytearray(make_package())
        original[KERNEL_OFFSET + 64] ^= 0x01
        with self.assertRaisesRegex(ValueError, "uImage CRC"):
            assemble(
                bytes(original), make_squashfs(),
                expected_sha256=None, expected_size=OEM_SIZE,
            )

    def test_rejects_non_xz_candidate(self):
        candidate = bytearray(make_squashfs())
        struct.pack_into("<H", candidate, 20, 1)
        with self.assertRaisesRegex(ValueError, "XZ compression ID"):
            assemble(
                make_package(), bytes(candidate),
                expected_sha256=None, expected_size=OEM_SIZE,
            )

    def test_rejects_truncated_squashfs_candidate(self):
        candidate = make_squashfs(bytes_used=4096)
        with self.assertRaisesRegex(ValueError, "extends beyond"):
            assemble(
                make_package(), candidate,
                expected_sha256=None, expected_size=OEM_SIZE,
            )


if __name__ == "__main__":
    unittest.main()
