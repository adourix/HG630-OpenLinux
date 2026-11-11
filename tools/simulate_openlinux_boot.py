#!/usr/bin/env python3
"""Simulate the observed OEM sysinit followed by the isolated OpenLinux hook."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def sysinit_path(root: Path) -> Path:
    for line in (root / "etc/inittab").read_text().splitlines():
        if line.startswith("::sysinit:"):
            command = line.split(":", 3)[3].strip()
            if command.startswith("/") and " " not in command:
                return root / command.lstrip("/")
    raise ValueError("no simple sysinit entry found in etc/inittab")


def simulate(root: Path, enabled: bool, timeout: int = 10, ctl: Path | None = None) -> dict[str, object]:
    root = root.resolve()
    env = os.environ.copy()
    env.update({"OPENLINUX_ROOT": str(root), "OPENLINUX_TIMEOUT": str(timeout)})
    if (root / "bin/busybox").exists():
        env["PATH"] = ":".join(str(root / item) for item in ("bin", "sbin", "usr/bin", "usr/sbin"))
        env["QEMU_LD_PREFIX"] = str(root)
    if ctl is not None:
        env["OPENLINUX_CTL"] = str(ctl.resolve())
    sysinit = sysinit_path(root)
    oem = subprocess.run(["/bin/sh", str(sysinit)], cwd=root, env=env, text=True, capture_output=True, check=False)
    result: dict[str, object] = {
        "sysinit": str(sysinit),
        "oem_returncode": oem.returncode,
        "oem_stdout": oem.stdout,
        "oem_stderr": oem.stderr,
        "openlinux_enabled": enabled,
        "openlinux_attempted": False,
        "openlinux_returncode": None,
        "oem_failure_isolated": False,
    }
    if not enabled:
        result["oem_failure_isolated"] = oem.returncode == 0
        return result
    hook = root / "etc/init.d/openlinux"
    result["openlinux_attempted"] = True
    hook_run = subprocess.run(["/bin/sh", str(hook)], cwd=root, env=env, text=True, capture_output=True, check=False, timeout=timeout + 3)
    result["openlinux_returncode"] = hook_run.returncode
    result["openlinux_stdout"] = hook_run.stdout
    result["openlinux_stderr"] = hook_run.stderr
    result["oem_failure_isolated"] = oem.returncode == 0 and hook_run.returncode == 0
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rootfs", type=Path)
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--ctl", type=Path)
    args = parser.parse_args()
    print(json.dumps(simulate(args.rootfs, args.enabled, args.timeout, args.ctl), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
