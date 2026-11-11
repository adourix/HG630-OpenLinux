# V1.1 kernel compatibility

## VERIFIED

- Original uImage: ARM/Linux legacy format, LZMA payload, Linux 2.6.30,
  load/entry `0x81208000`, valid header/data CRCs.
- Vendor modules carry vermagic `2.6.30 SMP preempt mod_unload ARMv7`.
- Kernel strings prove SquashFS 4.0 and generic XZ decoder paths.
- Vendor userspace uses the original `/lib/ld-uClibc.so.0` interpreter and
  module ABI. Reusing the VExpress-A9 6.12 kernel is not compatible with this
  target.

## PARTIALLY VERIFIED

The preserved RootFS contains the expected vendor module loading and DSL
startup sequence. This supports a vendor-kernel-derived userspace strategy but
does not prove successful target boot or DSL synchronization.

## UNKNOWN / BLOCKED

The kernel `.config`, exact machine handoff, root MTD, command line, RAM map,
and runtime ioctl behavior are unavailable. ARM BCJ support is not directly
shown by the kernel strings or module inventory. The V0.4 RootFS uses an ARM
BCJ filter and therefore cannot be promoted to target-compatible.

Replacement kernels are BLOCKED: no supported upstream SD5610x DSL stack or
verified boot protocol is available. The conservative architecture remains the
original kernel plus preserved vendor drivers and a minimally additive
userspace.
