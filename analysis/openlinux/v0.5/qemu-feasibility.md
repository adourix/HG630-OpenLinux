# QEMU feasibility

## Available emulation

QEMU 10.0.13 provides generic ARM machines including Versatile, RealView,
vexpress, `virt`, i.MX, Zynq, Raspberry Pi, and Cortex-A7/A8/A9/A15 boards. It
does not provide a HiSilicon SD56xx or SD5610x machine, compatible memory map,
interrupt controller, timer, UART, clocks, MTD controller, DSL/XPON hardware,
or vendor network peripherals.

## Conclusion

System emulation of the original kernel is **BLOCKED** by missing platform
emulation. Previous bounded generic-machine attempts produced no kernel console
output and are not repeated here. Passing the original LZMA uImage directly to
QEMU was rejected by its image loader as compression type 3; this is not a
kernel validity result.

QEMU user mode remains useful for selected userspace checks. With
`QEMU_LD_PREFIX` and a RootFS-only `PATH`, V0.4 OpenLinux scripts executed under
the preserved ARM BusyBox. This proves selected ARM process execution only; it
does not emulate kernel boot, mounts, modules, MTD, DSL, Wi-Fi, or firewall
kernel behavior.

## Required emulator work

A meaningful system emulator would require a model of the exact SD5610x SoC,
its ARM machine registration, UART, interrupt controller, timer/clock blocks,
RAM map, MTD device, and enough vendor peripheral behavior for `startbsp` and
the kernel's platform code. None of those artifacts are available in the
repository. No QEMU machine should be selected by CPU family alone.
