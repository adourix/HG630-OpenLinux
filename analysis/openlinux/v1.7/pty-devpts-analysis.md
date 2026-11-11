# V1.7 PTY and devpts analysis

Static source: `/home/ayad/build-output/rootfs`. The exact target kernel `.config` and live router procfs were not supplied.

## Evidence

- Extracted `/dev` has only `null`, `console`, and an empty `/dev/pts` directory. Those are extraction artifacts; `/etc/profile` mounts tmpfs on `/dev` and runs `makedevs` at boot.
- `/etc/devicetable` defines `/dev/ptmx` as char 5:2 and legacy `/dev/ptyp*`/`ttyp*` nodes. This does not prove Unix98 allocation.
- `/etc/fstab` mounts only proc. Inspected `profile`, `inittab`, `rcS`, and `insmod_all.sh` contain no devpts mount. No devpts module exists; devpts is normally filesystem support, not a module guarantee.
- OEM Dropbear imports `openpty` and contains PTY allocation errors. This proves code path presence, not kernel support.
- No exact kernel config or target kernel symbol/config file was found. `CONFIG_UNIX98_PTYS`, `CONFIG_DEVPTS_FS`, TTY support, and limits remain UNKNOWN. Separate VExpress configs are unrelated.

## Mount candidate

`mount -t devpts devpts /dev/pts` is syntactically conventional for Linux 2.6-era devpts, but whether this kernel includes devpts, accepts that source/options, has Unix98 PTYs enabled, or permits the resulting master/slave allocation is **UNKNOWN**. The OpenLinux service does not run this command. `openlinux-ssh-check` is read-only and reports mounts/filesystems; it never attempts a mount.

The related HG630 V2 `Server refused to allocate pty` observation cannot be causally attributed. An unmounted devpts filesystem is plausible, but kernel support, permissions, daemon policy, and firmware differences are also candidates.

## Diagnostic

`build/runtime/bin/openlinux-ssh-check` checks `/dev/ptmx`, `/dev/pts`, `/proc/mounts`, `/proc/filesystems`, kernel version/cmdline, `/bin/sh`, and the OEM daemon. It prints `MISSING/UNKNOWN` per absent item and returns nonzero if any evidence is missing. Path environment overrides exist solely for tests and later authorized read-only inspection. It changes no state.
