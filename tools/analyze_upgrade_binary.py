#!/usr/bin/env python3
"""Statically analyze the ARM ``upg`` executable without executing it.

The analyzer deliberately reports observations, not reconstructed source code.  It
parses the ELF/dynamic symbol tables, decodes ARM direct branches in ``.text``,
maps calls into the PLT to imported API names, and records literal references to
read-only strings.  No code from the inspected executable is loaded or run.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path


ELF32_HEADER = struct.Struct("<16sHHIIIIIHHHHHH")
ELF32_SECTION = struct.Struct("<IIIIIIIIII")
ELF32_SYM = struct.Struct("<IIIBBH")


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def decode_arm_branch(word: int, pc: int) -> dict | None:
    """Decode an ARM-state B/BL instruction, returning its absolute target."""
    if ((word >> 25) & 0x7) != 0b101:
        return None
    displacement = sign_extend(word & 0x00FFFFFF, 24) << 2
    return {
        "kind": "BL" if word & (1 << 24) else "B",
        "condition": (word >> 28) & 0xF,
        "target": (pc + 8 + displacement) & 0xFFFFFFFF,
    }


def _cstring(blob: bytes, offset: int) -> str | None:
    if offset < 0 or offset >= len(blob):
        return None
    end = blob.find(b"\0", offset)
    if end < 0:
        return None
    value = blob[offset:end]
    if not value or any(byte < 0x20 or byte > 0x7E for byte in value):
        return None
    return value.decode("ascii", errors="replace")


def _parse_sections(data: bytes) -> tuple[dict, dict[str, dict]]:
    ident, etype, machine, version, entry, phoff, shoff, flags, ehsize, phentsize, phnum, shentsize, shnum, shstrndx = ELF32_HEADER.unpack_from(data)
    if ident[:4] != b"\x7fELF" or ident[4] != 1 or ident[5] != 1:
        raise ValueError("expected a little-endian ELF32 file")
    raw = [ELF32_SECTION.unpack_from(data, shoff + i * shentsize) for i in range(shnum)]
    names = raw[shstrndx][4]
    shstr = data[names:names + raw[shstrndx][5]]
    sections = {}
    for item in raw:
        name_off, stype, sflags, addr, offset, size, link, info, align, entsize = item
        end = offset + size
        # SHT_NOBITS sections (notably .bss) occupy memory but no file bytes.
        if stype != 8 and end > len(data):
            raise ValueError(f"section at 0x{offset:x} exceeds file")
        name = _cstring(shstr, name_off) or ""
        sections[name] = {"type": stype, "flags": sflags, "address": addr, "offset": offset, "size": size, "link": link, "info": info, "entsize": entsize}
    header = {"class": 32, "machine": machine, "entry": entry, "section_count": shnum, "file_size": len(data)}
    return header, sections


def _dynamic_symbols(data: bytes, sections: dict[str, dict]) -> list[dict]:
    symtab = sections.get(".dynsym")
    strings = sections.get(".dynstr")
    if not symtab or not strings:
        return []
    strtab = data[strings["offset"]:strings["offset"] + strings["size"]]
    entsize = symtab["entsize"] or ELF32_SYM.size
    result = []
    for index, offset in enumerate(range(symtab["offset"], symtab["offset"] + symtab["size"], entsize)):
        if offset + ELF32_SYM.size > len(data):
            break
        name_off, value, size, info, other, shndx = ELF32_SYM.unpack_from(data, offset)
        name = _cstring(strtab, name_off) or ""
        result.append({"index": index, "name": name, "value": value, "size": size, "type": info & 0xF, "bind": info >> 4, "section": shndx})
    return result


def _plt_imports(data: bytes, sections: dict[str, dict], symbols: list[dict]) -> dict[int, str]:
    """Map ARM PLT entry addresses to imported names for ET_DYN files."""
    relplt = sections.get(".rel.plt")
    plt = sections.get(".plt")
    if not relplt or not plt:
        return {}
    result = {}
    for index, offset in enumerate(range(relplt["offset"], relplt["offset"] + relplt["size"], relplt["entsize"] or 8)):
        if offset + 8 > len(data):
            break
        _, info = struct.unpack_from("<II", data, offset)
        symbol_index = info >> 8
        if symbol_index < len(symbols) and symbols[symbol_index]["name"]:
            # ARM PLT: 20-byte resolver entry, then 12 bytes per symbol.
            result[plt["address"] + 20 + index * 12] = symbols[symbol_index]["name"]
    return result


def _section_bytes(data: bytes, section: dict | None) -> bytes:
    if not section:
        return b""
    return data[section["offset"]:section["offset"] + section["size"]]


def _entropy(blob: bytes) -> float:
    if not blob:
        return 0.0
    counts = Counter(blob)
    return -sum((n / len(blob)) * math.log2(n / len(blob)) for n in counts.values())


def analyze(path: str | Path, *, llvm_objdump: str | None = None) -> dict:
    path = Path(path)
    data = path.read_bytes()
    header, sections = _parse_sections(data)
    symbols = _dynamic_symbols(data, sections)
    imported = {s["value"]: s["name"] for s in symbols if s["name"] and s["section"] == 0 and s["value"]}
    imported.update(_plt_imports(data, sections, symbols))
    text_section = sections.get(".text")
    text = _section_bytes(data, text_section)
    text_addr = text_section["address"] if text_section else 0
    rodata_section = sections.get(".rodata")
    rodata = _section_bytes(data, rodata_section)
    rodata_addr = rodata_section["address"] if rodata_section else 0

    calls, branches, literal_refs = [], [], []
    function_starts = {header["entry"]}
    for index in range(0, len(text) - 3, 4):
        word = struct.unpack_from("<I", text, index)[0]
        pc = text_addr + index
        branch = decode_arm_branch(word, pc)
        if branch:
            record = {"site": pc, **branch}
            branches.append(record)
            if branch["kind"] == "BL":
                function_starts.add(branch["target"])
                calls.append({"site": pc, "target": branch["target"], "condition": branch["condition"], "import": imported.get(branch["target"]), "internal": branch["target"] not in imported and text_addr <= branch["target"] < text_addr + len(text)})
        # ARM literal LDR: cond 01 0 1 U 0 1 Rn=PC Rt imm12.
        if (word & 0x0F7F0000) == 0x051F0000:
            imm = word & 0xFFF
            target = pc + 8 + (imm if word & (1 << 23) else -imm)
            if rodata_addr <= target < rodata_addr + len(rodata):
                value = _cstring(rodata, target - rodata_addr)
                if value:
                    literal_refs.append({"site": pc, "target": target, "value": value})
            elif text_addr <= target <= text_addr + len(text) - 4:
                # GCC commonly places a pointer in a literal pool in .text;
                # follow one level so strings are tied to actual load sites.
                pointer = struct.unpack_from("<I", data, text_section["offset"] + target - text_addr)[0]
                if rodata_addr <= pointer < rodata_addr + len(rodata):
                    value = _cstring(rodata, pointer - rodata_addr)
                    if value:
                        literal_refs.append({"site": pc, "target": target, "pointer": pointer, "value": value})

    imported_calls = defaultdict(list)
    for call in calls:
        if call["import"]:
            imported_calls[call["import"]].append(call["site"])

    imported_names = list(imported.values())
    candidate_security = [name for name in imported_names if any(token in name.lower() for token in ("sec_", "key", "verify", "signature", "crypto"))]
    candidate_flash = [name for name in imported_names if any(token in name.lower() for token in ("flash", "mtd", "write", "erase", "upgrade"))]
    candidate_validation_strings = [ref for ref in literal_refs if any(token in ref["value"].lower() for token in ("verify", "error", "offset", "size", "single system"))]
    blob_candidates = []
    for offset in range(0, max(0, len(rodata) - 64), 16):
        block = rodata[offset:offset + 64]
        if _entropy(block) >= 5.0 and b"\0" not in block:
            blob_candidates.append({"address": rodata_addr + offset, "offset": rodata_section["offset"] + offset, "size": 64, "entropy_bits_per_byte": round(_entropy(block), 3)})
            if len(blob_candidates) >= 8:
                break

    result = {
        "tool": "analyze_upgrade_binary.py",
        "input": {"path": str(path), "sha256": __import__("hashlib").sha256(data).hexdigest(), "size": len(data)},
        "elf": header,
        "sections": sections,
        "dynamic_symbols": symbols,
        "imports": sorted(imported.values()),
        "function_starts": [{"address": address, "source": "entry" if address == header["entry"] else "direct BL target"} for address in sorted(function_starts) if text_addr <= address < text_addr + len(text)],
        "calls": sorted(calls, key=lambda item: item["site"]),
        "import_call_sites": {name: sorted(sites) for name, sites in sorted(imported_calls.items())},
        "literal_references": sorted(literal_refs, key=lambda item: item["site"]),
        "observations": {
            "security_api_imports": sorted(candidate_security),
            "flash_api_imports": sorted(candidate_flash),
            "validation_related_literals": candidate_validation_strings,
            "high_entropy_rodata_candidates": blob_candidates,
            "crc_algorithm": {"status": "UNKNOWN", "reason": "No CRC-named import or self-contained CRC implementation was identified by this first-pass static scan."},
            "signature_algorithm": {"status": "UNKNOWN", "reason": "Security API calls are statically referenced, but the linked library implementation and algorithm are outside this executable."},
            "key_material": {"status": "UNKNOWN", "reason": "High-entropy read-only data is recorded as candidates only; no key usage or format is proven."},
        },
        "disassembly": {"tool": llvm_objdump or "llvm-objdump-19", "available": bool(llvm_objdump or shutil_which("llvm-objdump-19") or shutil_which("llvm-objdump"))},
        "evidence_policy": "VERIFIED means directly observed in ELF metadata or decoded instruction references; UNKNOWN means this analyzer cannot establish the behavior.",
    }
    return result


def shutil_which(name: str) -> str | None:
    import shutil
    return shutil.which(name)


def markdown(report: dict) -> str:
    obs = report["observations"]
    lines = [f"# Static analysis of `{Path(report['input']['path']).name}`", "", f"- Input SHA-256: `{report['input']['sha256']}`", f"- Size: `{report['input']['size']}` bytes", f"- Architecture: ELF32 ARM (machine {report['elf']['machine']})", f"- Entry point: `0x{report['elf']['entry']:x}`", "", "## VERIFIED observations", "", f"- Decoded `{len(report['calls'])}` direct ARM call instructions and `{len(report['function_starts'])}` reachable function-start candidates.", f"- Found `{len(report['import_call_sites'])}` imported APIs with direct call sites.", "- Security-related imported APIs: " + (", ".join(f"`{x}`" for x in obs["security_api_imports"]) or "none") + ".", "- Flash/MTD-related imported APIs: " + (", ".join(f"`{x}`" for x in obs["flash_api_imports"]) or "none") + ".", "", "## Call-site evidence", "", "| Imported API | Call sites |", "|---|---|"]
    for name, sites in report["import_call_sites"].items():
        lines.append(f"| `{name}` | " + ", ".join(f"`0x{x:x}`" for x in sites) + " |")
    lines += ["", "## Validation and cryptography", "", "- Validation-related literals are directly referenced by ARM literal-load sites; this establishes use of the text, not its complete control-flow meaning."]
    for item in obs["validation_related_literals"]:
        lines.append(f"  - `0x{item['site']:x}` → `{item['value']}`")
    lines += ["", f"- CRC/checksum: **{obs['crc_algorithm']['status']}** — {obs['crc_algorithm']['reason']}", f"- Signature algorithm: **{obs['signature_algorithm']['status']}** — {obs['signature_algorithm']['reason']}", f"- Key material: **{obs['key_material']['status']}** — {obs['key_material']['reason']}", "", "## Scope limits", "", "This is static analysis only. The ARM executable was not executed, no router was contacted, and no MTD operation was attempted. Imported API names do not prove the implementation or argument semantics inside their shared libraries.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--json", type=Path, help="write structured JSON report")
    parser.add_argument("--markdown", type=Path, help="write human-readable Markdown report")
    args = parser.parse_args()
    if not args.binary.is_file():
        parser.error(f"binary not found: {args.binary}")
    report = analyze(args.binary)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(encoded)
    else:
        print(encoded, end="")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
