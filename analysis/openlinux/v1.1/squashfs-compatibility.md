# V1.1 SquashFS compatibility

## VERIFIED

- Original filesystem: SquashFS 4.0, little-endian, XZ, 1 MiB blocks.
- Original kernel strings include SquashFS 4.0, XZ decoder, and SquashFS XZ
  initialization/error paths.
- Host extraction of the original filesystem succeeds.

## UNKNOWN

The target kernel configuration is unavailable. No direct `CONFIG_XZ_DEC_ARM`,
SquashFS ARM-filter registration, or target-kernel mount test is available.
The V0.4 custom filesystem reports an ARM BCJ filter; host extraction proves
only host support, not target support.

## Reproducible test status

V0.6 generated matched host test files with ordinary XZ and XZ+ARM-BCJ. Both
extracted successfully; only the BCJ image reported `Filters selected: arm`.
This test is retained as host evidence and does not establish target-kernel
support.

Recommendation: do not change production defaults or claim a compatible
RootFS until the exact target `.config`/source or a read-only hardware mount
test is available. The original filesystem's ordinary-XZ properties are the
strongest evidence, but fixed-span size constraints remain separate.
