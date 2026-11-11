#!/usr/bin/env python3
"""Trace statically visible OEM upgrade signature paths.

This tool consumes preserved ARM ELF files and never executes them.  It combines
exported function ranges, direct ARM call sites, literal strings, and the
observable structure of the security wrappers.  Indirect GOT/function-pointer
calls are reported as unresolved instead of being guessed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools.analyze_upgrade_binary import analyze
except ModuleNotFoundError:  # direct execution from the tools directory
    from analyze_upgrade_binary import analyze


def file_strings(path: Path) -> list[dict]:
    data = path.read_bytes()
    result = []
    for match in re.finditer(rb"[ -~]{4,}\0", data):
        result.append({"file_offset": match.start(), "value": match.group()[:-1].decode("ascii", "replace")})
    return result


def symbol_ranges(report: dict, names: tuple[str, ...]) -> list[dict]:
    wanted = set(names)
    return [{"name": s["name"], "address": s["value"], "size": s["size"]}
            for s in report["dynamic_symbols"] if s["name"] in wanted and s["section"] != 0]


def calls_in(report: dict, start: int, size: int) -> list[dict]:
    return [call for call in report["calls"] if start <= call["site"] < start + size]


def make_report(upg_path: Path, msgapi_path: Path, cyassl_path: Path) -> dict:
    upg = analyze(upg_path)
    msg = analyze(msgapi_path)
    cyassl = analyze(cyassl_path)
    msg_strings = file_strings(msgapi_path)
    upg_strings = file_strings(upg_path)
    verify = symbol_ranges(msg, ("ATP_SEC_VerifyData", "ATP_SEC_VerifyDataEx"))
    context = symbol_ranges(msg, ("ATP_SEC_CreateSignatureContext",))
    security_calls = {
        name: upg["import_call_sites"].get(name, [])
        for name in ("ATP_SEC_VerifyData", "ATP_SEC_VerifyDataEx", "ATP_SEC_CreateSignatureContext", "ATP_SEC_KM_GetKey", "ATP_SEC_CreateData", "ATP_SEC_DeleteContext")
    }
    primitive_imports = sorted(name for name in msg["imports"] if name.startswith("CyaSSL_RSA_") or name.startswith("CyaSSL_SHA") or name.startswith("CyaSSL_MD5_"))
    paths = [item for item in msg_strings if item["value"] in ("/etc/root.pem", "/etc/servercert.pem", "/etc/serverkey.pem")]
    return {
        "tool": "analyze_upgrade_security.py",
        "inputs": {"upg": {"path": str(upg_path), "sha256": upg["input"]["sha256"]}, "libmsgapi": {"path": str(msgapi_path), "sha256": msg["input"]["sha256"]}, "libcyassl": {"path": str(cyassl_path), "sha256": cyassl["input"]["sha256"]}},
        "verified": {
            "upg_security_call_sites": security_calls,
            "wrapper_ranges": {"verify": verify, "signature_context": context},
            "verify_wrapper_direct_calls": [{"function": item["name"], "address": item["address"], "calls": calls_in(msg, item["address"], item["size"])} for item in verify],
            "signature_context_direct_calls": [{"function": item["name"], "address": item["address"], "calls": calls_in(msg, item["address"], item["size"])} for item in context],
            "crypto_primitive_imports": primitive_imports,
            "key_or_certificate_paths": paths,
            "upgrade_failure_strings": [item for item in upg_strings if any(word in item["value"].lower() for word in ("verify", "signature", "error"))],
        },
        "inferred": {
            "hash_algorithm": {"status": "INFERRED", "value": "SHA-256 candidate", "reason": "libmsgapi imports CyaSSL_SHA256_Init/Update/Final alongside security wrappers; direct resolution of the VerifyData context callback is unavailable."},
            "signature_family": {"status": "INFERRED", "value": "RSA candidate", "reason": "libmsgapi imports CyaSSL_RSA_verify, CyaSSL_RSA_size, and RSA key-management primitives."},
            "context_mode_constants": {"status": "VERIFIED", "values": [524288, 65536, 672, 4], "reason": "Immediate/loaded constants and stores are present in ATP_SEC_CreateSignatureContext; their public semantic names are unknown."},
        },
        "unknown": {
            "rsa_key_size": "UNKNOWN: CyaSSL_RSA_size is imported, but no verified result or fixed modulus length is exposed by the traced wrapper.",
            "signature_length_and_encoding": "UNKNOWN: no direct signature-buffer format or length field was resolved through the indirect context callback.",
            "padding_scheme": "UNKNOWN: RSA primitive presence does not distinguish PKCS#1 v1.5 from PSS.",
            "hashed_byte_range": "UNKNOWN: ATP_SEC_VerifyData adjusts caller length fields and calls ATP_SEC_DigestDataEx, but the ultimate callback arguments and header exclusions are unresolved.",
            "signature_storage": "UNKNOWN: no embedded public key/signature object was identified; certificate/key paths are runtime filesystem paths and are not proven firmware-update keys.",
            "failure_behavior": "INFERRED only: wrapper returns error values and `upg` contains Verify head/signature-related error strings; exact recovery/rollback actions remain unresolved.",
            "outer_container_checksum": "UNKNOWN: the existing firmware parser verifies embedded uImage header/data CRC32, but no OEM outer-container checksum or coverage has been identified.",
        },
        "reconstruction_requirements": {
            "verified": ["Preserve OEM metadata structure and embedded component ordering", "Produce valid uImage header/data CRC32 for changed kernel payloads", "Satisfy the linked security wrapper's runtime key and signature contract"],
            "inferred": ["A valid package likely needs RSA-family signature material and a SHA-256-compatible digest path"],
            "unknown": ["Exact signed byte range", "Signature encoding/padding and modulus size", "Outer checksum/authentication fields", "Exact section-to-MTD selection and acceptance policy"],
            "blocked": ["A flashable OEM update cannot be claimed without resolving unknown cryptographic and package-acceptance requirements; no signing-key bypass is authorized"],
        },
        "safety": "Static inspection only; no ARM executable, cryptographic operation, host MTD, or router was accessed.",
    }


def markdown(report: dict) -> str:
    v, i, u = report["verified"], report["inferred"], report["unknown"]
    lines = ["# OEM upgrade signature/security analysis", "", "## VERIFIED", "", "- The `upg` executable directly imports and calls the security wrapper family at the recorded call sites.", "- `ATP_SEC_VerifyData` has a checked-length path, calls `ATP_SEC_DigestDataEx`, and then dispatches through a context function pointer; the indirect target is not guessed.", "- `ATP_SEC_CreateSignatureContext` allocates 36 bytes, stores input fields and callback/context pointers, and selects mode-dependent constants including `0x80000`, `0x10000`, `672`, and `4`.", "- `libmsgapi.so` imports CyaSSL RSA, SHA-256, and MD5 primitives.", "- Static key/certificate path strings are: " + ", ".join(f"`{x['value']}`" for x in v["key_or_certificate_paths"]) + ".", "", "### Wrapper ranges", "", "| Function | Address | Size |", "|---|---:|---:|"]
    for group in (v["wrapper_ranges"]["verify"], v["wrapper_ranges"]["signature_context"]):
        for item in group:
            lines.append(f"| `{item['name']}` | `0x{item['address']:x}` | `{item['size']}` |")
    lines += ["", "## INFERRED", "", f"- Hash algorithm: **{i['hash_algorithm']['value']}** — {i['hash_algorithm']['reason']}", f"- Signature family: **{i['signature_family']['value']}** — {i['signature_family']['reason']}", "- Embedded uImage header and payload CRC32 are VERIFIED by the repository firmware validator; OEM outer-container checksum coverage remains UNKNOWN.", "", "## UNKNOWN / BLOCKED", ""]
    for name, value in u.items():
        lines.append(f"- `{name}`: {value}")
    lines += ["", "No private key is generated or extracted. This report does not bypass or weaken any signature check.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upg", type=Path, required=True)
    parser.add_argument("--msgapi", type=Path, required=True)
    parser.add_argument("--cyassl", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = make_report(args.upg, args.msgapi, args.cyassl)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown.write_text(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
