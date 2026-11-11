#!/usr/bin/env python3
"""Build a deterministic, relocatable OpenLinux runtime scaffold archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import stat
import tarfile
import tempfile
from pathlib import Path


DEPENDENCIES = {
    "bin/openlinuxctl": ["/bin/sh", "date", "mkdir", "rmdir or /bin/busybox rmdir", "rm", "sleep", "kill", "/proc", "/dev/caldata"],
    "bin/openlinux-shutdown": ["/bin/sh"],
    "libexec/openlinuxd": ["/bin/sh", "date", "rm", "rmdir or /bin/busybox rmdir", "sleep", "/proc/uptime"],
    "sbin/openlinux-uninstall": ["/bin/sh", "rm", "rmdir or /bin/busybox rmdir"],
    "etc/openlinux.conf": [],
    ".openlinux-owner": [],
}
OWNER_RULES = {
    "package_files": "OpenLinux owns only the exact paths listed in manifest.json.",
    "runtime_state": "OpenLinux owns only var/run/openlinux.lock and var/log/openlinux-runtime.log.",
    "oem_files": "No ownership or write permission over OEM files, startup files, services, network state, or devices.",
    "manifest_self_hash": "manifest.json is listed with sha256=null to avoid a recursive self-hash.",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect(source: Path) -> list[dict]:
    if not source.is_dir():
        raise ValueError(f"runtime source directory does not exist: {source}")
    entries: list[dict] = []
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source).as_posix()
        if path.is_symlink():
            raise ValueError(f"symlinks are not allowed in runtime source: {rel}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"unsupported runtime source entry: {rel}")
        payload = path.read_bytes()
        entries.append({
            "path": rel,
            "sha256": sha256(payload),
            "size": len(payload),
            "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
            "dependencies": DEPENDENCIES.get(rel, []),
            "ownership": "OpenLinux package file",
        })
    expected = set(DEPENDENCIES)
    actual = {entry["path"] for entry in entries}
    if actual != expected:
        raise ValueError(f"runtime source file set mismatch; missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    if not any(item["path"] == ".openlinux-owner" and item["sha256"] == sha256(b"HG630-OPENLINUX-RUNTIME-V1\n") for item in entries):
        raise ValueError("runtime ownership marker is missing or invalid")
    return entries


def make_manifest(source: Path, entries: list[dict]) -> dict:
    package_entries = entries + [{
        "path": "manifest.json", "sha256": None, "size": None, "mode": "0644",
        "dependencies": [], "ownership": "OpenLinux package metadata; self-hash omitted",
    }]
    return {
        "format": "openlinux-runtime-package-v1",
        "target": "POSIX shell runtime scaffold; architecture independent; no compiled target payload",
        "classification": "RESEARCH_ONLY; no physical HG630 V2 compatibility claim",
        "network": {"default": "disabled", "bind_address_setting_present": True, "bind_address_used": False, "network_actions_implemented": False},
        "files": package_entries,
        "ownership_rules": OWNER_RULES,
        "runtime_requirements": {
            "shell": "/bin/sh",
            "vendor_readiness": "operator runs after /dev/caldata symlink exists and a /proc process comm entry equals mic",
            "filesystem": "chosen extraction directory must be writable; no fixed external storage path is assumed",
            "kernel_or_library_payload": "none included; this scaffold cannot replace a target-compatible OpenLinux service implementation",
        },
        "source_directory": "build/runtime",
    }


def _add_bytes(archive: tarfile.TarFile, name: str, data: bytes, mode: int) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = 0
    archive.addfile(info, io.BytesIO(data))


def build(source: Path, output: Path) -> dict:
    source = source.resolve()
    output = output.resolve()
    if output == source or source in output.parents:
        raise ValueError("output must be outside the runtime source tree")
    entries = collect(source)
    manifest = make_manifest(source, entries)
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".openlinux-runtime-", dir=output.parent, delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    dirs = {"openlinux"}
                    for entry in entries:
                        parent = Path(entry["path"]).parent
                        while parent.as_posix() != ".":
                            dirs.add(f"openlinux/{parent.as_posix()}")
                            parent = parent.parent
                    for directory in sorted(dirs, key=lambda value: (value.count("/"), value)):
                        info = tarfile.TarInfo(directory + "/")
                        info.type = tarfile.DIRTYPE
                        info.mode = 0o755
                        info.uid = info.gid = info.mtime = 0
                        info.uname = info.gname = "root"
                        archive.addfile(info)
                    for entry in entries:
                        name = entry["path"]
                        _add_bytes(archive, f"openlinux/{name}", (source / name).read_bytes(), int(entry["mode"], 8))
                    _add_bytes(archive, "openlinux/manifest.json", manifest_bytes, 0o644)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    data = output.read_bytes()
    return {"output": str(output), "size": len(data), "sha256": sha256(data), "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("build/runtime"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.source, args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
