# Report 1 — Firmware integrity

## Verified server-run result

The committed server run records the owner-supplied image as 7,563,600 bytes with SHA-256 `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222` (`analysis/server-run/firmware-inspect.json`). It identifies one complete SquashFS 4.0 filesystem at offset 198,095, ending at 6,129,012, and one uImage at offset 6,129,103. Both uImage header and payload CRCs are valid.

The uImage is a Linux 2.6.30 ARM image (architecture ID 2), with a 1,434,088-byte gzip-compressed payload. The 91-byte gap between the filesystem and kernel is recorded evidence; it is not evidence of a partition map.

This verifies the recorded server-run input and its structural checks. It does not authorize flashing or prove that the package is a complete flash dump.

## Reproduction

```sh
sha256sum /root/firmware-input/HG630V2-12V100R001.bin
python3 tools/firmware_inspect.py /root/firmware-input/HG630V2-12V100R001.bin --json
```

No firmware was modified, flashed, or committed. The repository contains metadata and hashes only; the firmware binary and extracted rootfs remain excluded.
