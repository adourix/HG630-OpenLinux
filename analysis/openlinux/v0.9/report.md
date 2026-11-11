# OpenLinux V0.9 — First bootable image

Date: 2026-11-10

## Result

**Goal A VERIFIED:** A standalone ARMv7 OpenLinux boot bundle boots in QEMU
system emulation on `vexpress-a9`.

**Goal B UNKNOWN/BLOCKED:** No bootable HG630 V2 image was produced or claimed.
The emulator target does not emulate HiSilicon SD5610x.

## Booted artifact

- Bundle directory: `/home/ayad/build-output/openlinux-v09/image-v09/`
- Kernel: `openlinux-v0.9-vexpress-a9.zImage`
- Initramfs: `openlinux-v0.9-vexpress-a9.initramfs.cpio.gz`
- DTB: `openlinux-v0.9-vexpress-a9.dtb`
- Manifest: [build-manifest.json](build-manifest.json)
- Kernel SHA256: `b7ec99aa772542c52e85bdc2ffd04065a18e6b0b16c3ec519beb5fca2366aca1`
- Initramfs SHA256: `84b8e52875f2831f57a58b7bd6fad2634e01e18db99b850907f00fe83d83b98c`
- DTB SHA256: `cb35d197143510bcdadf022f925c23735c4e453f4aa7a207cfbc2b6fb99cb24d`

Artifact type: **QEMU ARMv7 boot bundle**, not an HG630 firmware image or disk
image.

## Validated after boot

The captured log proves:

- Linux 6.12.116 ARMv7 kernel booted on the V2P-CA9 machine model.
- Device tree and PL011 `ttyAMA0` console initialized.
- gzip cpio initramfs unpacked.
- BusyBox init executed the OpenLinux startup.
- status, monitor, memory, uptime, mounts, and logging interfaces ran.
- `OPENLINUX_READY` was reached.
- An interactive shell was available; `echo SHELL_ACCESS_OK` and
  `openlinuxctl status` succeeded.

No network service was enabled; all configured services remain disabled by
default. The interactive run was terminated from the host after validation;
the emulator's `poweroff` command did not terminate QEMU reliably, so clean
shutdown is not claimed.

Full console output is in [boot-logs/vexpress-a9-boot.log](boot-logs/vexpress-a9-boot.log).

## Reproduction inputs and build

The host used Debian trixie packages `gcc-arm-linux-gnueabi`,
`binutils-arm-linux-gnueabi`, `libc6-dev-armel-cross`, `linux-source`, `bc`,
`bison`, `flex`, `libssl-dev`, and `libelf-dev`. The kernel source was
Linux 6.12.116 and the standalone BusyBox source was 1.37.0. The kernel was
built with `ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- vexpress_defconfig`,
then `zImage` and `dtbs`; BusyBox was built static with ARM EABI5. The final
packaging command was:

```sh
python3 tools/build_qemu_image.py \
  --kernel /home/ayad/build-output/openlinux-v09/kernel-vexpress/arch/arm/boot/zImage \
  --dtb /home/ayad/build-output/openlinux-v09/kernel-vexpress/arch/arm/boot/dts/arm/vexpress-v2p-ca9.dtb \
  --busybox /home/ayad/build-output/openlinux-v09/busybox-build/busybox \
  --openlinuxctl build/experimental/openlinux-overlay/rootfs/usr/sbin/openlinuxctl \
  --output /home/ayad/build-output/openlinux-v09/image-v09
```

The external build directory is preserved outside Git; the committed manifest
records input and output hashes.

## Limitations

This is system-emulation validation, not user-mode QEMU and not router
hardware validation. The Huawei kernel, vendor hardware stack, DSL, Wi-Fi,
OEM flash layout, and OEM update acceptance were not exercised.
