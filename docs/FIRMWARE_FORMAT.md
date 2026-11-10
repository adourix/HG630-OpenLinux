# Firmware format notes

These observations refer to the owner-supplied firmware image examined during initial analysis.

| Observation | Value |
|---|---|
| File size | 7,563,600 bytes |
| SHA-256 | d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222 |
| SquashFS magic offset | 0x305cf |
| SquashFS marker | `hsqs` (little-endian) |
| uImage magic offset | 0x5d85cf |
| uImage name | Linux-2.6.30 |
| uImage data size | 1,434,088 bytes |
| uImage load address | 0x81208000 |
| uImage entry point | 0x81208000 |

The uImage header and payload CRCs were reported valid in the initial analysis. The SquashFS signature still needs extraction with a compatible SquashFS 4.0 LZMA implementation. These offsets do not prove the device flash partition map or that the update package is a raw flash dump.
