# HG630 OpenLinux

Research and development project for a Linux-based firmware for **Huawei HG630 V2 (reported hardware revision VER.B)**, with preservation of the original DSL functionality as a hard requirement.

> **Status: RESEARCH ONLY — NOT FLASHABLE**
>
> This repository does not contain a firmware image and does not claim that OpenWrt or any custom image is currently compatible with the user's router. Do not flash experimental images. The original firmware and a verified recovery route must be retained.

## Project goals

1. Identify the exact board, SoC, RAM, flash geometry, bootloader and DSL subsystem.
2. Inspect the vendor firmware without modifying the router.
3. Identify the original DSL driver, firmware blobs, user-space daemon and kernel ABI dependencies.
4. Evaluate a maintainable Linux base: OpenWrt port if feasible, otherwise a minimal vendor-derived Linux userspace/kernel strategy.
5. Preserve DSL synchronization and PPPoE operation. Ethernet-WAN fallback is not the target.
6. Establish a tested recovery procedure before any device write.

## Confirmed device information supplied by the owner

| Field | Value | Evidence |
|---|---|---|
| Product | Huawei HG630 V2 | Router UI and firmware response |
| Hardware revision | VER.B | Router UI/API |
| Software version | V100R001C298B010 | Router UI/API |
| Firmware filename | HG630V2-12V100R001.bin | User supplied |
| Firmware package board field | `board_id=1212` | String found in image; exact semantics unverified |
| Kernel string | Linux-2.6.30 | uImage header |
| Filesystem marker | SquashFS little-endian at offset `0x305cf` | Binary inspection |
| uImage marker | Offset `0x5d85cf` | Binary inspection |

### Firmware image integrity metadata

- File size: `7,563,600` bytes
- SHA-256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`

The above hash identifies the exact binary examined during initial analysis. **Do not commit the firmware binary or router configuration backup**; those may contain proprietary code, credentials or personal network configuration. Keep local copies under an ignored directory.

## Important distinction: package board ID vs CFE board ID

The `board_id=1212` string found in the update package is not proof of the CFE board ID. A commonly documented HG630 platform identity is associated with Broadcom BCM63168 and board identifiers from related devices, but the exact VER.B PCB must be independently confirmed before using any device profile.

## Repository layout

- `docs/` — evidence, hardware notes, DSL feasibility and recovery requirements
- `tools/` — read-only firmware inspection utilities
- `analysis/` — generated local analysis output (do not commit vendor firmware)
- `firmware/original/` — local-only input location, ignored by Git
- `build/` — future reproducible build environment; no flashable target yet
- `tests/` — parser and metadata tests

## Initial workflow

```bash
python3 tools/firmware_inspect.py /path/to/HG630V2-12V100R001.bin --json
```

The inspector is read-only. It reports common image signatures and validates the legacy 64-byte U-Boot uImage header/data CRC when a candidate is present.

## Hard gates before any device flashing

- [ ] Exact PCB/SoC/board identity confirmed
- [ ] RAM and flash capacity confirmed from independent evidence
- [ ] Full flash map and erase geometry known
- [ ] Original DSL kernel module and user-space stack identified
- [ ] Driver/kernel ABI compatibility established
- [ ] Original flash dump or vendor recovery path verified
- [ ] Recovery tested independently (not merely assumed)
- [ ] Candidate image fits actual flash partitions
- [ ] DSL sync, VPI/VCI or PTM mode, PPPoE and routing tested

Until all applicable gates pass, this project must not generate or distribute a flashable image.

## Security and licensing

No credentials, serial numbers, configuration backups, private keys, or vendor firmware binaries belong in this repository. Respect the firmware's license and applicable redistribution restrictions. Prefer official GPL source releases and independently written tooling.

## Current conclusion

A firmware inspection and porting investigation is justified. A working DSL-preserving replacement firmware is **not yet demonstrated**. The main feasibility risk is the proprietary Broadcom DSL stack tied to the vendor's Linux 2.6.30 kernel and userspace ABI.

See [docs/FEASIBILITY.md](docs/FEASIBILITY.md) and [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md).

## Read-only firmware inspection tool

The repository includes a standalone Python parser for the vendor package container. It reports SquashFS and uImage candidates, hashes the input, and validates the legacy uImage CRCs. It does not extract proprietary content or create a flashable image.

Run:

```bash
python3 tools/firmware_inspect.py /path/to/HG630V2-12V100R001.bin --json
python3 -m unittest discover -s tests -v
```
