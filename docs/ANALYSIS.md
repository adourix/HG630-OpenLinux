# Initial binary analysis

Input: owner-provided OEM update package, retained offline.

- Size: 7,563,600 bytes
- SHA-256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`
- SquashFS little-endian marker at `0x305cf`: version 4.0, compression ID 4 (LZMA), 1,257 inodes, 1 MiB block size, bytes_used 5,930,917.
- uImage header at `0x5d85cf`; payload begins at `0x5d860f`, length 1,434,088 bytes.
- Kernel name: `Linux-2.6.30`; load and entry address `0x81208000`.
- uImage header CRC and payload CRC both validate.
- Package string `board_id=1212` is observed; it is not proven to equal the physical CFE board ID.

## Layout arithmetic

The SquashFS region starts at decimal 197,071 and reports 5,930,917 bytes used, so its calculated end is 6,127,988 (0x5d85b4). The uImage header begins at 6,129,103 (0x5d85cf), leaving 27 bytes between the declared filesystem end and the uImage header.

The uImage payload ends at 7,563,255 (0x7368b7), leaving 345 bytes to the end of the input file (7,563,600). This arithmetic is useful for package-layout investigation; it is not a flash partition map.

## What is not established

These package facts do not prove PCB identity, flash partition geometry, DSL silicon, or driver compatibility. The image is an OEM update package, not a confirmed full-chip dump. Rootfs extraction and DSL stack inventory remain pending.
