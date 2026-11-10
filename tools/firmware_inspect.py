#!/usr/bin/env python3
"""Read-only inspector for common Huawei/Broadcom firmware container markers.

This is an initial triage tool, not a complete Huawei firmware unpacker.
It does not execute extracted code, modify the input, or produce flashable images.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

UIMAGE_MAGIC = b"\x27\x05\x19\x56"
SQUASHFS_LE_MAGIC = b"hsqs"
SQUASHFS_BE_MAGIC = b"qshs"
UIMAGE_HEADER_SIZE = 64


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return offsets
        offsets.append(pos)
        start = pos + 1


def parse_uimage(data: bytes, offset: int) -> dict[str, Any]:
    if offset < 0 or offset + UIMAGE_HEADER_SIZE > len(data):
        return {"offset": offset, "valid_header_bounds": False}

    header = data[offset : offset + UIMAGE_HEADER_SIZE]
    fields = struct.unpack(">7I4B32s", header)
    (
        magic, header_crc, timestamp, image_size, load, entry,
        data_crc, os_id, arch_id, image_type, compression, name,
    ) = fields
    header_for_crc = bytearray(header)
    header_for_crc[4:8] = b"\x00\x00\x00\x00"
    computed_header_crc = zlib.crc32(header_for_crc) & 0xFFFFFFFF

    payload_start = offset + UIMAGE_HEADER_SIZE
    payload_end = payload_start + image_size
    payload_bounds_valid = payload_end <= len(data)
    computed_data_crc = None
    if payload_bounds_valid:
        computed_data_crc = zlib.crc32(data[payload_start:payload_end]) & 0xFFFFFFFF

    return {
        "offset": offset,
        "magic": f"0x{magic:08x}",
        "header_crc_expected": f"0x{header_crc:08x}",
        "header_crc_computed": f"0x{computed_header_crc:08x}",
        "header_crc_valid": header_crc == computed_header_crc,
        "timestamp_unix": timestamp,
        "image_size": image_size,
        "load_address": f"0x{load:08x}",
        "entry_point": f"0x{entry:08x}",
        "data_crc_expected": f"0x{data_crc:08x}",
        "data_crc_computed": (
            f"0x{computed_data_crc:08x}" if computed_data_crc is not None else None
        ),
        "data_crc_valid": (
            data_crc == computed_data_crc if computed_data_crc is not None else False
        ),
        "os_id": os_id,
        "arch_id": arch_id,
        "image_type": image_type,
        "compression": compression,
        "name": name.split(b"\x00", 1)[0].decode("ascii", "replace"),
        "payload_start": payload_start,
        "payload_end": payload_end,
        "payload_bounds_valid": payload_bounds_valid,
    }


def inspect(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    result: dict[str, Any] = {
        "file": path.name,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "signatures": {
            "squashfs_le": [hex(x) for x in find_all(data, SQUASHFS_LE_MAGIC)],
            "squashfs_be": [hex(x) for x in find_all(data, SQUASHFS_BE_MAGIC)],
            "uimage": [hex(x) for x in find_all(data, UIMAGE_MAGIC)],
        },
    }
    result["uimages"] = [
        parse_uimage(data, offset) for offset in find_all(data, UIMAGE_MAGIC)
    ]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="local firmware image to inspect")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    if not args.image.is_file():
        parser.error(f"file does not exist: {args.image}")
    try:
        report = inspect(args.image)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"File: {report['file']}")
        print(f"Size: {report['size_bytes']} bytes")
        print(f"SHA-256: {report['sha256']}")
        for kind, offsets in report["signatures"].items():
            print(f"{kind}: {', '.join(offsets) if offsets else 'not found'}")
        for image in report["uimages"]:
            print(f"\nuImage at {hex(image['offset'])}: {image['name']}")
            print(f"  payload size: {image['image_size']}")
            print(f"  header CRC valid: {image['header_crc_valid']}")
            print(f"  data CRC valid: {image['data_crc_valid']}")
            print(f"  load / entry: {image['load_address']} / {image['entry_point']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
