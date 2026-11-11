# HG630 V2 compatibility track

Status: **UNKNOWN/BLOCKED for bootable deployment**.

The V0.9 emulator image deliberately does not use the Huawei 2.6.30 kernel,
OEM RootFS, SD5610x drivers, MTD layout, or update signature path. The original
kernel, DSL/Ethernet/Wi-Fi modules, calibration link, vendor libraries, and
OEM firmware remain preserved in their prior artifacts.

Known facts:

- Original platform family: HiSilicon SD56xx/SD5610x.
- Original kernel: ARMv7 Linux 2.6.30, legacy U-Boot uImage, LZMA payload.
- Original RootFS: SquashFS 4.0/XZ; generic XZ support is statically evidenced.
- Original root MTD, command line, RAM layout, machine ID, boot protocol, and
  ARM BCJ support: UNKNOWN.
- OEM signature/outer checksum and metadata-to-MTD mapping: UNKNOWN/BLOCKED.

Approach C remains the compatibility architecture: develop and test an
additional userspace layer while preserving the OEM image. No router-specific
bootable image was produced, and no OEM security mechanism was bypassed.
