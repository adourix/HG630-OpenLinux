# V1.7 changelog

- Reverse-engineered the OEM Huawei-modified Dropbear 2014.65 CLI with ELF inspection, strings, ARM disassembly reference, and QEMU user-mode `-h`/`-V` queries.
- Added a read-only PTY/devpts preflight; it reports missing evidence and never mounts filesystems.
- Added optional, disabled-by-default SSH lifecycle/provisioning wrappers using existing `/bin/sshd`, with key-only/root-denied flags, specific-address binding, PID checks, and package-owned logs/state.
- Made the SSH integration refuse root and absent/unverified prerequisites; no Huawei account/config/startup files are changed.
- Added an additive RootFS builder with before/after manifests, allowlist, extraction verification, sorted overlay priorities, and OEM inode timestamp preservation.
- Added explicit unpinned experimental-rootfs support to the offline rebuilder. Output remains unsigned and `EXPERIMENTAL_NON_FLASHABLE`.
- Restored the V1.2 source `openlinux.conf` in V1.6; V1.7 updates it with SSH disabled. Preserved the previously generated V1.2 archive.
- Full test run: 112 passed, one optional VExpress test skipped. No SSH protocol/authentication or physical-device test was performed.
