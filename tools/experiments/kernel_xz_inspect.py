#!/usr/bin/env python3
"""Collect conservative, read-only XZ/SquashFS evidence from OEM artifacts."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


XZ_MAGIC = b"\xfd7zXZ\x00"


def inspect(image: Path, kernel: Path) -> dict[str, object]:
    image_bytes = image.read_bytes()
    kernel_bytes = kernel.read_bytes()
    offsets = []
    cursor = 0
    while True:
        offset = image_bytes.find(XZ_MAGIC, cursor)
        if offset < 0:
            break
        offsets.append(offset)
        cursor = offset + 1
    strings = subprocess.run(["strings", "-a", str(kernel)], check=True, capture_output=True, text=True).stdout.splitlines()
    interesting = sorted({line for line in strings if re.search(r"squashfs_xz|xz_dec|tbcj|arm.*bcj|bcj", line, re.I)})
    # SquashFS 4.0 superblock fields are little-endian at these offsets.
    block_size = int.from_bytes(image_bytes[12:16], "little")
    compression_id = int.from_bytes(image_bytes[20:22], "little")
    return {
        "image": str(image),
        "kernel": str(kernel),
        "squashfs": {"magic": image_bytes[:4].hex(), "block_size": block_size, "compression_id": compression_id, "xz_magic_count": len(offsets), "xz_stream_header_offsets": offsets[:64], "first_xz_header": image_bytes[offsets[0]:offsets[0] + 12].hex() if offsets else None},
        "kernel_strings": interesting,
        "claims": {"generic_xz_decoder_observed": any("xz_dec_init" in line or "xz_dec_run" in line for line in interesting), "squashfs_xz_glue_observed": any("squashfs_xz_init" in line for line in interesting), "bcj_registration_proven": False, "exact_dictionary_supported_proven": False, "stream_boundaries_recovered": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.image, args.kernel)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
