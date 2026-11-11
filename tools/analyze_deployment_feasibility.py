#!/usr/bin/env python3
"""Collect conservative, read-only evidence for OEM-preserving deployment.

This tool parses the already-supported OEM container structures and inventories
only text/configuration files in an extracted RootFS.  It never executes OEM
programs, opens MTD devices, or attempts an update.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.inspect_firmware import inspect
except ModuleNotFoundError:
    from inspect_firmware import inspect


TEXT_NAMES = {"inittab", "rcS", "profile", "insmod_all.sh", "insmod_eth.sh"}
COMMAND_MARKERS = (
    "mount ", "insmod ", "startbsp", "hi_xpon", "hsanportinit", "mic", "mtdblock",
)
SERVICE_NAMES = ("upg", "startbsp", "mic", "web", "dns", "dhcps", "sshd", "telnetd")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def rootfs_evidence(rootfs: Path) -> dict:
    files = {}
    for name in TEXT_NAMES:
        path = rootfs / "etc" / ("init.d/rcS" if name == "rcS" else name)
        if path.is_file():
            text = read_text(path)
            if text is not None:
                files[name] = {
                    "path": str(path),
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "lines": text.splitlines(),
                }

    init = rootfs / "init"
    services = {}
    for name in SERVICE_NAMES:
        path = next((rootfs / d / name for d in ("bin", "sbin", "usr/bin", "usr/sbin")
                     if (rootfs / d / name).exists()), None)
        if path:
            services[name] = {"path": str(path), "type": "symlink" if path.is_symlink() else "file"}

    profile = files.get("profile", {}).get("lines", [])
    rc = files.get("rcS", {}).get("lines", [])
    startup_markers = []
    for line in profile + rc:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and any(marker in stripped for marker in COMMAND_MARKERS):
            startup_markers.append(stripped)

    return {
        "rootfs": str(rootfs),
        "init": {"exists": init.exists(), "is_symlink": init.is_symlink(),
                  "target": init.readlink().as_posix() if init.is_symlink() else None},
        "configuration_files": files,
        "startup_markers": startup_markers,
        "vendor_service_entries": services,
        "mtdblock_references": sorted({line.strip() for line in profile + rc if "mtdblock" in line}),
        "status": "VERIFIED_STATIC" if files and init.exists() else "PARTIALLY VERIFIED",
    }


def collect(firmware: Path, rootfs: Path) -> dict:
    parsed = inspect(firmware)
    squashfs = parsed["signatures"]["squashfs"]
    uimage = parsed["signatures"]["uimage"]
    return {
        "tool": "analyze_deployment_feasibility.py",
        "classification_legend": ["VERIFIED", "PARTIALLY VERIFIED", "UNKNOWN", "BLOCKED"],
        "inputs": {"firmware": {"path": str(firmware), "size": firmware.stat().st_size,
                                  "sha256": sha256(firmware)}, "rootfs": str(rootfs)},
        "container": {
            "metadata": parsed["metadata"],
            "squashfs": squashfs,
            "uimage": uimage,
            "metadata_semantics": "UNKNOWN",
            "package_to_physical_flash_mapping": "UNKNOWN",
            "embedded_component_validation": "VERIFIED" if squashfs and uimage else "BLOCKED",
        },
        "rootfs": rootfs_evidence(rootfs),
        "deployment": {
            "rootfs_only_oem_update": "UNKNOWN",
            "same_layout_experimental_replacement": "PARTIALLY VERIFIED",
            "additional_userspace_without_rootfs_replacement": "PARTIALLY VERIFIED",
            "oem_signature_acceptance": "UNKNOWN",
            "physical_mtd_access": "BLOCKED_BY_POLICY",
        },
        "safety": {"executed_oem_binary": False, "opened_mtd": False, "wrote_flash": False,
                    "modified_input_firmware": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("firmware", type=Path)
    parser.add_argument("rootfs", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    if not args.firmware.is_file() or not args.rootfs.is_dir():
        parser.error("firmware must be a file and rootfs must be an extracted directory")
    result = collect(args.firmware, args.rootfs)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
