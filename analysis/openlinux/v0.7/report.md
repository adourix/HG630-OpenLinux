# OpenLinux V0.7 — OEM-preserving deployment feasibility

Date: 2026-11-10

## Result

The strongest technically justified path is **additional userspace operation
against the preserved OEM RootFS (Approach C), initially operator-controlled
and non-persistent**. A RootFS-only OEM update cannot currently be claimed.

## Findings

- **VERIFIED:** Original package contains metadata, SquashFS, uImage, and suffix;
  embedded uImage CRCs validate.
- **VERIFIED:** `upg` and `libbhalapi.so` contain security, generic/area/config/
  bootloader update, erase/write, and logical `/dev/mtd0`–`/dev/mtd15` paths.
- **UNKNOWN:** Metadata address-space semantics, exact main/slave behavior,
  section-to-MTD mapping, root MTD, signed byte range, and OEM acceptance.
- **PARTIALLY VERIFIED:** Same-layout experimental assembly preserves the
  original kernel and OEM metadata, but remains non-flashable.
- **VERIFIED STATIC:** OEM startup depends on BusyBox init, a respawned shell,
  `/etc/profile`, vendor mounts, module loading, `startbsp`, `hi_xpon`,
  `hsanportinit`, and `mic`.
- **UNKNOWN:** BCJ support in the original kernel and any no-UART recovery path.

## V0.4 comparison

V0.4 RootFS SHA256:
`db620f72a514c62cccc9cd3ae6cb7d27151abec59cb4cb58b4c1aee393777785`.

V0.4 firmware SHA256:
`9ec2d00ffa546c7b0d3be228c0867fba7ffac2a5e354c6b22d249d1035ab5cb1`.

The V0.4 RootFS used XZ with an ARM BCJ filter. Development-host extraction
worked, but the original kernel's BCJ support is not proven. This is an
additional reason not to call the artifact deployable.

## Safety

The V0.7 work executed no OEM ARM binary, opened no MTD device, wrote no flash,
modified no bootloader, and did not modify the original firmware or prior
artifacts. The collector and evidence file are generated from static inputs.

See the detailed reports and `evidence.json` in this directory.
