# HG630 V2 flash layout evidence

## Status

**No physical flash map is verified.** The firmware metadata offers candidate extents only. The update package is 7,563,600 bytes (`0x736950`) and is smaller than the metadata extent (`0xfd0000`), so metadata offsets cannot all be direct offsets into this package.

## Metadata range arithmetic

Metadata records form several adjacent extents:

- `[20011]` main: `0x000000..0x020000` (128 KiB)
- `[20003]` main: `0x020000..0x030000` (64 KiB); slave: `0x030000..0x040000` (64 KiB)
- `[20002]` main: `0x040000..0x1a0000` (1.375 MiB); slave: `0x7c0000..0x920000` (1.375 MiB)
- `[20001]` main: `0x1a0000..0x7c0000` (6.125 MiB); slave: `0x920000..0xf40000` (6.125 MiB)
- `[20100]` and `[20101]` main: zero-size entries at `0xf40000`
- `[20005]` main: `0xf40000..0xfa0000` (384 KiB)
- `[20004]` and `[30002]` main: both `0xf70000..0xfd0000` (384 KiB), creating a metadata overlap with `[20005]` over `0xf70000..0xfa0000`.

The overlaps may reflect aliases, separate selection modes, or metadata inconsistency; semantics remain **UNKNOWN**. The analyzer flags partial intersections and does not treat identical extents as proof of a shared physical partition.

## Firmware component comparison

- SquashFS: package offset `0x305cf`, end `0x5d8574`.
- uImage: package offset `0x5d85cf`, end `0x7367f7`.
- There is a 91-byte gap between SquashFS end and uImage start.
- These are byte offsets within the update package. The metadata region values are numerically different and extend beyond the package. No verified mapping between the two coordinate systems has been found.

## Board and boot evidence

- **VERIFIED from package metadata:** `board_id=1212`, product text `HG630V2`, software string `V100R001C298B010`.
- **VERIFIED static RootFS reference:** `/etc/profile` creates `/dev/caldata` as a symlink to `/dev/mtd9`.
- **VERIFIED static binary symbols:** vendor utilities/libraries expose names including `ATP_MTD_Getfd`, `ATP_MTD_ReadBuffromOffset`, `ATP_FLASH_WriteArea`, `UPG_FlashPartWrite`, `ATP_DEBUG_KillActivePartition`, `UPG_GetRunCurrentSystem`, and `FOMGetAllFlashSize`.
- **VERIFIED static `libbhalapi.so` evidence:** the library exports `ATP_MTD_Getfd`, `ATP_MTD_Erase`, `ATP_MTD_WriteBufToOffset_Upg`, `ATP_FLASH_Write`, `ATP_FLASH_WriteArea`, `ATP_FLASH_Upgrade`, `ATP_FLASH_UpgradeCfg`, `ATP_FLASH_UpgradeBootloader`, `UPG_FlashPartWrite`, and `FOMGetAllFlashSize`.
- **VERIFIED static MTD device references:** `libbhalapi.so` contains `/dev/mtd0` through `/dev/mtd15`, plus `MEMERASE` and low-level read/write failure messages. This establishes support for a device-number range in vendor code, not the board's partition assignment.
- **Not found in the searched extracted RootFS strings:** a concrete `/proc/mtd` table or `mtdparts=` command line.
- These findings show MTD/upgrade functionality exists in vendor userspace. They do not reveal the actual MTD names, physical chip model/capacity, bootloader version, or erase geometry. Unknown binaries were inspected statically and not executed.

## Capacity candidates

The metadata end `0xfd0000` fits within a hypothetical 16 MiB (`0x1000000`) address space and does not fit within a hypothetical 8 MiB address space. This is arithmetic only; neither candidate is verified for this unit.

## Confidence and next evidence

All proposed extents are **INFERRED, LOW confidence**, with `physical_flash_verified=false`. To establish a physical map, obtain one of:

1. Exact-board GPL source/config containing the MTD partition declaration and flash driver/chip identification.
2. Trusted boot log or live `/proc/mtd` and `/proc/cmdline` from this exact VER.B unit.
3. Legible flash-chip marking and a verified full-chip read plus bootloader environment, with calibration regions protected.

No flash operation or firmware reconstruction is authorized by these findings.
