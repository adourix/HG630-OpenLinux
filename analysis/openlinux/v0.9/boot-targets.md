# V0.9 boot targets

| Target | Result | Evidence |
|---|---|---|
| Huawei HG630 V2 / SD5610x | BLOCKED | Original kernel and vendor stack are preserved, but machine handoff, RAM, root MTD, command line, and exact hardware protocol remain unknown. |
| QEMU `virt` | Not selected | Available in QEMU, but the selected kernel was not built for this machine; using it would require a separate compatible kernel/DTB profile. |
| QEMU `vexpress-a9` | VERIFIED system boot | QEMU 10.0.13, ARMv7 Cortex-A9, 256 MiB, Linux 6.12.116, supplied V2P-CA9 DTB, PL011 `ttyAMA0`, gzip newc initramfs. |

The selected target is a genuine generic ARM system emulator. It is not an
emulation of HiSilicon SD5610x and proves nothing about HG630 hardware boot.

## Reproducible boot command

From the image directory:

```sh
qemu-system-arm -M vexpress-a9 -m 256M \
  -kernel openlinux-v0.9-vexpress-a9.zImage \
  -dtb openlinux-v0.9-vexpress-a9.dtb \
  -initrd openlinux-v0.9-vexpress-a9.initramfs.cpio.gz \
  -append 'console=ttyAMA0,115200 rdinit=/init' \
  -serial stdio -monitor none -display none \
  -audio driver=none -no-reboot
```
