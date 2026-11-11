import unittest

from tools.validate_release_classification import validate


class ReleaseClassificationTests(unittest.TestCase):
    def test_research_manifest_is_safe(self):
        self.assertEqual(validate({"release_classification": "RESEARCH_ONLY", "flashable": False}), [])

    def test_flashable_requires_all_gates(self):
        errors = validate({"release_classification": "FLASHABLE", "flashable": True, "gates": {}})
        self.assertEqual(len(errors), 5)

    def test_flashable_is_accepted_only_with_verified_gates(self):
        gates = {name: "VERIFIED" for name in ("oem_signature", "metadata_to_mtd", "target_boot", "recovery", "rootfs_compatibility")}
        self.assertEqual(validate({"release_classification": "FLASHABLE", "flashable": True, "gates": gates}), [])
