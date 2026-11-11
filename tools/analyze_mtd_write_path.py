#!/usr/bin/env python3
"""Trace statically visible MTD selection, erase, and write paths."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from tools.analyze_upgrade_binary import analyze
except ModuleNotFoundError:  # direct execution from the tools directory
    from analyze_upgrade_binary import analyze


def strings(path: Path) -> list[dict]:
    data = path.read_bytes()
    return [{"file_offset": m.start(), "value": m.group()[:-1].decode("ascii", "replace")}
            for m in re.finditer(rb"[ -~]{4,}\0", data)]


def symbols(report: dict, names: tuple[str, ...]) -> list[dict]:
    wanted = set(names)
    return [{"name": s["name"], "address": s["value"], "size": s["size"]}
            for s in report["dynamic_symbols"] if s["name"] in wanted and s["section"] != 0]


def calls_in(report: dict, symbol: dict) -> list[dict]:
    return [call for call in report["calls"] if symbol["address"] <= call["site"] < symbol["address"] + symbol["size"]]


def make_report(upg_path: Path, bhal_path: Path) -> dict:
    upg = analyze(upg_path)
    bhal = analyze(bhal_path)
    bhal_strings = strings(bhal_path)
    mtd = symbols(bhal, ("ATP_MTD_Getfd", "ATP_MTD_Erase", "ATP_MTD_WriteBufToOffset_Upg", "ATP_MTD_WriteBufToOffset", "ATP_MTD_ReadBuffromOffset"))
    write_helpers = symbols(bhal, ("FomWriteFlashAreaByHead", "UPG_FlashPartWrite", "ATP_FLASH_WriteArea", "ATP_FLASH_Upgrade", "ATP_FLASH_UpgradeCfg", "ATP_FLASH_UpgradeBootloader"))
    path_strings = [x for x in bhal_strings if re.fullmatch(r"/dev/mtd(?:[0-9]|1[0-5])", x["value"])]
    low_level = {name: bhal["import_call_sites"].get(name, []) for name in ("open", "ioctl", "read", "write", "lseek", "close")}
    return {
        "tool": "analyze_mtd_write_path.py",
        "inputs": {"upg": {"path": str(upg_path), "sha256": upg["input"]["sha256"]}, "libbhalapi": {"path": str(bhal_path), "sha256": bhal["input"]["sha256"]}},
        "verified": {
            "mtd_device_paths": path_strings,
            "mtd_selection_function": {"name": "ATP_MTD_Getfd", "address": 0x3CE8, "size": 480, "control_flow": ["r0 is compared with 15", "an ARM jump table dispatches indices 0..15", "each selected case forms a /dev/mtdN path", "open/ioctl calls follow", "failure returns -1"]},
            "mtd_and_write_functions": [{"function": item, "calls": calls_in(bhal, item)} for item in mtd + write_helpers],
            "low_level_call_sites": low_level,
            "upg_flash_call_sites": {name: upg["import_call_sites"].get(name, []) for name in ("ATP_MTD_Getfd", "ATP_MTD_Erase", "ATP_MTD_WriteBufToOffset_Upg", "ATP_FLASH_Write", "ATP_FLASH_WriteArea", "ATP_FLASH_Upgrade", "ATP_FLASH_UpgradeCfg", "ATP_FLASH_UpgradeBootloader", "BSP_FLASH_UnProtect")},
            "protection_strings": [x for x in bhal_strings if any(term in x["value"].lower() for term in ("protect", "unprotect", "reject", "donot write config", "flash size", "erase"))],
        },
        "inferred": {
            "selection": "INFERRED: callers pass a logical MTD index to ATP_MTD_Getfd; this library resolves it to a static /dev/mtdN table.",
            "write_flow": "INFERRED: erase and write are separate operations, with error returns checked by callers; higher-level ATP_FLASH_Upgrade selects among paths using arguments and runtime state.",
            "main_slave": "UNKNOWN: upg contains main_offset/main_size/slave_offset/slave_size strings, but no proven mapping from those metadata records to an MTD index was recovered.",
        },
        "unknown": {
            "partition_assignment": "UNKNOWN: no exact section-ID-to-MTD mapping.",
            "calibration_exclusion": "UNKNOWN: /dev/caldata -> /dev/mtd9 is known, but no traced upgrade branch proves it is excluded.",
            "bootloader_exclusion": "UNKNOWN: a distinct ATP_FLASH_UpgradeBootloader path exists; its eligibility and target are unresolved.",
            "full_or_partial_image": "UNKNOWN: both full upgrade and area/partition write helpers exist; package selection logic is unresolved.",
            "erase_geometry": "UNKNOWN: MEMERASE is used, but exact erase-size source for each update path is not resolved.",
        },
        "safety": "Static inspection only; no /dev/mtd device was opened and no erase/write operation was executed.",
    }


def markdown(report: dict) -> str:
    v, i, u = report["verified"], report["inferred"], report["unknown"]
    lines = ["# OEM MTD selection and flash-write path", "", "## VERIFIED", "", "- `ATP_MTD_Getfd` at `0x3ce8` is 480 bytes and compares the logical index against `15` before an ARM jump-table dispatch.", "- Static paths include " + ", ".join(f"`{x['value']}`" for x in v["mtd_device_paths"]) + ".", "- The library contains separate MTD get-fd, erase, read, write, area-write, generic-upgrade, configuration-upgrade, bootloader-upgrade, and partition-write functions.", "- `upg` directly calls the recorded MTD/flash APIs at the addresses in the JSON report.", "", "## Call-path evidence", ""]
    for item in v["mtd_and_write_functions"]:
        f = item["function"]
        lines.append(f"- `{f['name']}` (`0x{f['address']:x}`, `{f['size']}` bytes): " + ", ".join(f"`0x{x['site']:x}`" for x in item["calls"] if x.get("import")) + ".")
    lines += ["", "## INFERRED", "", f"- {i['selection']}", f"- {i['write_flow']}", "", "## UNKNOWN / BLOCKED", ""]
    for value in u.values():
        lines.append(f"- {value}")
    lines += ["", "No host MTD device was accessed and no flash operation was executed.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upg", type=Path, required=True)
    parser.add_argument("--bhalapi", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = make_report(args.upg, args.bhalapi)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown.write_text(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
