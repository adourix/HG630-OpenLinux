# V1.1 boot-chain assessment

## VERIFIED

- The package contains a legacy U-Boot ARM uImage named `Linux-2.6.30`.
- uImage load and entry addresses are both `0x81208000`; header and payload
  CRCs validate.
- The decompressed kernel contains generic `root=` and `console=` handling,
  ATAGS-related strings, SD5610x platform strings, `uart:0/uart:1`, SquashFS
  4.0, and XZ decoder strings.
- Vendor startup statically creates device nodes, loads SD56xx modules,
  loads `ipcdrv.ko`/`tri_ctl.ko`, runs `hi_xpon`, `hsanportinit`, and mounts
  selected JFFS2 devices from the shell profile.

## UNKNOWN

No bootloader binary or UART log is available to prove the bootloader identity,
machine ID, ATAGS contents, FDT handoff, RAM map, command line, root MTD, initrd
use, or kernel root mount arguments. No FDT blob was found in the kernel payload,
but that does not prove the bootloader cannot supply one.

The original `root=` warning string proves the kernel supports a root argument,
not which value the router supplies. The observed `/dev/mtdblock7` and
`/dev/mtdblock12` mounts are configuration/image mounts, not proof of the root
partition.

## Safety conclusion

Boot-chain reconstruction is BLOCKED for a target image until a passive UART
capture or matching vendor source establishes the handoff. No kernel or
bootloader replacement is authorized.
