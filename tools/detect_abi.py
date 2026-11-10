#!/usr/bin/env python3
"""Infer the userspace ARM ABI from extracted ELF files without modifying them."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def inspect_elf(path: Path) -> dict[str, object]:
    result: dict[str, object] = {"path": str(path), "readelf": None}
    try:
        proc = subprocess.run(
            ["readelf", "-h", "-A", str(path)],
            check=False, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["error"] = str(exc)
        return result
    text = proc.stdout + proc.stderr
    result["readelf_exit"] = proc.returncode
    result["machine"] = re.search(r"Machine:\s*(.+)", text).group(1).strip() if re.search(r"Machine:\s*(.+)", text) else None
    result["class"] = re.search(r"Class:\s*(.+)", text).group(1).strip() if re.search(r"Class:\s*(.+)", text) else None
    result["endianness"] = re.search(r"Data:\s*(.+)", text).group(1).strip() if re.search(r"Data:\s*(.+)", text) else None
    result["hard_float_marker"] = any(x in text for x in ("Tag_ABI_VFP_args: VFP registers", "Tag_ABI_HardFP_use"))
    result["soft_float_marker"] = "Tag_ABI_VFP_args: Base AAPCS" in text
    return result


def detect(root: Path) -> dict[str, object]:
    elfs = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            try:
                if path.read_bytes()[:4] == b"\x7fELF":
                    elfs.append(inspect_elf(path))
            except OSError:
                continue
    hard = sum(bool(x.get("hard_float_marker")) for x in elfs)
    soft = sum(bool(x.get("soft_float_marker")) for x in elfs)
    if hard and not soft:
        recommendation = "arm-linux-gnueabihf"
    elif soft and not hard:
        recommendation = "arm-linux-gnueabi"
    else:
        recommendation = "undetermined; inspect representative dynamically linked ELF files"
    return {
        "rootfs": str(root),
        "elf_count": len(elfs),
        "hard_float_elf_count": hard,
        "soft_float_elf_count": soft,
        "recommended_cross_prefix": recommendation,
        "basis": "ELF e_flags/AEABI attributes via readelf; no hardware assumptions",
        "elfs": elfs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rootfs", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    if not args.rootfs.is_dir():
        ap.error("rootfs directory does not exist")
    result = detect(args.rootfs)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "elfs"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
