# OpenLinux V1.0 — flashability decision

## Result

**HG630 V2 flashable firmware: BLOCKED.** The evidence does not establish the
OEM installation mechanism, cryptographic acceptance contract, component-to-MTD
mapping, RootFS-only update behavior, or recovery path. The project therefore
does not produce or claim `HG630V2-OpenLinux-v1.0-flashable.bin`.

A separately labeled offline candidate was generated:

`/home/ayad/build-output/custom-build/firmware-run-v10/HG630V2-OpenLinux-v1.0-experimental.bin`

Status: `EXPERIMENTAL_NON_FLASHABLE`
SHA256: `9ec2d00ffa546c7b0d3be228c0867fba7ffac2a5e354c6b22d249d1035ab5cb1`

It is byte-identical to the prior V0.4 experimental package because the same
original firmware and same-span RootFS were used. It exists as a V1.0 manifest
reference, not as a deployment recommendation.

## Evidence summary

- **VERIFIED:** original ARMv7 Linux 2.6.30 LZMA uImage, header/data CRCs,
  package component offsets, RootFS extraction, and byte-for-byte kernel
  preservation.
- **PARTIALLY VERIFIED:** OpenLinux overlay preserves the observed vendor file
  inventory and can execute selected ARM userspace checks.
- **UNKNOWN:** hardware revision, root MTD, boot command line, machine handoff,
  BCJ support, main/slave semantics, component selection, outer checksum, and
  recovery.
- **BLOCKED:** legitimate OEM signature verification and a genuinely flashable
  reconstruction.

The V0.9 VExpress-A9 boot proves only the separate development target and does
not validate HG630 V2 hardware.
