#!/usr/bin/env python3
"""Enforce conservative firmware release classifications from a JSON manifest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FLASHABLE_GATES = (
    "oem_signature",
    "metadata_to_mtd",
    "target_boot",
    "recovery",
    "rootfs_compatibility",
)


def validate(manifest: dict) -> list[str]:
    errors: list[str] = []
    classification = manifest.get("release_classification")
    allowed = {"RESEARCH_ONLY", "EXPERIMENTAL_NON_FLASHABLE", "TARGET_BOOT_TESTED", "OEM_ACCEPTANCE_VERIFIED", "FLASHABLE"}
    if classification not in allowed:
        errors.append(f"invalid release classification: {classification!r}")
        return errors
    gates = manifest.get("gates", {})
    if classification == "FLASHABLE":
        for gate in REQUIRED_FLASHABLE_GATES:
            if gates.get(gate) != "VERIFIED":
                errors.append(f"FLASHABLE requires VERIFIED gate: {gate}")
    if classification in {"RESEARCH_ONLY", "EXPERIMENTAL_NON_FLASHABLE"} and manifest.get("flashable", False):
        errors.append(f"{classification} manifest cannot set flashable=true")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = validate(json.loads(args.manifest.read_text()))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("release classification accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
