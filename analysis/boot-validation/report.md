# HG630 V2 boot validation

Date: 2026-11-10

## Result

The first custom image is structurally validated but has not booted a Linux
kernel in emulation. The strongest executable validation is ARM user-mode
execution of the preserved RootFS BusyBox and its `rcS` script. No claim of
kernel or HG630 V2 hardware boot is made.

## Platform identification

**VERIFIED:** the preserved Linux 2.6.30 kernel identifies itself as ARMv7 and
contains the platform strings `SD56XX`, `sd5610x_iomux_*`, `sd5610x_gpio_*`,
`sd56xx System Timer`, and `sd56xx_reboot_reg`. The vendor modules use
`hi_kernel_sd56xx_*` symbols and were built with ARMv7 2.6.30 vermagic. This is
direct evidence for the HiSilicon SD56xx/SD5610x platform family.

**UNKNOWN:** the exact physical silicon revision or complete board wiring is not
recoverable from the available kernel/module evidence. The SD56xx/SD5610x
identifier must not be expanded into an unverified QEMU machine selection.

The RootFS module inventory also contains the hardware-specific DSL, Ethernet,
PHY, GPIO, SPI, firewall, Wi-Fi, and vendor SDK modules. These were preserved;
they were not loaded in the host or emulated kernel.

## Kernel and RootFS evidence

**VERIFIED:** the original uImage is preserved byte-for-byte in the experimental
image. It is a U-Boot ARM image named `Linux-2.6.30`, LZMA-compressed, with load
and entry address `0x81208000`, payload size 1,434,088 bytes, and valid uImage
header/data CRC32 values.

**VERIFIED:** the custom RootFS is SquashFS 4.0 and contains BusyBox `/init`
and `/sbin/init`. `/etc/inittab` invokes `/etc/init.d/rcS`; the current minimal
script sets `PATH` and prints `RCS DONE`. This script was executed by `qemu-arm`
in user mode with exit status 0.

The artifact and manifest were rechecked without rebuilding:

```text
HG630V2-experimental.bin SHA256
349d448549c468145df58176c4e787d5a192b5dbde6135496fa8e4027f84fcc4
size 7563600
```

The existing manifest remains authoritative for the input hashes, preserved
kernel hash, offsets, and `EXPERIMENTAL_NON_FLASHABLE` status. Its SHA report
uses a basename relative to its output directory; verification was therefore
performed with the absolute artifact path rather than `sha256sum -c` from the
repository root.

## QEMU investigation

`qemu-system-arm` and `qemu-arm` were installed from the configured Debian
trixie repository. QEMU 10.0.13 offers generic ARM boards such as `versatilepb`,
`realview-pb-a8`, `vexpress-a9`, and `virt`, but no HiSilicon SD56xx/SD5610x
machine.

Two bounded system-emulation attempts using the decompressed vendor kernel
produced no console output before timeout on `versatilepb` and `virt`.
Attempting to pass the original uImage directly produced:

```text
Unable to load u-boot images with compression type 3
```

The latter is a QEMU image-loader limitation for this LZMA uImage invocation,
not evidence that the router kernel is invalid. The generic-machine timeouts
are likewise not boot success or proof of a kernel defect; the machine ID,
memory map, UART, interrupt controller, and device tree/platform data do not
match the vendor SD56xx platform sufficiently to establish a meaningful boot.

Full command output is preserved in [boot-log.txt](boot-log.txt), with the
corresponding external raw run logs under
`/home/ayad/build-output/boot-validation/run-001/`.

## Validation levels

| Level | Status | Evidence |
|---|---|---|
| RootFS build and extraction | VERIFIED | Existing reproducible RootFS pipeline and validator |
| Kernel structure and CRC | VERIFIED | Existing uImage inspection and preserved-kernel hash |
| Firmware container structure | VERIFIED | Existing builder manifest and rechecked artifact hash |
| ARM user-mode BusyBox/rcS | VERIFIED (partial) | `qemu-arm`, exit 0, `RCS DONE` |
| Kernel boot in emulation | UNKNOWN/BLOCKED | No matching QEMU machine; bounded attempts had no console output |
| RootFS mounted by kernel | UNKNOWN/BLOCKED | No kernel boot reached a mount attempt |
| Services initialized with hardware | UNKNOWN/BLOCKED | No hardware devices or vendor modules available in emulation |
| OEM update acceptance | UNKNOWN | Signature/outer integrity requirements unresolved |
| Actual HG630 V2 hardware boot | BLOCKED | Deliberately not attempted |

## Reproducibility

The existing assembly command can be rerun with a new output directory, while
preserving the known-good run-001 artifact:

```sh
python3 tools/build_firmware.py \
  --original /home/ayad/firmware-input/HG630V2-12V100R001.bin \
  --rootfs /home/ayad/build-output/custom-build/run-007/rootfs.squashfs \
  --output /home/ayad/build-output/custom-build/firmware-run-N/HG630V2-experimental.bin
```

The builder validates the original SHA256, RootFS structure/extraction, exact
reserved span, preserved uImage, and output manifest. It does not synthesize an
OEM signature or claim flashability.

## Safety conclusion

The experimental image remains non-flashable and was not sent to a router. No
physical MTD device was opened and no erase/write operation was performed.
