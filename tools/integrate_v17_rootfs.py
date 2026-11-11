#!/usr/bin/env python3
"""Build an additive OpenLinux V1.7 OEM RootFS candidate and audit preservation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tarfile
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_rootfs import build as build_rootfs
from tools.package_runtime import build as build_package
from tools.rebuild_firmware import ROOTFS_RESERVED
from tools.firmware_inspect import parse_squashfs
from tools.validate_rootfs import validate as validate_rootfs_image


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest(root: Path) -> dict[str, dict]:
    items = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        st = path.lstat()
        mode = stat.S_IMODE(st.st_mode)
        if stat.S_ISREG(st.st_mode):
            record = {"type": "file", "mode": mode, "uid": st.st_uid, "gid": st.st_gid,
                      "mtime_ns": st.st_mtime_ns, "size": st.st_size, "sha256": digest(path)}
        elif stat.S_ISDIR(st.st_mode):
            record = {"type": "directory", "mode": mode, "uid": st.st_uid, "gid": st.st_gid,
                      "mtime_ns": st.st_mtime_ns}
        elif stat.S_ISLNK(st.st_mode):
            record = {"type": "symlink", "target": os.readlink(path), "uid": st.st_uid,
                      "gid": st.st_gid, "mtime_ns": st.st_mtime_ns}
        elif stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode):
            record = {"type": "char" if stat.S_ISCHR(st.st_mode) else "block", "mode": mode,
                      "uid": st.st_uid, "gid": st.st_gid, "rdev": st.st_rdev}
        elif stat.S_ISFIFO(st.st_mode):
            record = {"type": "fifo", "mode": mode, "uid": st.st_uid, "gid": st.st_gid}
        else:
            raise ValueError(f"unsupported RootFS entry: {rel}")
        items[rel] = record
    return items


def integrate(rootfs: Path, source_squashfs: Path, runtime: Path, output: Path) -> dict:
    rootfs = rootfs.resolve(); source_squashfs = source_squashfs.resolve()
    runtime = runtime.resolve(); output = output.resolve()
    if output.exists():
        raise ValueError(f"output must be unique and absent; preserving existing evidence: {output}")
    if rootfs == output or rootfs in output.parents:
        raise ValueError("output must not be inside original RootFS")
    output.mkdir(parents=True)
    before = manifest(rootfs)
    archive = output / "openlinux-runtime-v1.7.tar.gz"
    pkg = build_package(runtime, archive)
    overlay = output / "overlay"
    overlay.mkdir(parents=True)
    package_root = overlay / "opt"
    package_root.mkdir()
    with tarfile.open(archive, "r:gz") as package:
        package.extractall(package_root, filter="data")
    overlay_path = overlay / "opt/openlinux"
    normalized_mtime = 1490771239
    for path in sorted([overlay, *overlay.rglob("*")], key=lambda item: len(item.parts), reverse=True):
        os.utime(path, (normalized_mtime, normalized_mtime), follow_symlinks=False)
    build = build_rootfs(rootfs, [overlay], output / "rootfs-build", source_squashfs,
                         processors=1, bcj=None, pad_to=None,
                         allowlist=["opt/openlinux/**"], sort_overlay_files=True)
    after = manifest(output / "rootfs-build/stage-rootfs")
    changed = sorted(path for path in before if before[path] != after.get(path))
    missing = sorted(path for path in before if path not in after)
    extras = sorted(path for path in after if path not in before)
    squashfs = Path(build["squashfs"])
    parsed = parse_squashfs(squashfs.read_bytes(), 0)
    extracted_check = validate_rootfs_image(squashfs, output / "rootfs-build/stage-rootfs")
    if not extracted_check.get("match"):
        raise ValueError("SquashFS extraction differs from the staged RootFS")
    report = {
        "classification": "RESEARCH_ONLY; RootFS candidate is not a firmware image",
        "original_rootfs": str(rootfs), "source_squashfs": str(source_squashfs),
        "runtime_package": {"path": str(archive), "size": pkg["size"], "sha256": pkg["sha256"]},
        "squashfs": {"path": str(squashfs), "size": squashfs.stat().st_size,
                     "bytes_used": parsed["bytes_used"], "sha256": digest(squashfs),
                     "reserved_span": ROOTFS_RESERVED,
                     "fits_reserved_span": parsed["bytes_used"] <= ROOTFS_RESERVED,
                     "version": parsed["version"], "compression_id": parsed["compression_id"],
                     "block_size": parsed["block_size"]},
        "oem_preservation": {"changed_original_paths": changed, "missing_original_paths": missing,
                             "added_paths": extras, "preserved": not changed and not missing},
        "squashfs_extraction_matches_stage": extracted_check["match"],
        "overlay_paths": [p.relative_to(overlay).as_posix() for p in sorted(overlay_path.rglob("*"))],
        "auto_start_hook_added": False,
        "kernel_or_driver_changed": False,
        "notes": ["No OEM /bin/sshd replacement; package invokes it by absolute path.",
                  "No account database or startup file was changed.",
                  "No target mount, authentication, or hardware validation was performed."],
    }
    (output / "before-manifest.json").write_text(json.dumps(before, indent=2, sort_keys=True) + "\n")
    (output / "after-manifest.json").write_text(json.dumps(after, indent=2, sort_keys=True) + "\n")
    (output / "integration-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if changed or missing:
        raise ValueError(f"OEM preservation check failed: changed={changed}, missing={missing}")
    if not report["squashfs"]["fits_reserved_span"]:
        raise ValueError(f"V1.7 RootFS exceeds reserved span: {parsed['bytes_used']} > {ROOTFS_RESERVED}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rootfs", type=Path, required=True)
    parser.add_argument("--source-squashfs", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, default=Path("build/runtime"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = integrate(args.rootfs, args.source_squashfs, args.runtime, args.output)
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
