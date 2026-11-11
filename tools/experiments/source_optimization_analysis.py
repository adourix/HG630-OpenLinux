#!/usr/bin/env python3
"""Test comment/blank-line removal as a behavior-preserving source optimization."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def strip_nonsemantic_lines(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = source.read_text().splitlines(True)
    kept = [line for index, line in enumerate(lines) if not (line.strip() == "" or (line.lstrip().startswith("#") and not (index == 0 and line.startswith("#!"))))]
    destination.write_text("".join(kept)
    )
    shutil.copystat(source, destination, follow_symlinks=False)


def make_variant(overlay: Path, destination: Path) -> None:
    for source in sorted(overlay.rglob("*")):
        relative = source.relative_to(overlay)
        target = destination / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            shutil.copystat(source, target, follow_symlinks=False)
        elif source.is_file():
            strip_nonsemantic_lines(source, target)


def execute(script: Path, root: Path, *args: str, extra: dict[str, str] | None = None) -> dict[str, object]:
    environment = os.environ.copy()
    environment.update({"OPENLINUX_ROOT": str(root), "OPENLINUX_LOG": str(root / "var/log/test.log")})
    if extra:
        environment.update(extra)
    process = subprocess.run(["sh", str(script), *args], env=environment, text=True, capture_output=True, check=False)
    def normalize(value: str) -> str:
        return value.replace(str(root), "<ROOT>")
    return {"returncode": process.returncode, "stdout": normalize(process.stdout), "stderr": normalize(process.stderr), "files": {str(path.relative_to(root)): normalize(path.read_text(errors="replace")) for path in sorted(root.rglob("*")) if path.is_file()}}


def cases(root: Path, variant: Path) -> dict[str, dict[str, object]]:
    ctl = variant / "usr/sbin/openlinuxctl"
    config_text = """SERVICE_NETWORK=disabled
SERVICE_DNS=disabled
SERVICE_SSH=disabled
SERVICE_FIREWALL=disabled
SERVICE_WEB=disabled
NETWORK_LAN_IFACE=br0
NETWORK_LAN_MODE=static
NETWORK_LAN_ADDRESS=192.168.1.1
NETWORK_LAN_NETMASK=255.255.255.0
NETWORK_WAN_IFACE=eth0
NETWORK_WAN_MODE=dhcp
DHCP_ENABLE=enabled
DHCP_START=192.168.1.100
DHCP_END=192.168.1.200
DHCP_LEASE_SECONDS=86400
DNS_DOMAIN=lan
FIREWALL_BACKEND=auto
SSH_ENABLE=disabled
SSH_BIND=192.168.1.1
LOG_LEVEL=info
LOG_MAX_BYTES=128
"""
    config = root / "etc/openlinux/openlinux.conf"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(config_text)
    results = {
        "status": execute(ctl, root, "status"),
        "network-dry-run": execute(ctl, root, "network", "apply", "--dry-run"),
        "boot": execute(ctl, root, "boot"),
    }
    config.write_text(config_text.replace("NETWORK_LAN_IFACE=br0", "NETWORK_LAN_IFACE=bad iface"))
    results["invalid-config"] = execute(ctl, root, "network", "validate")
    config.write_text(config_text)
    results["dhcp"] = execute(ctl, root, "dhcp", "validate")
    network = variant / "usr/libexec/openlinux-services/network"
    results["network-script"] = execute(network, root)
    results["network-apply-requested"] = execute(network, root, extra={"OPENLINUX_APPLY_NETWORK": "1"})
    return results


def run(overlay: Path, output: Path) -> dict[str, object]:
    overlay, output = overlay.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to reuse output: {output}")
    output.mkdir(parents=True)
    variant = output / "comment-stripped-overlay"
    make_variant(overlay, variant)
    original_bytes = sum(p.stat().st_size for p in overlay.rglob("*") if p.is_file())
    stripped_bytes = sum(p.stat().st_size for p in variant.rglob("*") if p.is_file())
    with tempfile.TemporaryDirectory(prefix="openlinux-behavior-") as first, tempfile.TemporaryDirectory(prefix="openlinux-behavior-") as second:
        original_results = cases(Path(first), overlay)
        stripped_results = cases(Path(second), variant)
    equal = original_results == stripped_results
    report = {"schema": 1, "source": str(overlay), "variant": str(variant), "original_source_bytes": original_bytes, "stripped_source_bytes": stripped_bytes, "source_reduction": original_bytes - stripped_bytes, "behavior_equal": equal, "original": original_results, "stripped": stripped_results}
    (output / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.overlay, args.output)
    print(json.dumps({"behavior_equal": result["behavior_equal"], "source_reduction": result["source_reduction"]}, indent=2))
    return 0 if result["behavior_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
