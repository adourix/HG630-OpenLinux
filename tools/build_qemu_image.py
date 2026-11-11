#!/usr/bin/env python3
"""Build a standalone ARM QEMU boot bundle from a kernel and static BusyBox."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


RC_S = r'''#!/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin
export PATH
mkdir -p /proc /sys /dev /var/log /tmp
mount -t proc proc /proc 2>/dev/null || :
mount -t sysfs sysfs /sys 2>/dev/null || :
mount -t devtmpfs devtmpfs /dev 2>/dev/null || :
echo "OPENLINUX V0.9 STANDALONE INIT"
echo "target=vexpress-a9"
echo "kernel=$(uname -a)"
echo "OPENLINUX STATUS BEGIN"
/usr/sbin/openlinuxctl status || echo "status=unavailable"
/usr/sbin/openlinuxctl monitor || echo "monitor=unavailable"
/usr/sbin/openlinuxctl logs status || echo "logs=unavailable"
echo "OPENLINUX STATUS END"
echo "OPENLINUX_READY"
exec /bin/sh
'''

INITTAB = """::sysinit:/etc/init.d/rcS
::respawn:-/bin/sh
"""

CONFIG = """SERVICE_NETWORK=disabled
SERVICE_DNS=disabled
SERVICE_SSH=disabled
SERVICE_FIREWALL=disabled
SERVICE_WEB=disabled
NETWORK_LAN_IFACE=eth0
NETWORK_LAN_MODE=disabled
NETWORK_LAN_ADDRESS=192.168.1.1
NETWORK_LAN_NETMASK=255.255.255.0
NETWORK_LAN_GATEWAY=
NETWORK_WAN_IFACE=eth0
NETWORK_WAN_MODE=disabled
NETWORK_WAN_ADDRESS=
NETWORK_WAN_NETMASK=
NETWORK_WAN_GATEWAY=
DHCP_ENABLE=disabled
DHCP_START=192.168.1.100
DHCP_END=192.168.1.200
DHCP_LEASE_SECONDS=86400
DNS_UPSTREAM=
DNS_DOMAIN=openlinux
FIREWALL_BACKEND=none
SSH_ENABLE=disabled
SSH_BIND=127.0.0.1
LOG_LEVEL=info
LOG_MAX_BYTES=65536
"""

APPLET_LINKS = ("sh", "awk", "cat", "cp", "date", "echo", "grep", "mkdir",
                "mount", "ps", "readlink", "sleep", "test", "uname", "uptime")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_inputs(kernel: Path, busybox: Path, openlinuxctl: Path, dtb: Path | None = None) -> None:
    for path in (kernel, busybox, openlinuxctl, dtb):
        if path is None:
            continue
        if not path.is_file():
            raise ValueError(f"missing input: {path}")
    if busybox.read_bytes()[:4] != b"\x7fELF":
        raise ValueError("BusyBox input is not ELF")
    if openlinuxctl.read_bytes()[:2] != b"#!":
        raise ValueError("openlinuxctl must be a shell script")


def make_initramfs(busybox: Path, openlinuxctl: Path, output: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="openlinux-v09-initramfs-") as temp:
        stage = Path(temp)
        for directory in ("bin", "dev", "etc/init.d", "etc/openlinux", "proc", "sys", "tmp", "usr/sbin", "var/log"):
            (stage / directory).mkdir(parents=True, exist_ok=True)
        shutil.copy2(busybox, stage / "bin/busybox")
        os.chmod(stage / "bin/busybox", 0o755)
        for applet in APPLET_LINKS:
            (stage / "bin" / applet).symlink_to("busybox")
        (stage / "init").symlink_to("bin/busybox")
        (stage / "etc/inittab").write_text(INITTAB)
        (stage / "etc/init.d/rcS").write_text(RC_S)
        os.chmod(stage / "etc/init.d/rcS", 0o755)
        shutil.copy2(openlinuxctl, stage / "usr/sbin/openlinuxctl")
        os.chmod(stage / "usr/sbin/openlinuxctl", 0o755)
        (stage / "etc/openlinux/openlinux.conf").write_text(CONFIG)
        (stage / "etc/hostname").write_text("openlinux-v09\n")
        listing = subprocess.run(["find", ".", "-print"], cwd=stage,
                                 check=True, capture_output=True, text=True).stdout
        cpio = subprocess.run(["cpio", "-o", "-H", "newc"], cwd=stage,
                              input=listing.encode(), capture_output=True, check=True)
        with gzip.open(output, "wb", compresslevel=9) as stream:
            stream.write(cpio.stdout)
    return {"path": str(output), "sha256": digest(output), "size": output.stat().st_size,
            "format": "gzip-compressed newc cpio initramfs"}


def build(kernel: Path, busybox: Path, openlinuxctl: Path, output: Path, dtb: Path | None = None) -> dict:
    validate_inputs(kernel, busybox, openlinuxctl, dtb)
    output.mkdir(parents=True, exist_ok=True)
    initramfs = output / "openlinux-v0.9-vexpress-a9.initramfs.cpio.gz"
    kernel_out = output / "openlinux-v0.9-vexpress-a9.zImage"
    shutil.copy2(kernel, kernel_out)
    init_report = make_initramfs(busybox, openlinuxctl, initramfs)
    dtb_report = None
    if dtb is not None:
        dtb_out = output / "openlinux-v0.9-vexpress-a9.dtb"
        shutil.copy2(dtb, dtb_out)
        dtb_report = {"path": str(dtb_out), "sha256": digest(dtb_out), "size": dtb_out.stat().st_size}
    manifest = {
        "status": "BOOTABLE_EMULATOR_TARGET",
        "target": {"machine": "vexpress-a9", "cpu": "ARMv7 Cortex-A9", "ram_mb": 256,
                    "console": "ttyAMA0,115200", "boot_protocol": "QEMU kernel + initramfs"},
        "inputs": {"kernel": {"path": str(kernel), "sha256": digest(kernel), "size": kernel.stat().st_size},
                   "busybox": {"path": str(busybox), "sha256": digest(busybox), "size": busybox.stat().st_size},
                   "openlinuxctl": {"path": str(openlinuxctl), "sha256": digest(openlinuxctl), "size": openlinuxctl.stat().st_size}},
        "artifacts": {"kernel": {"path": str(kernel_out), "sha256": digest(kernel_out), "size": kernel_out.stat().st_size},
                      "initramfs": init_report, "dtb": dtb_report},
        "command": "qemu-system-arm -M vexpress-a9 -m 256M -kernel openlinux-v0.9-vexpress-a9.zImage -dtb openlinux-v0.9-vexpress-a9.dtb -initrd openlinux-v0.9-vexpress-a9.initramfs.cpio.gz -append 'console=ttyAMA0,115200 rdinit=/init' -serial stdio -monitor none -display none -audio driver=none -no-reboot",
        "hardware_compatibility": "UNKNOWN; this target does not emulate HiSilicon SD5610x",
    }
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--busybox", type=Path, required=True)
    parser.add_argument("--openlinuxctl", type=Path, required=True)
    parser.add_argument("--dtb", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.kernel, args.busybox, args.openlinuxctl, args.output, args.dtb), indent=2, sort_keys=True))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
