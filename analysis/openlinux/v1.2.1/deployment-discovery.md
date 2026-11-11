# V1.2.1 HG630 V2 runtime deployment discovery

Date: 2026-11-11. Scope: static host-side inspection of the preserved extracted OEM RootFS and V1.2 archive. No OEM executable was run; no device contacted, file uploaded, endpoint invoked, or flash/configuration/startup file changed.

## Finding

**No legitimate transfer-and-execution path is established.** The strongest next candidate is direct operator-controlled shell access through an authorized, documented console/service mechanism, followed by manually providing the package through an operator-controlled removable medium or an already supported network transfer client. The artifacts prove neither that such access is available to this operator nor that USB mass-storage host support is present. Do not infer deployment from admin upload controls: those are specific image/configuration/certificate workflows.

## Transport and access options

| Option | Status | Evidence and limit |
|---|---|---|
| SSH server | UNKNOWN | `/bin/sshd` exists (ARM EABI5), but inspected `/etc/inittab`, `/etc/profile`, and startup scripts do not launch it. No authorized login path, enabled state, keys/config, or transfer subsystem was established. |
| Telnet server | UNKNOWN | `/bin/telnetd` exists, not launched by inspected startup files. No authorized/active service or credential is established. Plain Telnet should not be presumed safe or enabled. |
| FTP server | UNKNOWN | `/bin/bftpd` exists, not launched by inspected startup files. Runtime `/var/ftp` is provisioned by `devicetable`, but `/var` is tmpfs; no service/configuration or permitted login was proven. |
| HTTP(S) admin firmware upload | BLOCKED as runtime transport | Static `webimg` shows `uploadimage.cgi` multipart form with field `imagefilename` on the software upgrade view. This is firmware upgrade workflow and must not be used for this runtime. Handler internals and endpoint behavior are not exercised. |
| HTTP(S) config restore | BLOCKED as runtime transport | Static `webimg` shows `uploadconfigfile.cgi`, field `configurefilename`, described as restoring a configuration file. Not a general file-storage endpoint. |
| HTTP certificate upload | BLOCKED as runtime transport | Static form uses `uploadcertification.cgi` for a certificate. Not general storage. |
| Admin web shell / arbitrary file store | UNKNOWN; no evidence found | `webidx`/`webimg` inventories web application routes and the observed upload forms are typed firmware, configuration, and certificate workflows. No general-purpose file manager or shell feature was found in the inspected static artifacts. This is not proof that every hidden server behavior is absent. |
| BusyBox wget / FTP/TFTP clients | PARTIALLY VERIFIED | OEM BusyBox embedded applet strings include `wget`, `ftpget`, `ftpput`, and `tftp`. This establishes compiled applets, not network reachability, auth, server availability, or an operator-authorized route. `wget` could retrieve to an operator-selected writable path only if a legitimate network path and invocation are independently established. |
| USB removable storage | UNKNOWN | `usbmount` binary and web UI USB storage-management code exist. However inspected kernel tree has only `drivers/usb/serial/option.ko`, no evident USB core/host/mass-storage or block-storage modules. USB driver loading lines in `insmod_all.sh` reference files that are absent from the inspected tree. FAT/VFAT/NTFS module load lines in `/etc/profile` are commented out, and corresponding kernel FS modules were not found. Physical USB disk support is therefore unproven. |
| UART/serial console | UNKNOWN | `/etc/inittab` respawns `-/bin/sh`, but contains no explicit tty binding (the `tty2` askfirst line is commented). This suggests a shell process exists, but does not identify a physical console, board UART pinout, serial settings, authentication/authorization, or safe operator connection. |

## Web administration static analysis

- `/etc/webimg` contains an upgrade view that posts `multipart/form-data` to `uploadimage.cgi`, with file field `imagefilename`, and CSRF token handling. It presents “Update Software” and firmware-upgrade error strings. This endpoint is expressly excluded from runtime deployment.
- The configuration view posts to `uploadconfigfile.cgi` with field `configurefilename`; accompanying UI says it restores previous settings. Download route `/api/system/downloadcfg` downloads a configuration backup. No code path indicates arbitrary path selection or general file storage.
- A certificate form posts to `uploadcertification.cgi`. This is certificate-specific.
- The existing media/USB web code refers to `/mnt` and USB account/directory APIs. `/mnt` is mounted as tmpfs by `/etc/profile`, so these references alone do not prove a mounted USB filesystem or durable storage.
- The static web application and server binaries were inspected as files only. No HTTP request was sent and no upload handler was invoked.

## Storage and reboot persistence

| Location | Status | Evidence and limit |
|---|---|---|
| `/tmp` | VERIFIED volatile writable filesystem configured | OEM `/etc/profile` mounts tmpfs at `/tmp`. Actual free space and mount success on a router are unverified. Contents do not survive reboot. |
| `/var` | VERIFIED volatile writable filesystem configured | OEM profile mounts tmpfs at `/var`; device table provisions `/var/ftp` and other runtime directories. Does not survive reboot. |
| `/mnt` | VERIFIED volatile writable filesystem configured; external mount UNKNOWN | OEM profile mounts tmpfs at `/mnt`. A removable filesystem could replace/be mounted over it only if supported and operator-authorized; no such actual mount is proven. |
| `/config` on `/dev/mtdblock7` | PARTIALLY VERIFIED | Profile conditionally mounts JFFS2 there only if `/etc/webimg1` exists. No evidence establishes this condition on the exact target, free capacity, operator write access, or suitability for arbitrary runtime files. Do not write there. |
| `/etc/tri_image_up` on `/dev/mtdblock12` | PARTIALLY VERIFIED | Profile conditionally mounts JFFS2 if the directory exists. It is named/used for image upgrade data; do not repurpose it. No arbitrary storage authorization or survival test exists. |
| OEM root (`/`) | BLOCKED for writes | Original root image is SquashFS and treated as immutable. No overlay writable root is established. |
| USB disk | UNKNOWN | USB management code and `usbmount` binary exist, but host/mass-storage and filesystem module evidence is missing or commented. Durability and mount point cannot be asserted. |

No safe persistent runtime location has been established. The only directly evidenced writable locations are RAM-backed and volatile. Conditional JFFS2 locations are not approved general storage and must not be used absent vendor documentation/operator authorization.

## OEM tools, extraction, and package integrity

- OEM BusyBox strings evidence applets `wget`, `ftpget`, `ftpput`, `tftp`, and `tar`; strings also show gzip support paths. Applet presence is verified statically; actual applet invocation was intentionally not performed.
- Actual V1.2 archive at `/home/ayad/build-output/openlinux-runtime-v1.2.tar.gz`: 4,417 bytes; SHA-256 `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`, matching the V1.2 record.
- Host-side read-only tar parsing found top directory `openlinux/` and `openlinux/manifest.json` (`openlinux-runtime-package-v1`). Every manifest-listed payload file's observed size and SHA-256 matched the manifest. `manifest.json` deliberately has no self-hash.
- Host-side archive parsing is not a test of OEM BusyBox `tar` extraction behavior. BusyBox includes `tar` and gzip-related strings, so extraction looks plausible but remains PARTIALLY VERIFIED on the target. No package content was changed.
- The package contains POSIX shell scripts only, with no compiled service binary or shared-library payload. It requires `/bin/sh`, the listed BusyBox applets, `/proc`, `/dev/caldata` symlink and an OEM `mic` process for its readiness checks. It is a monitor scaffold, not a working OpenLinux network/service payload. Package hash integrity does not establish physical compatibility or deployability.

## Operator-accessible shell mechanisms

**UNKNOWN:** inittab's `respawn:-/bin/sh` is evidence that init starts a shell, not that it is connected to an accessible serial console or safely available to an operator. The shell's terminal/stdio source and privileges have not been determined. Do not attempt undocumented credentials, hidden routes, debug interfaces, or vulnerability-based access. A documented vendor-authorized console/service procedure is required before considering this route.

## Recommended safe disposition

Do not deploy yet. The next action needed is for the operator to establish, through vendor documentation or their authorized service channel, whether this exact HG630 V2 has an approved serial/service-console shell and how to connect. If available, the operator can then independently verify read-only runtime readiness and writable volatile storage, and provide the unchanged archive through that authorized session. A reboot would erase a `/tmp`, `/var`, or `/mnt` tmpfs copy; no persistent method is currently supported by evidence.
