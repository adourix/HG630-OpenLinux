import struct
import tempfile
import unittest
from pathlib import Path

from tools.detect_abi import (
    EF_ARM_ABI_FLOAT_HARD,
    EF_ARM_ABI_FLOAT_SOFT,
    classify_abi,
    inspect_elf,
    parse_arm_attributes,
)


def elf32(flags: int, machine: int = 40) -> bytes:
    header = bytearray(52)
    header[:4] = b"\x7fELF"
    header[4:6] = bytes((1, 1))  # ELF32, little endian
    struct.pack_into("<H", header, 16, 2)  # ET_EXEC
    struct.pack_into("<H", header, 18, machine)
    struct.pack_into("<I", header, 20, 1)
    struct.pack_into("<I", header, 36, flags)
    struct.pack_into("<HHH", header, 46, 40, 0, 0)
    return bytes(header)


def attrs(vfp_args: int) -> bytes:
    file_subsection = struct.pack("<I", 6) + bytes((28, vfp_args))
    subsection = struct.pack("<I", 4 + 6 + len(file_subsection)) + b"aeabi\0" + file_subsection
    return b"A" + subsection


class DetectAbiTests(unittest.TestCase):
    def test_hard_float_e_flags_are_decoded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hard"
            path.write_bytes(elf32(EF_ARM_ABI_FLOAT_HARD))
            result = inspect_elf(path)
        self.assertEqual(result["architecture"], "ARM")
        self.assertEqual(result["raw_elf_flags"], "0x00000400")
        self.assertEqual(result["abi"], "hard")


    def test_soft_float_e_flags_are_decoded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "soft"
            path.write_bytes(elf32(EF_ARM_ABI_FLOAT_SOFT))
            result = inspect_elf(path)
        self.assertEqual(result["abi"], "soft")
        self.assertIn("EF_ARM_ABI_FLOAT_SOFT", result["abi_evidence"][0])


    def test_arm_attributes_soft_and_hard_calling_conventions(self):
        hard = parse_arm_attributes(attrs(1))
        soft = parse_arm_attributes(attrs(0))
        self.assertEqual(hard["vendor"], "aeabi")
        self.assertEqual(hard["tags"]["28"], 1)
        self.assertEqual(classify_abi(None, hard)[0], "hard")
        self.assertEqual(classify_abi(None, soft)[0], "soft")


    def test_missing_float_evidence_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ambiguous"
            path.write_bytes(elf32(0))
            result = inspect_elf(path)
        self.assertIsNone(result["abi"])
        self.assertIsNone(classify_abi(EF_ARM_ABI_FLOAT_HARD | EF_ARM_ABI_FLOAT_SOFT, None)[0])


if __name__ == "__main__":
    unittest.main()
