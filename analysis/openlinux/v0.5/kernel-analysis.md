# Original kernel analysis

## uImage header — VERIFIED

The preserved kernel is a U-Boot legacy ARM uImage:

| Field | Value | Classification |
|---|---:|---|
| Magic | `0x27051956` | VERIFIED |
| Header CRC | `0x0e3295ab`, valid | VERIFIED |
| Data CRC | `0x88c1e0b5`, valid | VERIFIED |
| Timestamp | 2017-03-29 07:06:10 UTC | VERIFIED |
| Payload size | 1,434,088 bytes | VERIFIED |
| Load address | `0x81208000` | VERIFIED |
| Entry address | `0x81208000` | VERIFIED |
| OS | Linux | VERIFIED |
| Architecture | ARM | VERIFIED |
| Image type | Kernel | VERIFIED |
| Compression | LZMA, U-Boot type 3 | VERIFIED |
| Name | `Linux-2.6.30` | VERIFIED |

The decompressed payload begins with ARM instructions, is not an ELF image, and
contains Linux 2.6.30/ARMv7 build text from GCC 4.4.6/crosstool-NG `hsan-5115`.
The kernel contains `SD56XX`, `sd5610x_*`, `sd56xx System Timer`, GPIO/IOMUX,
MTD, SquashFS, and vendor reboot/platform symbols. The platform family is
**VERIFIED** as HiSilicon SD56xx/SD5610x; the exact silicon revision is
**UNKNOWN**.

## Command line and boot protocol clues

The kernel contains generic parameter names `root=`, `rootfstype=`, `rootflags=`,
`rootwait`, `console=`, `mem=`, `init=`, and `rdinit=`, but no default command
line string was identified. No `mtdparts=` string was found. Root device,
console argument, RAM size argument, and mount flags are therefore **UNKNOWN**.

The payload contains the generic ARM messages `Converting old-style param struct
to taglist` and `ATAG_INITRD is deprecated`. This proves that the kernel includes
generic ATAGS parsing support (**PARTIALLY VERIFIED**), not that the bootloader
actually supplies ATAGS on this board. No `0xd00dfeed` FDT magic and no readable
`Device Tree` marker was found in the decompressed payload. Actual ATAGS versus
device-tree handoff remains **UNKNOWN**.

The kernel includes `ttyS`, `ttyAMA`, and `uart:0`/`uart:1` strings, but these
are generic driver/platform strings. No SD5610x UART base, IRQ, baud rate, or
boot console selection was proven.

## Configuration and limitations

No embedded `IKCFG` marker or readable kernel `.config` was recovered. Static
strings prove SquashFS XZ, MTD, proc, module, and ARM kernel facilities, but do
not prove every build option or hardware initialization path. The original
kernel has not been executed.
