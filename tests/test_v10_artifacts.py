import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V10ArtifactTests(unittest.TestCase):
    def test_v10_manifest_is_explicitly_non_flashable(self):
        manifest = json.loads((ROOT / "analysis/openlinux/v1.0/build-manifest.json").read_text())
        self.assertEqual(manifest["status"], "EXPERIMENTAL_NON_FLASHABLE")
        self.assertFalse(manifest["flashable"])
        self.assertEqual(manifest["verification"]["oem_signature"], "BLOCKED")

    def test_component_map_does_not_claim_mtd_semantics(self):
        component_map = json.loads((ROOT / "analysis/openlinux/v1.0/component-map.json").read_text())
        self.assertEqual(component_map["mtd_mapping"], "UNKNOWN")
        self.assertEqual(component_map["flashability"], "BLOCKED")
        self.assertEqual(component_map["original"]["sha256"], "d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222")
