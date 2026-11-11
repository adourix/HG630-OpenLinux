# V1.6 — OEM SSH and PTY static audit

Date: 2026-11-11. Target reported by operator: HG630 V2 VER.B, firmware `V100R001C298B010`. Evidence is from the supplied extracted image at `/home/ayad/build-output/rootfs`. No OEM executable was run and no router was contacted or changed.

## Findings

| Topic | Finding | Confidence |
|---|---|---|
| `/bin/sshd` identity | Dropbear **2014.65**, based on the embedded `SSH-2.0-dropbear_2014.65` banner and Dropbear usage/diagnostic strings. It contains Huawei/ATP-specific modifications (`libgplutil.so`, ATP APIs, `/var/sshusers.cfg`, and vendor logging strings); it is not an unmodified upstream binary. | VERIFIED static |
| ABI | ELF32 little-endian ARM, EABI5, dynamically linked, interpreter `/lib/ld-uClibc.so.0`. RootFS provides uClibc 0.9.32.1-git and all named `DT_NEEDED` objects: `libz.so.1`, `libgplutil.so`, `libdl.so.0`, `libutil.so.0`, `libcrypt.so.0`, `libgcc_s.so.1`, `libc.so.0`. | VERIFIED static |
| Startup | No `sshd` invocation in `inittab`, `profile`, `rcS`, or `insmod_all.sh`. `mic` contains SSH and dynamic-app management strings, but the service activation state and its ATP configuration are not established. | VERIFIED static / runtime UNKNOWN |
| Shell | Dropbear strings identify the `shell` SSH channel and exec-related code. OEM `passwd1` specifies root shell `/bin/sh`; the root account is copied to `/var/passwd` during startup. This supports capability, not proof that a successful session reaches an interactive shell. | PARTIALLY VERIFIED |
| PTY | The binary imports `openpty`, `ioctl`, and terminal functions and contains `pty_allocate`/`pty_setowner` diagnostics. It supports PTY requests. Allocation on the target is not established. | VERIFIED capability / runtime UNKNOWN |
| Authentication | Strings show password authentication, public-key parsing, `authorized_keys`, and key option handling. The usage strings expose `-c` to disable password logins, `-g` to disable root password logins, and `-w` to disallow root logins. Root has an empty shadow field in the supplied `/etc/shadow`, so password-authenticated root access is unsafe to enable. A key-only policy is technically indicated by `-c`, but exact vendor semantics and effective auth policy are untested. | PARTIALLY VERIFIED |
| Key location | Strings include `/.ssh` and `%s/.ssh/authorized_keys`. No authorized key file exists in the extracted tree. Root's passwd home field is `/bin`, making `/bin/.ssh/authorized_keys` the likely root key path if this build uses the passwd home convention; custom Huawei auth logic may alter this. | INFERRED |
| Host keys | `/etc/handy_rsa_key` and `/etc/handy_dss_key` exist as binary SSH key blobs; Dropbear also mentions `/etc/dropbear/dropbear_ecdsa_host_key`, `-r`, and `-R` generation. Their provenance, whether the handy files are private host keys, whether they are shared across firmware units, and whether startup creates keys are unknown. Treat checked-in firmware keys as unsuitable until proven unique/private. | VERIFIED paths / suitability UNKNOWN |
| SFTP | The binary contains `/usr/libexec/sftp-server`, but that path does not exist in the extracted tree. SFTP subsystem availability is therefore not established. | PARTIALLY VERIFIED |
| Config/account files | No `/etc/ssh/sshd_config` or Dropbear config was found. `passwd1`, `group1`, and `shadow` are present; standard `/etc/passwd` and `/etc/group` are not present in the extracted image. Startup copies passwd/group sources into volatile `/var/passwd` and `/var/group`. `/etc/securetty` lists many tty names but does not itself prove SSH root-login policy. | VERIFIED static |

## CLI and implementation details

The embedded usage text includes `-b`, repeatable `-r`, `-R`, `-F`, `-E`, `-w`, `-c`, `-g`, `-B`, `-j`, `-k`, `-a`, `-p`, `-P`, `-W`, `-K`, `-I`, and `-V`. It advertises SSH-2, `ssh-rsa`, `ssh-dss`, `zlib@openssh.com`, `curve25519-sha256@libssh.org`, shell channels, PTY requests, and authorized-key options. These are binary strings, not a live `-h`/`-V` run; option acceptance and order-specific behavior remain untested.

`-B` explicitly allows blank-password logins and must never be used. Because `/etc/shadow` has an empty root hash field, never start this daemon with password authentication enabled. If an authorized service workflow is later established, a key-only policy (at minimum `-c`, with a fresh unique host key and a dedicated authorized key) is the least-bad candidate, but must first be validated against this Huawei build and its vendor policy. Do not put an invocation into OEM startup based on static strings.

## PTY and interactive-shell evidence

- `/etc/profile` mounts tmpfs on `/dev`, mounts proc and sysfs, then runs `makedevs -d /etc/devicetable /`. It does **not** mount devpts.
- `/etc/fstab` contains only `/proc`.
- `/etc/devicetable` provisions `/dev/ptmx` as character major 5 minor 2 and legacy `/dev/ptyp*`/`/dev/ttyp*` nodes. Those static nodes do not prove kernel Unix98 PTY support or working allocation.
- The extracted `/dev/pts` directory exists and is empty. There is no `/dev/pts/ptmx` node and no static `/dev/pts/N` slave. Dynamic Unix98 slave nodes normally appear through a mounted devpts filesystem.
- No devpts mount command or `devpts` string was found in the inspected startup/configuration files or the RootFS search. This is evidence that no mount is configured by the inspected OEM startup, not proof that no other runtime component mounts it.
- The exact target kernel `.config` was not supplied. `CONFIG_UNIX98_PTYS`, `CONFIG_DEVPTS_FS`, legacy PTY configuration, and PTY limits cannot be proven. A separate VExpress kernel configuration in the build workspace is unrelated and is not evidence about the HG630 kernel.

### PTY refusal diagnosis

The reported `Server refused to allocate pty` came from an earlier experiment on a related HG630 V2 firmware, not a captured session on this exact VER.B/C298B010 unit. The daemon's `openpty` use plus the absence of an OEM devpts mount in the inspected startup makes an unmounted devpts filesystem (or kernel PTY support/configuration) the strongest static explanation. Missing devpts is **not proven as the exact cause**: the related firmware may differ, the target may mount devpts elsewhere at runtime, and daemon-side policy/permissions can also reject allocation. `/dev/ptmx` alone is not proof of usable PTYs.

## Shell and account policy

`/bin/sh` is the OEM BusyBox shell, not an ATP CLI wrapper. The inittab entry `::respawn:-/bin/sh` starts it without assigning a named tty. It proves that init launches a shell process, but not that shell stdin/stdout point to a reachable UART or that a remote SSH session invokes it. `/bin/false` is configured for service accounts (`web`, `upnp`, `cwmp`, and others), so those accounts cannot be assumed to receive a shell. The `root` record in `passwd1` names `/bin/sh`; the root shadow field is empty. SSH's effective user database and Huawei authorization checks are not fully recoverable from static strings.

## Deployment disposition

**Do not enable SSH or modify the router as part of this host-side phase.** Existing Dropbear is a plausible reuse candidate and makes adding another daemon premature, but security and functionality are not yet established. No secure, supported SSH deployment artifact can be called target-ready until all of these are verified on an authorized maintenance path:

1. Exact daemon option behavior and Huawei user policy; no password or blank-password authentication.
2. Fresh, unit-unique private host key generation and protected storage; do not reuse the bundled `handy_*` files without proving they are unique private keys.
3. A dedicated nonempty authorized-key policy and effective authorized-key path/permissions.
4. LAN-only bind/firewall exposure with existing Huawei ACL behavior understood.
5. Kernel Unix98 PTY and devpts support, a devpts mount, and successful allocation; verify `/dev/pts` live rather than inferring from `/dev/ptmx`.
6. A normal interactive `/bin/sh` session and clean disconnect behavior, without replacing vendor services or init.
7. SSH daemon start/stop through a supported operator mechanism; no guessed `mic`/ATP command or web upload path.

Adding a Dropbear build is not justified yet: the OEM binary already is Dropbear and matches the RootFS ABI. Replacing it would add compatibility and footprint risks while the blockers are startup authorization, account policy, keys, and PTY setup. If later evidence shows a defect that cannot be safely configured, evaluate a pinned Dropbear release cross-built for ARM EABI5/uClibc 0.9.32.1-git, as an isolated optional component with its own key-only config and explicit manual start/stop. Do not overwrite `/bin/sshd`.

## Evidence scope and gaps

Paths examined include `/bin/sshd`, its ELF dynamic section and printable strings, `/lib` shared objects, `/etc/devicetable`, `fstab`, `inittab`, `profile`, `init.d/rcS`, `insmod_all.sh`, `passwd1`, `group1`, `shadow`, `securetty`, `/dev`, `/dev/pts`, and SSH/PTY-related file names and strings in the extracted RootFS. Static inspection does not validate daemon operation, current router settings, kernel configuration, live mounts, actual accounts, network exposure, or exact cause of a related-model PTY failure.

Prior reports `analysis/openlinux/v1.2.1/deployment-discovery.md`, `analysis/openlinux/v1.3/usb-runtime-investigation.md`, and `analysis/openlinux/v1.5/deployment-strategy.md` remain the deployment context. The requested V1.5 `recommended-architecture.md` and `firmware-compatibility-matrix.md` files were not present in the repository at audit time; architecture/compatibility findings are instead in `deployment-strategy.md` and `deployment-options.json`.
