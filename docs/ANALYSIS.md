# Initial binary analysis

Input: owner-provided OEM update package, retained offline.

- Size: 7,563,600 bytes
- SHA-256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`
- Package magic: `10 32 54 76`
- Product/version strings: `HG630 V2`, `V100R001C298B010`
- Observed HG630 component table: four 44-byte big-endian records beginning at `0x7c`.
- RootFS component record: ID 1, offset `0x305cf`, size `0x5a8000` (5,931,008 bytes).
- Kernel component record: ID 2, offset `0x5d85cf`, size `0x15e228` (1,434,152 bytes).
- SquashFS little-endian marker at `0x305cf`: version 4.0, compression ID 4 (XZ), 1,257 inodes, 14 fragments, 1 MiB block size, bytes_used 5,930,917.
- uImage header at `0x5d85cf`; payload begins at `0x5d860f`, length 1,434,088 bytes.
- Kernel name: `Linux-2.6.30`; load and entry address `0x81208000`.
- uImage header CRC and payload CRC both validate.
- 91 bytes exist between SquashFS bytes_used end and the uImage header.
- uImage ends at `0x7367f7`; 345 bytes remain at EOF. The first 89 are zero and the final 256 are high-entropy bytes. They may be signature material, but this has not been proven.
- Package string `board_id=1212` is observed; it is not proven to equal the physical CFE board ID.

## Component table observed in this package

The four records at `0x7c`, `0xa8`, `0xd4`, and `0x100` decode as big-endian `type:u16, component_id:u16, payload_offset:u32, payload_size:u32, name[32]`:

| Component ID | Offset | Size | Name |
|---:|---:|---:|---|
| 17 | `0x5cf` | `0x20000` | `HG630V2V100R001C298B010` |
| 3 | `0x205cf` | `0x10000` | `v1.0` |
| 1 | `0x305cf` | `0x5a8000` | `HG630V2V100R001C298B010` |
| 2 | `0x5d85cf` | `0x15e228` | `HG630V2V100R001C298B010` |

These records are contiguous and match the observed RootFS and uImage boundaries. The parser is scoped to this specific HG630 package layout; the meaning of all header fields and component IDs is not generalized to other Huawei models.

## Layout arithmetic

The SquashFS region starts at decimal 198,095 and reports 5,930,917 bytes used, so its calculated end is 6,129,012 (`0x5d8574`). The uImage header begins at 6,129,103 (`0x5d85cf`), leaving 91 bytes between the declared filesystem end and the uImage header.

The uImage payload ends at 7,563,255 (`0x7367f7`), leaving 345 bytes to the end of the input file (7,563,600; `0x736950`).

## Reconstruction status

`tools/rebuild_firmware.py` now creates a research-only reconstruction by replacing only the RootFS component slot, preserving the package prefix and all bytes from the original kernel offset to EOF. It verifies the original package hash, observed component table, candidate SquashFS format/size, and original uImage CRCs.

It does **not** recalculate unknown Huawei package-level checksums or signatures. The last 256 bytes are only a signature candidate based on size and entropy; no signature format or verification key has been identified. Therefore the generated package is not established as updater-acceptable or flashable.

## What is not established

These package facts do not prove PCB identity, flash partition geometry, DSL silicon, or driver compatibility. This image is an OEM update package, not a confirmed full-chip dump. RootFS extraction and DSL stack inventory remain separate from package-level authentication and target boot validation.
