#!/usr/bin/env python3
"""Validate and compare an extracted SquashFS RootFS without modifying inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root: Path) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for path in sorted([root, *root.rglob("*")]):
        relative = "." if path == root else str(path.relative_to(root))
        info = path.lstat()
        kind = "directory" if stat.S_ISDIR(info.st_mode) else "regular" if stat.S_ISREG(info.st_mode) else "symlink" if stat.S_ISLNK(info.st_mode) else "fifo" if stat.S_ISFIFO(info.st_mode) else "character" if stat.S_ISCHR(info.st_mode) else "block" if stat.S_ISBLK(info.st_mode) else "unsupported"
        entry: dict[str, object] = {"kind": kind, "mode": stat.S_IMODE(info.st_mode), "uid": info.st_uid, "gid": info.st_gid, "mtime": int(info.st_mtime)}
        if kind == "regular":
            entry["sha256"] = digest(path)
            entry["size"] = info.st_size
        elif kind == "symlink":
            entry["target"] = os.readlink(path)
        elif kind in {"character", "block"}:
            entry["rdev"] = [os.major(info.st_rdev), os.minor(info.st_rdev)]
        result[relative] = entry
    return result


def validate(image: Path, source: Path | None = None, allowed_extra: set[str] | None = None, allowed_difference: set[str] | None = None) -> dict[str, object]:
    image = image.resolve()
    allowed_extra = allowed_extra or set()
    allowed_difference = allowed_difference or set()
    summary = subprocess.run(["unsquashfs", "-s", str(image)], check=True, capture_output=True, text=True).stdout
    with tempfile.TemporaryDirectory(prefix="rootfs-compare-") as directory:
        subprocess.run(["unsquashfs", "-no-progress", "-d", directory, str(image)], check=True, capture_output=True, text=True)
        generated = inventory(Path(directory))
        report: dict[str, object] = {
            "image": str(image),
            "image_sha256": digest(image),
            "image_size": image.stat().st_size,
            "validation_level": "SQUASHFS_STRUCTURE_AND_EXTRACTION",
            "unsquashfs_summary": summary,
            "generated_entries": len(generated),
        }
        if source is not None:
            expected = inventory(source.resolve())
            missing = sorted(set(expected) - set(generated))
            extra = sorted(set(generated) - set(expected) - allowed_extra)
            changed = sorted(path for path in set(expected) & set(generated) if expected[path] != generated[path] and path not in allowed_difference)
            intentional = sorted((set(generated) - set(expected)) & allowed_extra)
            report.update({"source": str(source.resolve()), "source_entries": len(expected), "missing": missing, "extra": extra, "intentional_additions": intentional, "changed": changed, "match": not (missing or extra or changed)})
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--source", type=Path, help="source RootFS to compare with the extracted image")
    parser.add_argument("--allow-extra", action="append", default=[], help="relative path allowed in image but absent from source")
    parser.add_argument("--allow-difference", action="append", default=[], help="relative path whose metadata/content difference is intentional")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = validate(args.image, args.source, set(args.allow_extra), set(args.allow_difference))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("match", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
