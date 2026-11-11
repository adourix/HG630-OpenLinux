#!/usr/bin/env python3
"""Assemble a same-layout experimental HG630 image without bypassing OEM checks.

The builder only replaces the verified SquashFS byte span when the replacement
has exactly the same reserved span as the original package.  The original
metadata prefix, original uImage, and all suffix bytes are copied unchanged.
Because the OEM signature/outer-integrity contract is unresolved, every output
is explicitly marked experimental and non-flashable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

try:
    from tools.inspect_firmware import inspect, parse
    from tools.validate_rootfs import validate as validate_rootfs
except ModuleNotFoundError:  # direct execution from the tools directory
    from inspect_firmware import inspect, parse
    from validate_rootfs import validate as validate_rootfs


KNOWN_ORIGINAL_SHA256 = "d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _single_component(report: dict, kind: str) -> dict:
    components = report["signatures"][kind]
    if len(components) != 1:
        raise ValueError(f"expected exactly one {kind} component, found {len(components)}")
    component = components[0]
    if component.get("error") or not component.get("within_file", False):
        raise ValueError(f"{kind} component is truncated or out of bounds")
    return component


def validate_original(data: bytes, expected_sha256: str | None = KNOWN_ORIGINAL_SHA256) -> tuple[dict, dict, dict]:
    actual = sha256_bytes(data)
    if expected_sha256 and actual != expected_sha256:
        raise ValueError(f"original firmware SHA-256 mismatch: expected {expected_sha256}, got {actual}")
    report = parse(data, "original-firmware")
    squashfs = _single_component(report, "squashfs")
    uimage = _single_component(report, "uimage")
    if squashfs.get("version") != "4.0":
        raise ValueError(f"unsupported SquashFS version: {squashfs.get('version')}")
    if not uimage.get("header_crc_valid") or not uimage.get("data_crc_valid"):
        raise ValueError("original uImage header/data CRC validation failed")
    if squashfs["end"] > uimage["offset"]:
        raise ValueError("original SquashFS overlaps original uImage")
    return report, squashfs, uimage


def validate_replacement_rootfs(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"custom RootFS image not found: {path}")
    raw = path.read_bytes()
    if raw[:4] != b"hsqs":
        raise ValueError("custom RootFS is not a SquashFS image")
    report = validate_rootfs(path)
    if report.get("validation_level") != "SQUASHFS_STRUCTURE_AND_EXTRACTION":
        raise ValueError("custom RootFS did not receive full SquashFS structure/extraction validation")
    return report


def assemble(original: bytes, replacement: bytes, squashfs_offset: int, uimage_offset: int) -> bytes:
    reserved = uimage_offset - squashfs_offset
    if reserved <= 0:
        raise ValueError("invalid component ordering")
    if len(replacement) != reserved:
        raise ValueError(f"custom RootFS must be exactly {reserved} bytes to preserve the verified uImage offset; got {len(replacement)}")
    return original[:squashfs_offset] + replacement + original[uimage_offset:]


def build(original_path: Path, rootfs_path: Path, output_path: Path, expected_sha256: str | None = KNOWN_ORIGINAL_SHA256) -> dict:
    original_path = original_path.resolve()
    rootfs_path = rootfs_path.resolve()
    output_path = output_path.resolve()
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")
    original = original_path.read_bytes()
    original_report, squashfs, uimage = validate_original(original, expected_sha256)
    rootfs_report = validate_replacement_rootfs(rootfs_path)
    replacement = rootfs_path.read_bytes()
    reserved = uimage["offset"] - squashfs["offset"]
    assembled = assemble(original, replacement, squashfs["offset"], uimage["offset"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(assembled)
    output_report = parse(assembled, str(output_path))
    output_squashfs = _single_component(output_report, "squashfs")
    output_uimage = _single_component(output_report, "uimage")
    if output_uimage["offset"] != uimage["offset"] or output_uimage["header_hex"] != uimage["header_hex"]:
        raise ValueError("assembled output changed the preserved uImage header or offset")
    if not output_uimage["header_crc_valid"] or not output_uimage["data_crc_valid"]:
        raise ValueError("assembled output failed preserved uImage CRC validation")
    if output_squashfs["offset"] != squashfs["offset"] or output_squashfs["bytes_used"] > reserved:
        raise ValueError("assembled output SquashFS is not contained in the reserved component span")
    manifest = {
        "tool": "build_firmware.py",
        "status": "EXPERIMENTAL_NON_FLASHABLE",
        "flashable": False,
        "reason": "OEM signature and outer-container integrity requirements remain UNKNOWN; this output must not be flashed.",
        "inputs": {"original_firmware": {"path": str(original_path), "sha256": sha256_bytes(original), "size": len(original)}, "custom_rootfs": {"path": str(rootfs_path), "sha256": sha256_bytes(replacement), "size": len(replacement), "validation": rootfs_report}},
        "preservation": {"metadata_prefix_preserved": True, "kernel_uimage_preserved": True, "kernel_uimage_sha256": sha256_bytes(original[uimage["offset"]:uimage["end"]]), "suffix_preserved": True, "unknown_header_fields_preserved": True},
        "layout": {"squashfs_offset": squashfs["offset"], "original_squashfs_bytes_used": squashfs["bytes_used"], "reserved_rootfs_span": reserved, "uimage_offset": uimage["offset"], "uimage_end": uimage["end"], "same_offsets": True},
        "validation_levels": {"rootfs_build_and_extraction": "VERIFIED", "kernel_structure_and_crc": "VERIFIED", "container_structure_and_embedded_components": "VERIFIED", "oem_update_acceptance": "UNKNOWN", "kernel_boot": "UNKNOWN", "hardware_boot": "UNKNOWN"},
        "output": {"path": str(output_path), "sha256": sha256_bytes(assembled), "size": len(assembled)},
        "original_inspection": {"issues": original_report["issues"], "squashfs": squashfs, "uimage": uimage},
        "output_inspection": {"issues": output_report["issues"], "squashfs": output_squashfs, "uimage": output_uimage},
    }
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    sha_path = output_path.with_suffix(output_path.suffix + ".sha256")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    sha_path.write_text(f"{manifest['output']['sha256']}  {output_path.name}\n")
    manifest["output"]["manifest"] = str(manifest_path)
    manifest["output"]["sha256_report"] = str(sha_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("rootfs", type=Path, help="validated custom SquashFS RootFS image")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-original-sha256", default=KNOWN_ORIGINAL_SHA256)
    parser.add_argument("--allow-unpinned-original", action="store_true", help="for synthetic tests only; do not use for OEM inputs")
    args = parser.parse_args()
    expected = None if args.allow_unpinned_original else args.expected_original_sha256
    try:
        print(json.dumps(build(args.original, args.rootfs, args.output, expected), indent=2, sort_keys=True))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
