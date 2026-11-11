#!/usr/bin/env python3
"""Run complete-overlay size experiments with a historical mksquashfs binary.

The source RootFS and overlay are copied into a new output directory.  No OEM
input is modified.  Each image is extracted and compared with the expected
source tree after the experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.build_rootfs import _apply_overlay_entry, _restore_oem_directory_metadata, copy_rootfs
from tools.validate_rootfs import validate
from tools.experiments.oem_reproduction import summary


RESERVED = 5_931_008
TIMESTAMP = 1_490_771_239


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def apply_overlay(stage: Path, overlay: Path) -> None:
    entries = sorted(overlay.rglob("*"))
    for source in entries:
        relative = source.relative_to(overlay)
        _apply_overlay_entry(source, stage / relative)


def build_stage(source: Path, overlay: Path, destination: Path) -> None:
    copy_rootfs(source, destination)
    apply_overlay(destination, overlay)
    _restore_oem_directory_metadata(source, destination)


def command_for(tool: Path, stage: Path, image: Path, extra: list[str]) -> list[str]:
    return [str(tool), str(stage), str(image), "-noappend", "-comp", "xz", "-no-xattrs", "-b", "1M", "-processors", "1", "-no-progress", *extra]


def set_mkfs_time(image: Path, timestamp: int = TIMESTAMP) -> None:
    """Set the SquashFS 4.0 superblock creation time deterministically.

    SquashFS-tools 4.2 predates the later -mkfs-time option.  The field is a
    documented little-endian superblock value and is not covered by a checksum.
    """
    data = bytearray(image.read_bytes())
    data[8:12] = timestamp.to_bytes(4, "little")
    image.write_bytes(data)


def run_one(tool: Path, stage: Path, expected: Path, destination: Path, label: str, extra: list[str]) -> dict[str, object]:
    destination.mkdir(parents=True, exist_ok=False)
    image = destination / "rootfs.squashfs"
    command = command_for(tool, stage, image, extra)
    process = subprocess.run(command, check=False, capture_output=True, text=True)
    if process.returncode:
        result = {"label": label, "extra": extra, "command": command, "status": "unsupported_or_failed", "returncode": process.returncode, "stderr": process.stderr}
        (destination / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    set_mkfs_time(image)
    comparison = validate(image, expected)
    data = summary(image)
    result = {"label": label, "extra": extra, "command": command, "summary": data, "sha256": digest(image), "difference_from_reserved": int(data["bytes_used"]) - RESERVED, "comparison": {"match": comparison.get("match"), "missing": len(comparison.get("missing", [])), "extra": len(comparison.get("extra", [])), "changed": len(comparison.get("changed", []))}}
    (destination / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def make_sort_file(directory: Path, entries: dict[str, int]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "sort.txt"
    path.write_text("\n".join(f"{name} {priority}" for name, priority in entries.items()) + "\n")
    return path


def run(source: Path, overlay: Path, tool: Path, output: Path) -> dict[str, object]:
    source, overlay, tool, output = source.resolve(), overlay.resolve(), tool.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to reuse existing output: {output}")
    output.mkdir(parents=True)
    stage = output / "stage-rootfs"
    build_stage(source, overlay, stage)
    variants: list[tuple[str, list[str]]] = [("base", [])]
    for size in ("87.5%", "75%", "62.5%", "50%", "37.5%", "25%", "16K"):
        variants.append(("dict-" + size.replace("%", "pct"), ["-Xdict-size", size]))
    for flag in ("-noI", "-noF", "-noD", "-no-fragments", "-always-use-fragments", "-no-duplicates"):
        variants.append((flag.lstrip("-").replace("-", "_"), [flag]))
    sort_dir = output / "sort-files"
    sort_dir.mkdir()
    overlay_names = [p.relative_to(overlay).as_posix() for p in sorted(overlay.rglob("*")) if p.is_file()]
    sort_specs = {
        "sort-overlay-first": {name: -100 for name in overlay_names},
        "sort-overlay-last": {name: 100 for name in overlay_names},
        "sort-controller-first": {"usr/sbin/openlinuxctl": -100},
        "sort-controller-last": {"usr/sbin/openlinuxctl": 100},
    }
    for label, entries in sort_specs.items():
        variants.append((label, ["-sort", str(make_sort_file(sort_dir / label, entries))]))
    results = [run_one(tool, stage, stage, output / label, label, extra) for label, extra in variants]
    report = {"schema": 1, "tool": str(tool), "source": str(source), "overlay": str(overlay), "reserved_span": RESERVED, "overlay_timestamp": TIMESTAMP, "results": results, "notes": ["All candidate images were extracted and compared to the staged complete overlay.", "Ordering tests use mksquashfs sort priorities; no OEM file was replaced or removed.", "-noI/-noF/-noD/no-fragments/always-use-fragments/no-duplicates are measurements only and are not accepted as compatible without matching OEM/kernel evidence."]}
    (output / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--tool", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.overlay, args.tool, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
