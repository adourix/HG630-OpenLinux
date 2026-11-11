# V0.4 kernel and RootFS compatibility audit

## Verified static compatibility

- OEM userspace and V0.4 scripts target ARM EABI5/uClibc, matching the
  original ARMv7 Linux 2.6.30 environment.
- The dynamic interpreter `/lib/ld-uClibc.so.0` and vendor libraries are
  preserved.
- Vendor modules carry matching `2.6.30 SMP preempt mod_unload ARMv7` vermagic;
  `tri_ctl.ko` declares `ipcdrv` as a dependency.
- The OEM profile explicitly establishes `/dev`, `/proc`, `/sys`, `/var`,
  `/tmp`, and `/mnt` before vendor services start. Vendor paths use `/var/run`,
  not systemd or a mandatory `/run` hierarchy.
- V0.4 scripts use only verified shell/BusyBox facilities: `sh`, `awk`, `mkdir`,
  `kill`, `sleep`, `cp`, `cat`, and shell builtins. The previous V0.3 use of
  unavailable `sed`, `wc`, `mv`, and `tr` was removed.

## Kernel feature boundary

The OEM profile requires proc/sysfs/tmpfs mounts, module loading, MTD/JFFS2
access, and hardware network interfaces. Static kernel strings support the
presence of proc, MTD, SquashFS XZ, and module infrastructure, but no runtime
kernel is available in user-mode QEMU. Firewall hooks and vendor ioctl behavior
remain target-kernel dependent.

No unsupported syscall was identified, but absence of an embedded kernel config
means syscall/config coverage is **UNKNOWN**. ARM user-mode execution validates
selected processes and scripts only; it cannot validate mounts, modules,
interrupts, DSL, Wi-Fi, MTD, firewall kernel hooks, or actual init behavior.
