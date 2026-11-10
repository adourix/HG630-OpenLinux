# Report 2 — Package layout and kernel

The historical repository evidence identifies a little-endian SquashFS 4.0 region at `0x305cf`, compression ID 4 (LZMA), and a legacy uImage at `0x5d85cf`. The uImage name is `Linux-2.6.30`, load/entry address `0x81208000`, and its prior inspection reported valid header and payload CRCs.

The recorded uImage architecture ID is 2, which is the legacy U-Boot ARM identifier. This supports 32-bit ARM, but does not independently prove ARMv7, floating-point ABI, SoC, board ID, flash geometry, or partition layout. The values must be re-run against the supplied binary before release decisions.
