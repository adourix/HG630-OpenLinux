# V0.7 RootFS-only deployment feasibility

## Evidence

**VERIFIED:** The extracted OEM RootFS uses BusyBox init via `/init ->
bin/busybox` and `/sbin/init -> ../bin/busybox`. `/etc/inittab` runs
`/etc/init.d/rcS` as `sysinit`, then respawns `-/bin/sh`.

**VERIFIED:** The observed `rcS` only sets `PATH` and prints `RCS DONE`.
The subsequent shell profile contains the vendor startup work: tmpfs/proc/sysfs
mounts, `makedevs`, `startbsp`, `hi_xpon`, `hsanportinit`, background module
loading, `/dev/caldata -> /dev/mtd9`, and `mic`.

**VERIFIED:** The profile contains conditional JFFS2 mounts for
`/dev/mtdblock7 -> /config` and `/dev/mtdblock12 -> /etc/tri_image_up`.
These are configuration/image references, not proof that either is the root
filesystem. The root MTD device and kernel root arguments remain UNKNOWN.

**VERIFIED:** The RootFS contains the original vendor libraries, DSL/network
modules, `startbsp`, `mic`, `web`, `dns`, `dhcps`, `sshd`, and `upg`. The V0.4
artifact preserves these files and the original kernel.

## Feasibility result

**UNKNOWN:** An OEM-supported RootFS-only update path. The package includes an
embedded filesystem and kernel, but no traced selection rule proves that the
updater can replace only the filesystem while preserving the kernel and all
other regions.

**PARTIALLY VERIFIED:** A same-offset experimental RootFS replacement can be
assembled and structurally validated. This preserves the original uImage and
metadata bytes, but it is not OEM acceptance or hardware compatibility evidence.

**BLOCKED:** Deployment. Signature/outer-integrity requirements, exact
metadata-to-MTD mapping, root mount parameters, recovery behavior, and hardware
boot evidence are missing. The V0.4 artifact remains
`EXPERIMENTAL_NON_FLASHABLE`.

## Conservative conclusion

Do not treat the current same-layout builder as a RootFS-only OEM update tool.
The safe next step is hardware discovery and read-only observation of the exact
board. Any future RootFS replacement must keep the original kernel and vendor
stack and must first establish the root partition and signed update contract.
