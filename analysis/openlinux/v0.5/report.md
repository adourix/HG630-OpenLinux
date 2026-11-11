# OpenLinux V0.5 boot compatibility research

Date: 2026-11-10

## Conclusion

The original kernel and the experimental RootFS have compatible broad formats:
the original kernel is ARMv7 Linux 2.6.30 and both filesystems are SquashFS 4.0
with XZ compression and 1 MiB blocks. However, a bootable combination is not
established.

The original kernel contains static SquashFS XZ and generic ARM ATAGS parser
evidence, but no recovered kernel configuration, machine ID, RAM map, UART
address, command line, root MTD mapping, or proof of ARM BCJ filter support.
V0.4's ARM BCJ XZ filter is therefore **UNKNOWN/BLOCKED** for the target
kernel. The maximum proven-compatible build configuration is ordinary XZ
without BCJ, although its size may exceed the fixed replacement span.

## Findings

- uImage header/data CRCs: **VERIFIED**.
- U-Boot LZMA/ARM/Linux kernel format: **VERIFIED**.
- HiSilicon SD56xx/SD5610x platform family: **VERIFIED**.
- Generic ATAGS parser present: **PARTIALLY VERIFIED**.
- Actual ATAGS versus device-tree handoff: **UNKNOWN**.
- Original XZ SquashFS support in kernel: **VERIFIED STATIC**.
- V0.4 ARM BCJ support in kernel: **UNKNOWN/BLOCKED**.
- Kernel `root=` value and runtime MTD partition: **UNKNOWN**.
- Matching QEMU system machine: **BLOCKED**.
- ARM user-mode OpenLinux execution: **VERIFIED PARTIAL**.
- Actual kernel/hardware boot: **BLOCKED**.

Detailed evidence is split across [kernel-analysis.md](kernel-analysis.md),
[boot-protocol.md](boot-protocol.md), [squashfs-deep-analysis.md](squashfs-deep-analysis.md),
[qemu-feasibility.md](qemu-feasibility.md), and [hardware-test-plan.md](hardware-test-plan.md).

## RootFS readiness blockers

The kernel must provide a valid platform handoff and mount the runtime MTD
partition before `/sbin/init` can run. The OEM profile then requires proc/sysfs,
tmpfs, device nodes, vendor modules, `/dev/mtd9` calibration access, and
SD5610x hardware. None of these can be validated by QEMU user mode. The
OpenLinux hook remains outside the OEM startup path.

No generic QEMU machine was retried. No flash, MTD write, bootloader change, or
original-firmware modification occurred.
