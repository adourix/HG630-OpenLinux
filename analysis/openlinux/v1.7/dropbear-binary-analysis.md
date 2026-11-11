# V1.7 OEM Dropbear binary analysis

Date: 2026-11-11. Static host analysis of `/home/ayad/build-output/rootfs`; the ARM daemon was not executed. SHA-256 of `/bin/sshd`: `a9d072dac7e64f432b51e4c7c335084f6cea01991fba6dfc0e8fbafd47ce0ddb`.

## Identity, ABI, dependencies

`file`/`readelf` identify ELF32 little-endian ARM ET_EXEC, EABI5, interpreter `/lib/ld-uClibc.so.0`. Embedded SSH banner is `SSH-2.0-dropbear_2014.65`. It is Huawei-modified: imports/strings include `libgplutil.so`, `ATP_LOG_RecordItem`, ATP message APIs, `/var/sshusers.cfg`, Huawei-specific session/CLI strings, and non-upstream option spellings. This is not safely interchangeable with upstream Dropbear documentation.

DT_NEEDED libraries: `libz.so.1`, `libgplutil.so`, `libdl.so.0`, `libutil.so.0`, `libcrypt.so.0`, `libgcc_s.so.1`, `libc.so.0`. RootFS provides those objects and uClibc 0.9.32.1-git symlinks. No target execution was performed.

## QEMU user-mode CLI reference

The OEM ARM daemon was queried without treating it as a host-native executable:

```text
qemu-arm -L /home/ayad/build-output/rootfs /home/ayad/build-output/rootfs/bin/sshd -V
qemu-arm -L /home/ayad/build-output/rootfs /home/ayad/build-output/rootfs/bin/sshd -h
```

QEMU user mode printed `Dropbear v2014.65`, the full usage text, default keys (`/etc/handy_dss_key`, `/etc/handy_rsa_key`, `/etc/dropbear/dropbear_ecdsa_host_key`), default port 22, default PID `/var/run/dropbear.pid`, max 10 listen specifications, receive window 24576, keepalive 0, idle timeout 0. It also emitted `cache '/etc/ld.so.cache' is corrupt`; the CLI nevertheless completed. The output confirms argument/help code under this QEMU sysroot, not behavior on the Linux 2.6.30 target. No daemon socket, authentication, shell, or PTY was started.

The disassembly contains a direct `openpty@plt` call at `0x1844c`. It does not prove target kernel allocation.

## Embedded usage reference

The usage string (not a live help invocation) records:

| Option | Embedded description | Integration use |
|---|---|---|
| `-b bannerfile` | display banner before login | Not needed |
| `-r keyfile` | specify host key; repeatable | Supply explicitly provisioned ECDSA private host key |
| `-R` | create host keys as required | **Do not use:** defaults include `/etc/dropbear/dropbear_ecdsa_host_key`, inside the firmware root |
| `-F` | do not fork into background | Lifecycle manager starts and records its child |
| `-E` | log to stderr rather than syslog | Use with package-owned log redirection |
| `-w` | disallow root logins | Required |
| `-c` | disable password logins | Required; no fallback allowed |
| `-g` | disable password logins for root | Redundant with `-w`; root denied |
| `-B` | allow blank password logins | Never use |
| `-j` | disable local port forwarding | Use |
| `-k` | disable remote port forwarding | Use |
| `-a` | allow forwarded ports from any host | Never use |
| `-p [address:]port` | listen on address/port; repeatable | Bind to configured specific address, never wildcard |
| `-P PidFile` | PID file | Avoid relying on daemon-owned path; wrapper controls PID |
| `-W n` | receive window, max 1 MiB | Leave default |
| `-K n` | keepalive seconds, 0 disables | Leave default |
| `-I n` | idle timeout seconds, 0 disables | Leave default |
| `-V` | version | Could identify daemon if run on target; not run here |

No `sshd_config` parsing evidence was found. The only config-like path is Huawei `/var/sshusers.cfg`; schema and enforcement are unknown. Do not deploy OpenSSH directives.

## Authentication, host keys, algorithms

Strings show `password` auth, public-key parser paths, `authorized_keys`, `no-pty`, shell channel, and authorized-key options. `-c` says password auth can be disabled; exact patched runtime behavior is untested. `-B` explicitly enables blank passwords. Root's extracted shadow field is empty, making ordinary root password auth unacceptable.

Key algorithm strings include `ssh-rsa`, `ssh-dss`, and ECDSA `ecdsa-sha2-nistp256`, `nistp384`, and `nistp521`; key exchange strings include curve25519 and ECDH groups, plus legacy group1 SHA-1. Cipher/MAC strings include `aes128-ctr`, `hmac-sha1`, and `hmac-md5`. No `ssh-ed25519`, `rsa-sha2-256`, `rsa-sha2-512`, or HMAC-SHA2 string was found. This is a bounded strings observation, not a complete algorithm negotiation proof. The integration accepts only ECDSA P-256 user keys; RSA/SHA-1 and DSA are rejected. Host key generation is not included: `dropbearkey` is absent from RootFS, and `-R` writes to a compiled default under `/etc`.

Strings name `/etc/handy_rsa_key`, `/etc/handy_dss_key`, and default `/etc/dropbear/dropbear_ecdsa_host_key`; QEMU `-h` reports those exact defaults. The handy blobs' provenance/uniqueness are unknown and they are not reused. Authorized keys are searched under `%s/.ssh/authorized_keys`; root passwd home is `/bin`, but no key file exists. User home lookup may be affected by vendor patches.

PTY code imports `openpty`, `ioctl`, and termios APIs and contains allocation/ownership failures. Shell channel and `execv` are present. PTY capability is indicated, not target allocation success.

## Account, execution, logging, network, PID

The daemon imports `getpwnam`, `getspnam`, `getgrnam`, and `execv`; strings expose a `shell` channel and `/bin/sh` in account data. No evidence of a forced-command policy or restricted-shell option was found. Authorized-key `command=` parsing strings exist, but static strings alone do not prove enforcement and are not accepted as a security boundary.

`/etc/passwd` and `/etc/group` are absent in the extracted image. `/etc/passwd1` and `/etc/group1` are copied by `/etc/profile` to volatile `/var/passwd` and `/var/group`. There is no `openlinux` account. Non-root service accounts use `/bin/false`. `mic`/ATP strings include SSH dynamic-app/service management; the active policy and generated `/var/sshusers.cfg` are unknown.

Logging strings include syslog and Huawei ATP log APIs; `-E` selects stderr. `-F` prevents daemon fork. Default PID string is `/var/run/dropbear.pid`. `-p [address:]port` supports a specific bind address syntactically; whether the patched parser obeys this exactly is not runtime-tested. Binding a specific configured local address reduces exposure but cannot establish which address is LAN without live interface knowledge.

## Determination

Public-key shell capability is **PARTIALLY VERIFIED statically**. A secure service usable by this router is **BLOCKED**: no dedicated non-root shell account, no target key generator, no verified account database behavior, no live PTY/devpts evidence, no known SSH-user policy, and no end-to-end target authentication. Lifecycle tools therefore fail closed by default and refuse root. They do not claim authentication success.
