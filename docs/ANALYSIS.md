# Initial binary analysis

Input: owner-provided OEM package, retained offline.

- Size: 7,563,600 bytes
- SHA-256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`
- SquashFS LE marker at `0x305cf`: v4.0, LZMA compression ID 4, 1,257 inodes, 1 MiB block size, bytes_used 5,930,917.
- uImage header at `0x5d85cf`; payload begins at `0x5d860f`, length 1,434,088 bytes.
- Kernel name: `Linux-2.6.30`; load and entry address `0x81208000`.
- uImage header CRC and payload CRC both validate.
- Package string `board_id=1212` is observed; it is not proven to equal physical CFE board ID.

These package facts do not prove PCB identity, flash partition geometry, DSL silicon or DSL driver compatibility. Rootfs extraction and DSL stack inventory remain pending.
