# Report 1 — Firmware integrity

## Result

This Debian server cannot verify the requested input because `/root/firmware-input/HG630V2-12V100R001.bin` is absent, and no matching copy was found under the available `/root`, `/tmp`, or `/mnt` trees on 2026-11-10.

The repository records prior, unverified-on-this-server evidence for the owner-supplied file: 7,563,600 bytes and SHA-256 `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`. Treat that as a comparison value, not a new verification.

## Reproduction

```sh
sha256sum /root/firmware-input/HG630V2-12V100R001.bin
python3 tools/firmware_inspect.py /root/firmware-input/HG630V2-12V100R001.bin --json
```

No firmware was modified or copied.
