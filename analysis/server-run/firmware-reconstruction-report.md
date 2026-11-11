# HG630 V2 firmware reconstruction audit

Status: `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`.

## Scope

This report records the verified package layout and the guarded reconstruction workflow. The owner-provided OEM package was inspected locally; the firmware binary is intentionally not committed to this repository.

OEM input:
- Filename: `HG630V2-12V100R001.bin`
- Size: `7,563,600` bytes
- SHA-256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`
- Product/version strings: `HG630 V2`, `V100R001C298B010`

## Verified package layout

| Region | Start | End (exclusive) | Size |
|---|---:|---:|---:|
| Huawei package prefix/container metadata | `0x000000` | `0x0305CF` | 198,095 |
| SquashFS RootFS slot | `0x0305CF` | `0x5D85CF` | 5,931,008 |
| Original uImage + trailing bytes | `0x5D85CF` | `0x736950` | 1,434,497 |

The original SquashFS superblock reports:
- SquashFS 4.0, little-endian
- XZ compression ID 4
- 1 MiB blocks
- 1,257 inodes and 14 fragments
- `bytes_used = 5,930,917`
- Filesystem end: `0x5D8574`
- Gap from filesystem end to uImage start: **91 bytes**

The original uImage:
- Header at `0x5D85CF`
- Header size: 64 bytes
- Payload size: 1,434,088 bytes
- Payload ends at `0x7367F7`
- 345 trailing bytes remain after the uImage
- Name: `Linux-2.6.30`
- Load and entry address: `0x81208000`
- Header CRC32 and payload CRC32 both validate

The package prefix begins with magic bytes `10 32 54 76`. An observed four-record component table begins at `0x7C`; each record is 44 bytes and decodes as big-endian `type:u16, component_id:u16, payload_offset:u32, payload_size:u32, name[32]`. The four contiguous records are: component 17 at `0x5CF` size `0x20000`; component 3 at `0x205CF` size `0x10000`; RootFS component 1 at `0x305CF` size `0x5A8000`; and kernel component 2 at `0x5D85CF` size `0x15E228`. These values match the observed payload boundaries. The parser is intentionally scoped to this HG630 V2 package; meanings beyond the observed IDs/names are not assumed. The header fields before the table and their checksum semantics remain unknown.

## Reconstruction implementation

Added `tools/rebuild_firmware.py`. It is deliberately conservative:

1. Requires the exact known OEM SHA-256 and package size by default.
2. Checks SquashFS magic and uImage magic at the verified offsets.
3. Checks the candidate is SquashFS 4.0, XZ compression ID 4, 1 MiB blocks, OEM-compatible flags, and fits the reserved RootFS span by both file size and internal `bytes_used`.
4. Requires the recorded winning RootFS SHA-256 `1f0760422f5f94b5da8ad7670725e1c2fc6fe0134d6649b96e5f2a2dbca2515e` by default.
5. Replaces only bytes `[0x305CF, 0x5D85CF)`.
6. Zero-fills unused bytes inside that reserved RootFS slot.
7. Preserves the complete package prefix and every byte from the original kernel offset through EOF.
8. Re-parses the uImage and verifies its header and payload CRCs remain valid.
9. Writes a JSON report alongside the output and marks the result `EXPERIMENTAL_NON_FLASHABLE`.

The tool refuses to overwrite either input or an existing output. It performs a full `unsquashfs` extraction check by default; optionally, `--expected-rootfs` compares every path, type, mode, UID/GID, timestamp, file hash/size, symlink target and device number against the expected staged RootFS.

Example (run on the build host where the original and winning candidate artifacts exist):

```bash
python3 tools/rebuild_firmware.py \
  /home/ayad/firmware-input/HG630V2-12V100R001.bin \
  /path/to/winning/rootfs.squashfs \
  --expected-rootfs /path/to/winning/stage-rootfs \
  --output /home/ayad/build-output/custom-build/HG630V2-OpenLinux-RESEARCH-ONLY.bin
```

Adjust only the candidate and staged-tree paths to the actual winning run. Verify the candidate SHA-256 against the recorded winning artifact before using it.

## What this does NOT establish

The reconstruction tool does not recalculate or claim to understand:
- Huawei package-level checksums in the prefix
- package signatures or authentication coverage
- updater acceptance, anti-rollback, or model/revision checks
- flash partition mapping or erase geometry
- target-kernel SquashFS mount behavior
- boot behavior, DSL operation, or hardware compatibility
- a safe recovery procedure

Preserving an unknown signature while changing RootFS bytes may invalidate that signature. Conversely, not finding a documented checksum does not prove there is none. The package prefix is preserved byte-for-byte, but package authentication remains unresolved.

**Do not flash the output.** A valid SquashFS, unchanged uImage CRC, unchanged prefix/kernel bytes, and successful host extraction are necessary structural checks only; they do not prove that the OEM updater accepts the package or that the router can boot it.

## Current conclusion

A deterministic, size-fitting RootFS exists and can be inserted into the original package's reserved RootFS slot without changing the OEM package prefix or original kernel/trailing region. This is now mechanically reproducible with an auditable tool. The resulting package remains research-only until Huawei container validation/authentication, updater acceptance, target boot, and a verified recovery path are established.
