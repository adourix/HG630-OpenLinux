# Extraction status — 2026-11-10

## Completed on the supplied OEM image

The supplied file was read locally and carved without modifying it.

- OEM image size: 7,563,600 bytes
- OEM image SHA-256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`
- SquashFS starts at `0x305cf`, size 5,930,917 bytes, version 4.0, compression ID 4, 1,257 inodes.
- SquashFS carved-file SHA-256: `68dcfa5c1b53bd09fcd00ea52bdcd3fb1da25d53446915cd6fd2f3aba22bb534`
- uImage starts at `0x5d85cf`; image name `Linux-2.6.30`; MIPS architecture ID 2; load/entry `0x81208000`.
- uImage payload size: 1,434,088 bytes.
- Header CRC and payload CRC both validate.
- Gap between SquashFS end and uImage start: 91 bytes.

## Not yet completed

The SquashFS has been carved, but not decompressed. The filesystem declares compression ID 4 (legacy LZMA). This environment did not have `unsquashfs`; package installation timed out. Therefore no rootfs inventory, DSL driver identification, or module dependency graph can honestly be claimed yet.

## Reproducible commands

```bash
python3 tools/carve_firmware.py HG630V2-12V100R001.bin -o artifacts/carved
tools/extract_rootfs.sh HG630V2-12V100R001.bin
python3 tools/inventory_rootfs.py artifacts/extracted/rootfs
```

Use an `unsquashfs` build with legacy LZMA1 support. Upstream SquashFS tools document the extraction interface; OpenWrt's host build recipe shows enabling `LZMA_XZ_SUPPORT=1` for LZMA1 support. See references in the project README.

Do not commit extracted vendor binaries or firmware blobs until redistribution rights are established.
