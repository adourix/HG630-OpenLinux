# SD5610x platform extraction

Date: 2026-11-10

## Evidence

**VERIFIED:** the original ARM uImage payload, decompressed without executing
it, contains these platform identifiers and initialization symbols:

- `SD56XX`
- `sd5610x_iomux_*` and `sd5610x_gpio_*`
- `sd56xx apb bus clk is %lu`
- `sd56xx System Timer`
- `sd56xx_reboot_reg`
- `Machine: %s`

The kernel identifies as Linux 2.6.30, ARMv7, SMP PREEMPT, built with GCC 4.4.6
from the vendor `hsan-5115` toolchain. Vendor modules carry matching
`2.6.30 SMP preempt mod_unload ARMv7` vermagic and reference
`hi_kernel_sd56xx_*`. Modules include `hi_kgpio`, `hi_keth`, `hi_kphy`,
`hi_kmdio`, `hi_sdk_l0`, `hi_sdk_l1`, and `hisihwfirewall`.

This establishes the HiSilicon SD56xx/SD5610x platform family. It does not
establish a precise chip revision, board schematic, or register map.

## Boot protocol and memory

**VERIFIED:** the outer uImage header supplies load and entry address
`0x81208000`, and the payload is LZMA-compressed. The kernel contains standard
Linux strings for `Machine:`, `root=`, MTD partition registration, and the
SquashFS 4.0 driver.

**UNKNOWN:** no embedded `IKCFG` marker or readable kernel configuration was
found in the decompressed payload. The available evidence does not prove the
machine ID integer, ATAGS layout, device-tree use, RAM size, UART address,
interrupt controller, timer registers, or clock registers.

**UNKNOWN:** SquashFS support is present, but the MTD partition name/device and
mount flags remain unproven. Vendor startup ordering must be mapped before
enabling hardware-changing services.

## Safe next analysis

Targeted disassembly around the `SD56XX` machine descriptor and `sd5610x_*`
platform functions is the next platform task. Register addresses, ATAGS values,
and RAM layout will be recorded only when supported by instruction/data
references. No vendor kernel or module was executed and no hardware or MTD was
accessed.
