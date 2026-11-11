# Boot protocol and handoff evidence

## Verified facts

- U-Boot loads and enters the LZMA uImage at `0x81208000`, according to the
  preserved header.
- The image is a legacy ARM uImage, not an ELF kernel and not a self-describing
  device-tree bundle.
- The kernel contains generic ARM ATAGS parsing messages and generic `root=` and
  `console=` parameters.
- The OEM RootFS startup expects `/dev`, `/proc`, `/sys`, tmpfs, module loading,
  `/dev/mtd9` calibration access, hardware character devices, and vendor
  platform modules.

## Unknown handoff requirements

The available artifacts do not establish:

- machine ID integer;
- ATAGS contents or whether ATAGS are supplied;
- device-tree blob address or usage;
- RAM base, RAM size, or reserved regions;
- UART base/IRQ/baud or console device;
- kernel command line;
- initrd usage;
- root MTD partition name/device and mount flags;
- bootloader environment or fallback behavior.

The absence of an FDT magic value in the kernel payload does not rule out a
bootloader-supplied FDT. Conversely, generic ATAGS strings do not prove that
the board uses ATAGS. These are **UNKNOWN**, not assumptions.

## RootFS mount implications

The original package places SquashFS at offset `0x305cf` in the update image,
while the kernel is at `0x5d85cf`. Those package offsets are not a verified
runtime MTD address. The exact MTD partition mapping and the kernel's `root=`
value must be obtained from matching bootloader/kernel source or read-only
hardware observation. No mount command should be invented from the package
offset alone.
