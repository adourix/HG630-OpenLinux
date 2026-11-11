#!/usr/bin/env python3
"""Rebuild and compare an OEM RootFS with multiple SquashFS processors.

Inputs are read-only.  The output directory must be new so that old run
evidence cannot be overwritten accidentally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.validate_rootfs import validate


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tool_version(tool: Path) -> str:
    return subprocess.run([str(tool), "-version"], check=True, capture_output=True, text=True).stdout.strip()


def summary(image: Path) -> dict[str, object]:
    text = subprocess.run(["unsquashfs", "-s", str(image)], check=True, capture_output=True, text=True).stdout
    patterns = {
        "bytes_used": r"Filesystem size (\d+) bytes",
        "block_size": r"Block size (\d+)",
        "fragments": r"Number of fragments (\d+)",
        "inodes": r"Number of inodes (\d+)",
        "ids": r"Number of ids (\d+)",
        "compression": r"Compression (.+)",
        "creation": r"Creation or last append time (.+)",
    }
    result: dict[str, object] = {"raw": text}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            result[key] = int(value) if value.isdigit() else value
    result["file_size"] = image.stat().st_size
    result["sha256"] = sha256(image)
    return result


def build_variant(source: Path, tool: Path, destination: Path, normalized: bool) -> dict[str, object]:
    destination.mkdir(parents=True, exist_ok=False)
    image = destination / "rootfs.squashfs"
    command = [str(tool), str(source), str(image), "-noappend", "-comp", "xz", "-no-xattrs", "-b", "1M", "-processors", "1", "-no-progress"]
    if normalized:
        command += ["-all-time", "1490771239", "-mkfs-time", "1490771239"]
    (destination / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    subprocess.run(command, check=True, capture_output=True, text=True)
    (destination / "mksquashfs.log").write_text("command: " + " ".join(command) + "\n")
    comparison = validate(image, source)
    result = {
        "tool": tool_version(tool),
        "tool_path": str(tool),
        "normalized_timestamps": normalized,
        "command": command,
        "summary": summary(image),
        "comparison": comparison,
    }
    (destination / "comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n")
    return result


def run(source: Path, original: Path, output: Path, tools: list[tuple[str, Path]]) -> dict[str, object]:
    source = source.resolve()
    original = original.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to reuse existing output directory: {output}")
    output.mkdir(parents=True)
    original_result = {"path": str(original), "summary": summary(original), "comparison": validate(original, source)}
    variants: list[dict[str, object]] = []
    for label, tool in tools:
        variants.append({"label": label, "native": build_variant(source, tool, output / f"{label}-native", False)})
        help_process = subprocess.run([str(tool), "-help"], check=False, capture_output=True, text=True)
        help_text = help_process.stdout + help_process.stderr
        if "-all-time" in help_text and "-mkfs-time" in help_text:
            variants[-1]["normalized"] = build_variant(source, tool, output / f"{label}-normalized", True)
    report = {
        "schema": 1,
        "host": {"platform": platform.platform(), "python": platform.python_version(), "compiler": subprocess.run(["gcc", "--version"], capture_output=True, text=True).stdout.splitlines()[0]},
        "source_rootfs": str(source),
        "original": original_result,
        "tools": variants,
        "reserved_span": 5931008,
        "notes": ["A filesystem metadata/content match is not byte identity or proof of bootability.", "All images are host-side research artifacts; no firmware or kernel was modified."],
    }
    (output / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tool", action="append", required=True, metavar="LABEL=PATH")
    args = parser.parse_args()
    tools = []
    for spec in args.tool:
        label, separator, raw_path = spec.partition("=")
        if not separator or not label or not raw_path:
            parser.error(f"--tool must be LABEL=PATH: {spec}")
        tools.append((label, Path(raw_path).resolve()))
    run(args.source, args.original, args.output, tools)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
