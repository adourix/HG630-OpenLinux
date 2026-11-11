#!/usr/bin/env python3
"""Inspect ARM ELF ABI evidence without executing or modifying firmware files."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

EF_ARM_ABI_FLOAT_SOFT = 0x00000200
EF_ARM_ABI_FLOAT_HARD = 0x00000400
EM_ARM = 40
SHT_ARM_ATTRIBUTES = 0x70000003
TAG_ABI_HARDFP_USE = 27
TAG_ABI_VFP_ARGS = 28


def _uleb(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    raise ValueError("truncated ULEB128")


def parse_arm_attributes(data: bytes) -> dict[str, object]:
    """Decode the AEABI tags relevant to float calling convention."""
    result: dict[str, object] = {"format": None, "vendor": None, "tags": {}}
    if not data:
        return result
    if data[0:1] != b"A":
        result["error"] = "invalid ARM attributes format"
        return result
    result["format"] = 1
    offset = 1
    tags: dict[str, object] = {}
    try:
        while offset + 4 <= len(data):
            subsection_start = offset
            subsection_length = struct.unpack_from("<I", data, offset)[0]
            if subsection_length < 5 or subsection_start + subsection_length > len(data):
                raise ValueError("invalid ARM attributes subsection length")
            offset += 4
            vendor_end = data.index(b"\0", offset, subsection_start + subsection_length)
            result["vendor"] = data[offset:vendor_end].decode("ascii", "replace")
            offset = vendor_end + 1
            end = subsection_start + subsection_length
            while offset + 4 <= end:
                file_length = struct.unpack_from("<I", data, offset)[0]
                file_start = offset
                if file_length < 4 or file_start + file_length > end:
                    raise ValueError("invalid ARM attributes file subsection length")
                offset += 4
                while offset < file_start + file_length:
                    tag, offset = _uleb(data, offset)
                    if tag in (TAG_ABI_HARDFP_USE, TAG_ABI_VFP_ARGS):
                        value, offset = _uleb(data, offset)
                        tags[str(tag)] = value
                    elif offset < file_start + file_length:
                        if tag in (4, 5, 32, 34, 36, 65):
                            end_string = data.index(b"\0", offset, file_start + file_length)
                            offset = end_string + 1
                        else:
                            _, offset = _uleb(data, offset)
                offset = file_start + file_length
            offset = end
    except (ValueError, IndexError) as exc:
        result["error"] = str(exc)
    result["tags"] = tags
    return result


def _arm_attributes_from_elf(data: bytes, endian: str, elf_class: int) -> bytes | None:
    if elf_class != 1 or len(data) < 52:
        return None
    prefix = "<" if endian == "little" else ">"
    e_shoff = struct.unpack_from(prefix + "I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from(prefix + "HHH", data, 46)
    if not e_shoff or not e_shnum or e_shentsize < 40 or e_shstrndx >= e_shnum:
        return None
    sections = []
    for index in range(e_shnum):
        start = e_shoff + index * e_shentsize
        if start + 40 > len(data):
            return None
        sections.append(struct.unpack_from(prefix + "IIIIIIIIII", data, start))
    strtab = sections[e_shstrndx]
    names = data[strtab[4]:strtab[4] + strtab[5]]
    for section in sections:
        name_offset, section_type, section_offset, section_size = section[0], section[1], section[4], section[5]
        name_end = names.find(b"\0", name_offset)
        name = names[name_offset:name_end] if name_offset < len(names) and name_end >= 0 else b""
        if section_type == SHT_ARM_ATTRIBUTES or name == b".ARM.attributes":
            return data[section_offset:section_offset + section_size]
    return None


def classify_abi(e_flags: int | None, attributes: dict[str, object] | None) -> tuple[str | None, list[str]]:
    evidence: list[str] = []
    hard = bool(e_flags is not None and e_flags & EF_ARM_ABI_FLOAT_HARD)
    soft = bool(e_flags is not None and e_flags & EF_ARM_ABI_FLOAT_SOFT)
    if hard:
        evidence.append("e_flags: EF_ARM_ABI_FLOAT_HARD")
    if soft:
        evidence.append("e_flags: EF_ARM_ABI_FLOAT_SOFT")
    tags = (attributes or {}).get("tags", {})
    hardfp_use = tags.get(str(TAG_ABI_HARDFP_USE)) if isinstance(tags, dict) else None
    if hardfp_use is not None:
        evidence.append(f".ARM.attributes: Tag_ABI_HardFP_use={hardfp_use} (not a calling-convention decision)")
    vfp_args = tags.get(str(TAG_ABI_VFP_ARGS)) if isinstance(tags, dict) else None
    if vfp_args == 1:
        hard = True
        evidence.append(".ARM.attributes: Tag_ABI_VFP_args=VFP registers")
    elif vfp_args == 0:
        soft = True
        evidence.append(".ARM.attributes: Tag_ABI_VFP_args=Base AAPCS")
    if hard and soft:
        return None, evidence + ["conflicting hard/soft evidence"]
    if hard:
        return "hard", evidence
    if soft:
        return "soft", evidence
    return None, evidence


def inspect_elf(path: Path) -> dict[str, object]:
    result: dict[str, object] = {"path": str(path), "readelf": None, "abi": None, "abi_evidence": []}
    try:
        data = path.read_bytes()
        if data[:4] != b"\x7fELF" or len(data) < 20:
            result["error"] = "not an ELF file"
            return result
        elf_class = data[4]
        endian = "little" if data[5] == 1 else "big" if data[5] == 2 else None
        if elf_class != 1 or endian is None:
            result.update({"architecture": None, "raw_elf_flags": None, "abi": None})
            return result
        prefix = "<" if endian == "little" else ">"
        machine = struct.unpack_from(prefix + "H", data, 18)[0]
        e_flags = struct.unpack_from(prefix + "I", data, 36)[0]
        attributes_raw = _arm_attributes_from_elf(data, endian, elf_class)
        attributes = parse_arm_attributes(attributes_raw) if attributes_raw else None
        abi, evidence = classify_abi(e_flags, attributes)
        result.update({
            "architecture": "ARM" if machine == EM_ARM else f"machine-{machine}",
            "machine": "ARM" if machine == EM_ARM else f"machine-{machine}",
            "machine_id": machine, "class": "ELF32", "endianness": endian,
            "raw_elf_flags": f"0x{e_flags:08x}", "elf_flags": e_flags,
            "abi": abi, "abi_evidence": evidence, "arm_attributes": attributes,
        })
    except OSError as exc:
        result["error"] = str(exc)
    except (struct.error, ValueError) as exc:
        result["error"] = str(exc)
    return result


def detect(root: Path) -> dict[str, object]:
    elfs = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            try:
                if path.read_bytes()[:4] == b"\x7fELF":
                    elfs.append(inspect_elf(path))
            except OSError:
                continue
    hard = sum(x.get("abi") == "hard" for x in elfs)
    soft = sum(x.get("abi") == "soft" for x in elfs)
    unknown = len(elfs) - hard - soft
    recommendation = "arm-linux-gnueabihf" if hard and not soft and not unknown else "arm-linux-gnueabi" if soft and not hard and not unknown else "undetermined"
    return {
        "rootfs": str(root), "elf_count": len(elfs), "hard_float_elf_count": hard,
        "soft_float_elf_count": soft, "ambiguous_or_unknown_elf_count": unknown,
        "recommended_cross_prefix": recommendation,
        "basis": "direct ELF e_flags and .ARM.attributes evidence; no hardware assumptions",
        "elfs": elfs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rootfs", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    if not args.rootfs.is_dir():
        ap.error("rootfs directory does not exist")
    result = detect(args.rootfs)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "elfs"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
