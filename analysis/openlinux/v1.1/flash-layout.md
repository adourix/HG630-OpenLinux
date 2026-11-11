# V1.1 flash-layout assessment

## Verified package map

| Component | Package location | Status |
|---|---:|---|
| Metadata inspection span | `0x000000..0x000600` | VERIFIED |
| SquashFS | `0x305cf`, 5,930,917 used bytes | VERIFIED |
| Gap | 91 bytes before `0x5d85cf` | VERIFIED; meaning UNKNOWN |
| uImage | `0x5d85cf..0x7368b6` | VERIFIED |
| Suffix | 345 bytes after uImage payload | VERIFIED; meaning UNKNOWN |

The metadata records include extents ending at `0xfd0000`, past the 7,563,600
byte package. They are therefore not treated as package offsets or physical
flash addresses.

## UNKNOWN

Physical flash part, capacity, erase size, MTD partition names/numbers, bootloader
and environment regions, calibration/NVRAM, board data, active/slave banks, and
the metadata-to-MTD mapping are all UNKNOWN. Static `/dev/mtd0`–`/dev/mtd15`
support in the vendor library proves an API range, not a partition map.

No physical MTD was opened and no partition map is inferred from package
metadata.
