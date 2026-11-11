import struct
import unittest

from tools.analyze_upgrade_binary import decode_arm_branch, sign_extend


class UpgradeAnalysisHelpersTest(unittest.TestCase):
    def test_sign_extend(self):
        self.assertEqual(sign_extend(0x7FFFFF, 24), 0x7FFFFF)
        self.assertEqual(sign_extend(0x800000, 24), -0x800000)

    def test_decode_forward_bl(self):
        # BL +0x10 from an instruction at 0x1000: PC is instruction + 8.
        word = 0xEB000004
        self.assertEqual(decode_arm_branch(word, 0x1000)["kind"], "BL")
        self.assertEqual(decode_arm_branch(word, 0x1000)["target"], 0x1018)

    def test_decode_backward_conditional_branch(self):
        # BNE -0x10 from 0x2000.
        word = 0x1AFFFFFC
        decoded = decode_arm_branch(word, 0x2000)
        self.assertEqual(decoded["kind"], "B")
        self.assertEqual(decoded["condition"], 1)
        self.assertEqual(decoded["target"], 0x1FF8)

    def test_non_branch_is_ignored(self):
        self.assertIsNone(decode_arm_branch(struct.unpack("<I", b"\0\0\0\0")[0], 0))
