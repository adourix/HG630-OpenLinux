#!/usr/bin/env python3
"""Reassemble a research-only HG630 V2 package by replacing only its RootFS slot.

This tool deliberately does not rewrite Huawei package metadata, signatures, or
unknown checksums. Its output is NOT flashable until updater acceptance and
recovery are independently established.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tools.firmware_inspect import parse_hg630_component_table, parse_squashfs, parse_uimage

OEM_SHA256 = "d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222"
OEM_SIZE = 7_563_600
ROOTFS_OFFSET = 0x305CF
KERNEL_OFFSET = 0x5D85CF
ROOTFS_RESERVED = KERNEL_OFFSET - ROOTFS_OFFSET
UIMAGE_MAGIC = b"\x27\x05\x19\x56"
SQUASHFS_MAGIC = b"hsqs"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_layout(original: bytes, expected_sha256: str | None, expected_size: int | None) -> dict[str, Any]:
    if expected_size is not None and len(original) != expected_size:
        raise ValueError(f"unexpected OEM package size: {len(original)} != {expected_size}")
    digest = sha256_bytes(original)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"OEM package SHA-256 mismatch: {digest}")
    if original[ROOTFS_OFFSET:ROOTFS_OFFSET + 4] != SQUASHFS_MAGIC:
        raise ValueError("SquashFS magic is absent at the verified OEM RootFS offset")
    if original[KERNEL_OFFSET:KERNEL_OFFSET + 4] != UIMAGE_MAGIC:
        raise ValueError("uImage magic is absent at the verified OEM kernel offset")
    components = parse_hg630_component_table(original)
    rootfs_record = next((r for r in components["records"] if r["component_id"] == 1), None)
    kernel_record = next((r for r in components["records"] if r["component_id"] == 2), None)
    if rootfs_record is None or (rootfs_record["payload_offset"], rootfs_record["payload_size"]) != (ROOTFS_OFFSET, ROOTFS_RESERVED):
        raise ValueError("HG630 component table does not describe the verified RootFS slot")
    if kernel_record is None or kernel_record["payload_offset"] != KERNEL_OFFSET:
        raise ValueError("HG630 component table does not describe the verified kernel offset")
    rootfs = parse_squashfs(original, ROOTFS_OFFSET)
    kernel = parse_uimage(original, KERNEL_OFFSET)
    if not kernel["header_crc_valid"] or not kernel["data_crc_valid"]:
        raise ValueError("original uImage CRC validation failed")
    if rootfs["bytes_used"] > ROOTFS_RESERVED:
        raise ValueError("OEM RootFS bytes_used exceeds the reserved RootFS span")
    kernel_end = kernel["payload_end"]
    if kernel_end > len(original):
        raise ValueError("uImage payload extends beyond the package")
    return {
        "original_sha256": digest,
        "original_size": len(original),
        "rootfs": rootfs,
        "kernel": kernel,
        "components": components,
        "kernel_end": kernel_end,
        "trailing_bytes": len(original) - kernel_end,
    }


def _validate_candidate(rootfs: bytes) -> dict[str, Any]:
    if len(rootfs) < 96 or rootfs[:4] != SQUASHFS_MAGIC:
        raise ValueError("candidate is not a complete SquashFS image")
    parsed = parse_squashfs(rootfs, 0)
    if parsed["version"] != "4.0":
        raise ValueError(f"candidate SquashFS version must be 4.0, got {parsed['version']}")
    if parsed["compression_id"] != 4:
        raise ValueError("candidate must use the OEM XZ compression ID (4)")
    if parsed["block_size"] != 1_048_576:
        raise ValueError("candidate block size differs from the OEM 1 MiB profile")
    if parsed["bytes_used"] > ROOTFS_RESERVED:
        raise ValueError(
            f"candidate bytes_used {parsed['bytes_used']} exceeds reserved span {ROOTFS_RESERVED}"
        )
    if len(rootfs) > ROOTFS_RESERVED:
        raise ValueError(
            f"candidate file size {len(rootfs)} exceeds reserved span {ROOTFS_RESERVED}"
        )
    return parsed


def assemble(
    original: bytes,
    candidate_rootfs: bytes,
    *,
    expected_sha256: str | None = OEM_SHA256,
    expected_size: int | None = OEM_SIZE,
) -> tuple[bytes, dict[str, Any]]:
    """Return a package with only the reserved RootFS slot replaced."""
    original_info = _validate_layout(original, expected_sha256, expected_size)
    candidate_info = _validate_candidate(candidate_rootfs)

    output = bytearray(original)
    slot_end = ROOTFS_OFFSET + ROOTFS_RESERVED
    output[ROOTFS_OFFSET:slot_end] = b"\0" * ROOTFS_RESERVED
    output[ROOTFS_OFFSET:ROOTFS_OFFSET + len(candidate_rootfs)] = candidate_rootfs
    rebuilt = bytes(output)

    if rebuilt[:ROOTFS_OFFSET] != original[:ROOTFS_OFFSET]:
        raise AssertionError("package prefix changed unexpectedly")
    if rebuilt[slot_end:] != original[slot_end:]:
        raise AssertionError("kernel/trailing package region changed unexpectedly")

    rebuilt_kernel = parse_uimage(rebuilt, KERNEL_OFFSET)
    if not rebuilt_kernel["header_crc_valid"] or not rebuilt_kernel["data_crc_valid"]:
        raise AssertionError("uImage CRC changed after RootFS replacement")
    if rebuilt_kernel != original_info["kernel"]:
        raise AssertionError("uImage metadata changed after RootFS replacement")

    report = {
        "schema": 1,
        "release_classification": "EXPERIMENTAL_NON_FLASHABLE",
        "flashable": False,
        "input": {
            "sha256": original_info["original_sha256"],
            "size": original_info["original_size"],
        },
        "output": {
            "sha256": sha256_bytes(rebuilt),
            "size": len(rebuilt),
        },
        "layout": {
            "rootfs_offset": ROOTFS_OFFSET,
            "kernel_offset": KERNEL_OFFSET,
            "reserved_rootfs_span": ROOTFS_RESERVED,
            "candidate_file_size": len(candidate_rootfs),
            "candidate_bytes_used": candidate_info["bytes_used"],
            "remaining_internal_margin": ROOTFS_RESERVED - candidate_info["bytes_used"],
            "candidate_sha256": sha256_bytes(candidate_rootfs),
            "candidate_version": candidate_info["version"],
            "candidate_compression_id": candidate_info["compression_id"],
            "candidate_block_size": candidate_info["block_size"],
        },
        "preservation": {
            "package_prefix_byte_identical": True,
            "kernel_and_trailing_region_byte_identical": True,
            "uimage_header_crc_valid": rebuilt_kernel["header_crc_valid"],
            "uimage_data_crc_valid": rebuilt_kernel["data_crc_valid"],
            "kernel_payload_end": original_info["kernel_end"],
            "trailing_bytes_preserved": original_info["trailing_bytes"],
            "component_table_preserved": True,
        },
        "unverified": [
            "Huawei package header fields outside the observed component table and any package-level checksum",
            "OEM signature/authentication coverage and verification key",
            "updater acceptance and anti-rollback behavior",
            "physical flash partition map and erase geometry",
            "target-kernel mount and boot behavior",
            "device recovery procedure",
        ],
        "warning": (
            "Research reconstruction only. Unknown Huawei checksums/signatures were not "
            "recomputed. Do not flash this image."
        ),
    }
    return rebuilt, report


def validate_extraction(image: Path, expected_rootfs: Path | None = None) -> dict[str, Any]:
    """Require host unsquashfs structural and extraction checks."""
    summary = subprocess.run(
        ["unsquashfs", "-s", str(image)], check=True, capture_output=True, text=True
    ).stdout
    with tempfile.TemporaryDirectory(prefix="hg630-fw-rootfs-") as temp:
        extracted = Path(temp) / "rootfs"
        extracted.mkdir()
        subprocess.run(
            ["unsquashfs", "-no-progress", "-d", str(extracted), str(image)],
            check=True, capture_output=True, text=True,
        )
        if not any(extracted.iterdir()):
            raise ValueError("candidate RootFS extracted no entries")
        result: dict[str, Any] = {
            "unsquashfs_summary": summary,
            "extracted_entry_count": sum(1 for _ in extracted.rglob("*")),
            "extraction_succeeded": True,
        }
        if expected_rootfs is not None:
            from tools.validate_rootfs import inventory
            expected = inventory(expected_rootfs.resolve())
            actual = inventory(extracted)
            missing = sorted(set(expected) - set(actual))
            extra = sorted(set(actual) - set(expected))
            changed = sorted(p for p in set(expected) & set(actual) if expected[p] != actual[p])
            result.update({
                "expected_rootfs": str(expected_rootfs.resolve()),
                "missing": missing,
                "extra": extra,
                "changed": changed,
                "content_and_metadata_match": not (missing or extra or changed),
            })
            if missing or extra or changed:
                raise ValueError("candidate extraction does not match expected staged RootFS")
        return result


def rebuild(
    original_path: Path,
    rootfs_path: Path,
    output_path: Path,
    *,
    expected_rootfs: Path | None = None,
    skip_extraction_validation: bool = False,
) -> dict[str, Any]:
    original_path = original_path.resolve()
    rootfs_path = rootfs_path.resolve()
    output_path = output_path.resolve()
    if output_path in {original_path, rootfs_path}:
        raise ValueError("output must not overwrite either input")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")
    original = original_path.read_bytes()
    candidate = rootfs_path.read_bytes()
    package, report = assemble(original, candidate)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(package)
    report["source_paths"] = {
        "original_firmware": str(original_path),
        "candidate_rootfs": str(rootfs_path),
    }
    report["host_validation"] = (
        {"skipped": True, "reason": "explicit --skip-extraction-validation"}
        if skip_extraction_validation
        else validate_extraction(rootfs_path, expected_rootfs)
    )
    report_path = output_path.with_suffix(output_path.suffix + ".report.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_firmware", type=Path)
    parser.add_argument("candidate_rootfs", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-rootfs", type=Path, help="staged RootFS tree for full path/content/metadata comparison")
    parser.add_argument("--skip-extraction-validation", action="store_true", help="skip unsquashfs extraction check; not recommended")
    args = parser.parse_args()
    report = rebuild(
        args.original_firmware, args.candidate_rootfs, args.output,
        expected_rootfs=args.expected_rootfs,
        skip_extraction_validation=args.skip_extraction_validation,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
