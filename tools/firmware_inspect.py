#!/usr/bin/env python3
"""Read-only structural inspector for Huawei HG630-family firmware packages."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any

UIMAGE_MAGIC = 0x27051956
SQUASHFS_MAGIC = b"hsqs"


def find_all(data: bytes, marker: bytes) -> list[int]:
    offsets, start = [], 0
    while True:
        offset = data.find(marker, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def parse_uimage(data: bytes, offset: int) -> dict[str, Any]:
    if offset + 64 > len(data):
        raise ValueError("Truncated uImage header")
    f = struct.unpack(">7I4B32s", data[offset:offset + 64])
    magic, hcrc, timestamp, size, load, entry, dcrc, osid, arch, kind, comp, raw_name = f
    if magic != UIMAGE_MAGIC:
        raise ValueError("Invalid uImage magic")
    header = bytearray(data[offset:offset + 64])
    header[4:8] = b"\0" * 4
    payload_start, payload_end = offset + 64, offset + 64 + size
    if payload_end > len(data):
        raise ValueError("uImage payload extends beyond input file")
    payload = data[payload_start:payload_end]
    return {
        "offset": offset, "header_size": 64, "timestamp": timestamp,
        "payload_size": size, "payload_offset": payload_start, "payload_end": payload_end,
        "load_address": load, "entry_address": entry,
        "header_crc32": f"{hcrc:08x}", "data_crc32": f"{dcrc:08x}",
        "header_crc_valid": (zlib.crc32(header) & 0xffffffff) == hcrc,
        "data_crc_valid": (zlib.crc32(payload) & 0xffffffff) == dcrc,
        "os_id": osid, "architecture_id": arch, "image_type_id": kind,
        "compression_id": comp,
        "name": raw_name.split(b"\0", 1)[0].decode("ascii", "replace"),
    }


def parse_squashfs(data: bytes, offset: int) -> dict[str, Any]:
    if offset + 96 > len(data):
        raise ValueError("Truncated SquashFS superblock")
    f = struct.unpack_from("<5I6H2Q5Q", data, offset)
    (magic, inodes, mkfs, block, fragments, compression, block_log, flags,
     no_ids, major, minor, root_inode, bytes_used, id_start, xattr_start,
     inode_start, dir_start, frag_start) = f
    if magic != 0x73717368:
        raise ValueError("Invalid SquashFS magic")
    return {
        "offset": offset, "version": f"{major}.{minor}", "inode_count": inodes,
        "mkfs_time": mkfs, "block_size": block, "fragment_count": fragments,
        "compression_id": compression, "block_log": block_log, "flags": flags,
        "id_count": no_ids, "bytes_used": bytes_used,
        "filesystem_end": offset + bytes_used,
        "filesystem_within_input": offset + bytes_used <= len(data),
        "inode_table_start_relative": inode_start,
        "directory_table_start_relative": dir_start,
    }


# Observed in HG630 V2 V100R001C298B010. This is a narrowly scoped parser,
# not a claim that all Huawei packages share this container format.
HUAWEI_PACKAGE_MAGIC = b"\x10\x32\x54\x76"
HG630_COMPONENT_TABLE_OFFSET = 0x7C
HG630_COMPONENT_RECORD_SIZE = 44
HG630_COMPONENT_COUNT = 4


def parse_hg630_component_table(data: bytes) -> dict[str, Any]:
    """Parse the four observed big-endian component records in this HG630 package."""
    if len(data) < HG630_COMPONENT_TABLE_OFFSET + HG630_COMPONENT_RECORD_SIZE * HG630_COMPONENT_COUNT:
        raise ValueError("Truncated HG630 component table")
    if data[:4] != HUAWEI_PACKAGE_MAGIC:
        raise ValueError("Unrecognized HG630 package magic")
    records = []
    for index in range(HG630_COMPONENT_COUNT):
        offset = HG630_COMPONENT_TABLE_OFFSET + index * HG630_COMPONENT_RECORD_SIZE
        kind, component_id, payload_offset, payload_size, raw_name = struct.unpack_from(
            ">HHII32s", data, offset
        )
        name = raw_name.split(b"\\0", 1)[0].decode("ascii", "replace")
        if not name or payload_size == 0:
            raise ValueError(f"Invalid HG630 component record {index}")
        end = payload_offset + payload_size
        if end > len(data):
            raise ValueError(f"HG630 component {name} extends beyond package")
        records.append({
            "record_offset": offset,
            "type": kind,
            "component_id": component_id,
            "payload_offset": payload_offset,
            "payload_size": payload_size,
            "payload_end": end,
            "name": name,
        })
    for previous, current in zip(records, records[1:]):
        if previous["payload_end"] != current["payload_offset"]:
            raise ValueError("HG630 component payloads are not contiguous")
    return {
        "format_scope": "observed HG630 V2 V100R001C298B010 package only",
        "table_offset": HG630_COMPONENT_TABLE_OFFSET,
        "record_size": HG630_COMPONENT_RECORD_SIZE,
        "record_count": HG630_COMPONENT_COUNT,
        "records": records,
        "trailing_bytes_after_components": len(data) - records[-1]["payload_end"],
    }


def inspect(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    out: dict[str, Any] = {
        "file": path.name, "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "squashfs": [], "uimage": [], "markers": {},
    }
    if data.startswith(HUAWEI_PACKAGE_MAGIC):
        try:
            out["hg630_component_table"] = parse_hg630_component_table(data)
        except ValueError as exc:
            out["hg630_component_table"] = {"error": str(exc)}
    for off in find_all(data, SQUASHFS_MAGIC):
        try:
            out["squashfs"].append(parse_squashfs(data, off))
        except (ValueError, struct.error) as exc:
            out["squashfs"].append({"offset": off, "error": str(exc)})
    for off in find_all(data, struct.pack(">I", UIMAGE_MAGIC)):
        try:
            out["uimage"].append(parse_uimage(data, off))
        except (ValueError, struct.error) as exc:
            out["uimage"].append({"offset": off, "error": str(exc)})
    for marker in (b"board_id=", b"hgw_softversion=", b"HG630V2", b"Linux-2.6.30"):
        out["markers"][marker.decode()] = [f"0x{x:x}" for x in find_all(data, marker)]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("firmware", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.firmware.is_file():
        ap.error(f"input file does not exist: {args.firmware}")
    report = inspect(args.firmware)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
