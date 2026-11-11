# OpenLinux V1.3 — HG630 V2 USB Runtime Deployment Investigation

Date: 2026-11-11. Target reported by operator: HG630 V2 VER.B, OEM `V100R001C298B010`. This is static inspection of the supplied extracted OEM RootFS and V1.2 package plus the operator's stated FTP observations. No router command was run, no configuration changed, no service enabled, and no runtime executed on the target. QEMU results are not target validation.

## Conclusion

The existing USB/FTP path is a confirmed file-transfer route, and firmware evidence maps FTP-managed storage into `/mnt`. It is **not a confirmed runtime execution route**. The firmware's `usbmount` mount-option strings specify `noexec` for NTFS, VFAT, and HFS+ and for ext3; only the ext2 mount command lacks an explicit `noexec`. The connected device's filesystem types and live mount flags are not known from the operator observations. FTP write access does not establish that uploads retain Unix execute bits or that a local shell can execute them.

No authorized, documented interactive shell method is established for this exact VER.B unit. Until the operator obtains such a method and can read the live mount table/filesystem type, the runtime must not be deployed. The immediate next action is to ask Huawei/the authorized service provider for the approved service-console procedure and exact-board pinout for this VER.B unit. Do not infer pinout or use an undocumented debug interface based on a similar HG630 model.

## Confirmed observations

- Operator reports USB recognized; FTP banner is `bftpd`; FTP login as `ayad` succeeds; root lists `Lexar___-21C40209_usb1_1` and `_usb1_2`; archive download and `test.txt` upload work. Operator verified the downloaded archive SHA-256 as `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`.
- Host-side archive SHA-256 independently matches that value. The archive has top-level `openlinux/` and contains only shell/text runtime files, including scripts installed with executable mode in the tar archive.
- These operator observations demonstrate FTP file transfer only. They do not show the local mount path, filesystem type/options, resulting mode bits, shell access, or successful `execve` on the router.
- The supplied extracted firmware tree is `/home/ayad/build-output/rootfs`. Exact device identity comes from operator confirmation; static files are from the supplied firmware extraction and not a live router read.

## USB mount and visibility analysis

### Firmware evidence

- `/home/ayad/build-output/rootfs/etc/profile` mounts tmpfs at `/mnt` during startup, then runs `/etc/insmod_all.sh` asynchronously and starts `mic`. It does not contain an explicit removable-disk mount command. `/mnt` is therefore initially RAM-backed and volatile; USB management must mount storage over or below this location later.
- `/home/ayad/build-output/rootfs/etc/devicetable` creates SCSI block nodes `/dev/sda` through `/dev/sdh` (mode `0640`, root:root), creates `/mnt` (mode `0770`, uid/gid 1103), and creates `/var/usb` and `/var/ftp` as `0770` root-owned directories. These entries establish intended node/directory provisioning, not a live device or mount.
- `/home/ayad/build-output/rootfs/bin/cms` strings include `/mnt/%s`, `/mnt%s`, a generated name pattern `%s%s-%s_usb%u%s`, `/proc/mounts`, `usbmount %x %s %s`, success/error messages with device and mount paths, and supported mount commands/options. This supports a dynamic USB storage mount path under `/mnt`; exact live paths remain unobserved. No reliable source-name-to-local-path mapping is available from strings alone.
- `usbmount` has ARM executable type and mount-command strings. Presence of the binary is not proof it was invoked for these partitions. The absence of USB mass-storage modules in the extracted module tree is notable: `/lib/kernel/drivers/usb` contains only `serial/option.ko`, while the scripts reference USB core, host, and storage modules that are not present there. The operator's live recognition shows some working firmware path for this particular disk; the static module inventory does not explain it and should not override that observation.

### Filesystem and execution flags

`/home/ayad/build-output/rootfs/bin/cms` embeds these relevant mount invocations:

| Filesystem | Embedded mount evidence | Execution assessment |
|---|---|---|
| NTFS | `ntfs-3g -o big_writes,noexec,...` | Explicitly noexec. |
| ext3 | `mount -t ext3 -o rw,noexec` | Explicitly noexec. |
| VFAT | `mount -t vfat -o iocharset=utf8,shortname=winnt,noexec` | Explicitly noexec; FAT mode bits are mount-derived as well. |
| HFS+ | `mount -t hfsplus -o nls=utf8,rw,noexec` | Explicitly noexec. |
| ext2 | `mount -t ext2` with no options visible in this string | No explicit noexec is visible in the captured command string. Whether this path is used, its kernel default/live flags, and file mode behavior are unverified. This is not evidence that the current disk is ext2 or executable. |

`/home/ayad/build-output/rootfs/etc/profile` contains commented-out module loads for FAT, VFAT, and NTFS kernel modules; however, `cms` has NTFS-3G strings and the operator confirms a working disk. The report does not infer the filesystem from the product label. The actual filesystem may be implemented via another runtime component or mount path.

### FTP root, chroot, permissions, local visibility

- The operator-confirmed FTP server is `bftpd`. `/home/ayad/build-output/rootfs/bin/cms` contains generated bftpd config strings for `/var/ftp/bftpd.conf`, password/user files, `DO_CHROOT="yes"`, and `InternetGatewayDevice.Services.StorageService.1.FTPServer.AnonymousUser.StartingFolder`. This is evidence the firmware's FTP implementation supports chroot and a configurable starting folder. The exact active config was generated under volatile `/var`, not present as a static config file, so the effective per-user root/chroot and `ayad` mapping cannot be proven from the image alone.
- `/home/ayad/build-output/rootfs/etc/webimg` configures USB accounts and defaults `utf8dir`/`nativedir` to `/mnt`; its USB folder management also supplies `/mnt` paths. The CMS mount naming strings and web UI behavior support the interpretation that the FTP-exposed volume directories correspond to local paths managed under `/mnt`.
- Consequently, uploaded files are expected to be visible to local processes at the same mounted storage location if the active FTP user maps into that location. The operator has not verified local process visibility, and FTP chroot can make the client-visible path differ from the physical path. Classify local visibility as **POSSIBLE_BUT_UNVERIFIED**, not confirmed.
- `/var` is tmpfs per `/etc/profile`, so bftpd's generated configuration, FTP state, and `/var/ftp` are volatile. `/mnt` is also initially tmpfs; USB contents would persist on the medium, while mount state does not.
- Firmware mount flags make USB execution unlikely for the common filesystems explicitly listed above. No target `mount` output or execution attempt is available. The archive's tar executable modes only describe archive metadata; FTP upload and the target filesystem may not preserve them.

## FTP implementation and shell access investigation

Statuses use `CONFIRMED`, `PRESENT_BUT_DISABLED`, `POSSIBLE_BUT_UNVERIFIED`, and `NOT_FOUND`. These labels concern what the evidence establishes for this specific target, not whether a binary exists somewhere.

| Method/service | Status | Evidence and limit |
|---|---|---|
| FTP file transfer | **CONFIRMED** | Operator's successful login/download/upload and banner. It is a file service, not an interactive shell. |
| FTP chroot/config mapping | **POSSIBLE_BUT_UNVERIFIED** | CMS strings show generated `DO_CHROOT="yes"` config and a `StartingFolder` field. Actual generated config and `ayad` mapping were not collected. |
| SSH interactive shell | **PRESENT_BUT_DISABLED** | `/bin/sshd` exists, and CMS strings reference `/var/sshusers.cfg` and `killall sshd`, indicating management code. No SSH launch in `/etc/profile`, `/etc/inittab`, `/etc/init.d/rcS`, or `/etc/insmod_all.sh` was found; no active service/config/login is evidenced. Do not enable it. |
| Telnet interactive shell | **POSSIBLE_BUT_UNVERIFIED** | `/bin/telnetd` exists; `/etc/insmod_all.sh` requests `atpsync dynapp telnetd true`. This is a dynamic-app control call, but its effect, runtime state, listening port, login path, and authorization are not established. `/etc/passwd1` assigns telnetd shell `/bin/false`. No telnet access was tested or should be attempted as a deployment assumption. |
| Firmware respawn shell | **POSSIBLE_BUT_UNVERIFIED** | `/home/ayad/build-output/rootfs/etc/inittab` contains `::respawn:-/bin/sh`; the `tty2::askfirst:-/bin/sh` line is commented. Respawn alone does not reveal stdio/tty or expose an operator terminal. |
| Serial/UART shell | **POSSIBLE_BUT_UNVERIFIED** | `/etc/devicetable` creates `/dev/ttyAMA0` and `ttyAMA1`; `/etc/securetty` lists generic serial devices. Neither identifies board pads, UART routing, voltage, baud, login behavior, or an authorized procedure. Published material found for HG630B is a different designation/board, not an exact VER.B service document. Exact hardware documentation is **NOT_FOUND** in supplied repo/firmware and no matching verified vendor procedure was established. |
| Debug/maintenance shell over web/FTP | **NOT_FOUND** | Static web sources show typed admin flows and USB storage management, not an interactive shell route. `diagnose.lua` calls local `sys.exec` internally, but this is not a documented remote command shell and must not be repurposed. No hidden endpoint or exploit is authorized. |
| BusyBox shell availability | **CONFIRMED in firmware image** | `/bin/busybox` is ARM ELF and contains `ash` and `/bin/sh` strings; `/etc/inittab` references `/bin/sh`. This confirms a shell implementation exists in the image, not operator access. |

No supported operator-accessible shell method is established. A binary's presence or a startup control call does not establish service availability. No router settings/services were touched.

## Runtime compatibility matrix

The artifact is the unchanged `/home/ayad/build-output/openlinux-runtime-v1.2.tar.gz`, 4,417 bytes, SHA-256 `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`.

| Requirement/question | Assessment | Evidence |
|---|---|---|
| Shell interpreter | **PRESENT; target execution unverified** | Firmware `/bin/busybox` has `ash`, `/bin/sh` is referenced by inittab. Runtime uses POSIX shell syntax. |
| BusyBox commands | **PRESENT in static strings; target invocation unverified** | Runtime requires `date`, `mkdir`, `rm`, `sleep`, `kill`; the BusyBox string table contains these. `rmdir` is invoked through `/bin/busybox rmdir` fallback. `tar` and gzip support strings exist. |
| Extraction | **POSSIBLE_BUT_UNVERIFIED** | OEM BusyBox appears to include tar/gzip handling, but no target extraction is performed. FTP already places archive on the volume; this does not establish the OEM's tar behavior. |
| Writable USB destination | **PARTIALLY VERIFIED** | FTP upload works. Local writable path/owner/mode and whether archive can be extracted there by an authorized shell remain unknown. |
| Executable USB payload | **NOT ESTABLISHED; likely blocked on common listed filesystems** | NTFS/VFAT/HFS+/ext3 mount commands carry `noexec`; ext2 path is inconclusive. Current filesystem and live flags are unknown. Runtime launcher and daemon must be executable, and scripts invoke `/bin/sh`; no target exec test exists. |
| State files | **Package-contained** | `openlinuxctl` places lock, pid, and log under `$BASE/var`; `openlinuxd` logs there. It does not require writable `/var` outside the package. The package root itself must be writable. |
| OEM readiness markers | **Available after observed OEM initialization, not live-checked** | `/etc/profile` creates `/dev/caldata` symlink and runs `mic`; runtime requires that symlink plus a `/proc/*/comm` equal to `mic`. These markers are not proof of DSL/Wi-Fi health. |
| start/status/stop | **Conditional only** | Implemented by `openlinux/bin/openlinuxctl`; use absolute path. `start` checks marker, dependencies, writable package root, and process state. `status` and `stop` use procfs and PID verification. None has been run on HG630. `stop` uses kill; uninstall has fixed package-owned paths and ownership marker checks. |
| Runtime payload completeness | **Monitor scaffold only** | `analysis/openlinux/v1.2/runtime-implementation.md`; no OpenLinux network service is implemented and `NETWORK_MODE` must stay disabled. |
| QEMU result | **Not proof of HG630 compatibility** | Existing v1.2 validation explicitly uses VExpress A9 and separate static BusyBox; the target is a different HiSilicon platform. |

### Exact blockers

1. No supported shell method for this exact unit is established. FTP cannot execute commands.
2. No live local path, filesystem type, mount options, or executable-bit behavior was confirmed for either `Lexar___...usb1_1` or `_2`. For four firmware mount paths, `noexec` is explicit.
3. Local visibility of FTP uploads at a usable mount path remains an inference from CMS/web code, not a live observation.
4. OEM tar extraction and all V1.2 commands/readiness checks have not run on target.
5. No deployable network/service payload exists in V1.2; this investigation concerns only its monitor scaffold.

## Conditional manual deployment design

Do not perform this procedure until an authorized shell is established and target checks show the selected location is writable and executable. It intentionally avoids flash, startup files, service enablement, and router configuration changes.

1. From the authorized shell, read-only inspect `/proc/mounts`, `/proc/filesystems`, `df`, and `ls -ld`/`ls -l` for the actual mounted volume and archive. Confirm exact mount path, filesystem, free space, writable status, and absence of `noexec`; do not choose an unverified path. Verify the archive hash on the router if available, or compare its hash to the operator-verified value before use.
2. Select a dedicated new directory on the verified writable/executable volume; ensure it does not already exist. Extract only the top-level `openlinux/` package using available tar/gzip support, without extracting over existing files. Inspect `.openlinux-owner`, `manifest.json`, file list/modes, and configuration (`NETWORK_MODE=disabled`).
3. Verify `/bin/sh`, required BusyBox applets, `/proc`, writable package-contained `var` state, `/dev/caldata` symlink, and a `mic` process. If any check fails, stop without starting.
4. Start manually by the absolute path `.../openlinux/bin/openlinuxctl start`. Then run `status` and inspect `.../openlinux/var/log/openlinux-runtime.log`; confirm the monitor PID and `network=disabled` lines. Keep normal OEM services untouched.
5. Stop with the absolute path `.../openlinux/bin/openlinuxctl stop`; verify `status` reports stopped and the PID/lock are gone. For removal, use `.../openlinux/sbin/openlinux-uninstall` and review its ownership marker/path checks first. Remove only this marked package and its private state. Because USB mount behavior and target shell remain unknown, this is a future conditional design, not an instruction to run now.

## Recommended next operator action

Request from Huawei or the authorized service provider the documented, approved service-console access method and exact HG630 V2 VER.B board pinout/electrical levels. Once shell access is legitimately established, collect read-only live mount/filesystem output for the two Lexar partitions. Do not enable SSH/Telnet, use firmware/config uploads as a transport, invoke commands through FTP/web upload, or modify OEM configuration.

## Evidence provenance

Firmware references above are exact paths in `/home/ayad/build-output/rootfs` from the extracted firmware. Runtime requirements are read from the unchanged V1.2 archive and corresponding tracked V1.2 implementation/validation files. FTP observations and archive hash verification are operator-provided confirmations. No live target data beyond those operator observations is claimed.
