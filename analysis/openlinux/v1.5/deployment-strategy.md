# OpenLinux V1.5 — Full Deployment Strategy and Firmware Integration

Date: 2026-11-11. Target reported by operator: Huawei HG630 V2, VER.B, OEM `V100R001C298B010`. This investigation combines static analysis already recorded for the supplied firmware extraction, the V1.2 runtime package, prior RootFS build experiments, and a web search of public firmware/support sources. No router was contacted, no service/configuration was changed, no image was submitted to an updater, and no firmware was flashed.

## Executive result

**Recommended route:** develop OpenLinux as a small additive userspace running on top of the OEM Linux 2.6.30 kernel and Huawei/Triductor hardware stack. First target a manually started monitor/service from a verified executable RAM-backed location after an authorized shell exists. For persistence later, investigate a minimal additive OEM RootFS rebuild only after recovery, updater authentication, board identity, and physical validation gates are closed.

This is an architecture recommendation, not a deployment claim. Today, no authorized interactive shell method is established, no live writable/executable location has been confirmed, and the current V1.2 package is only a monitor scaffold. Its tracked build source also lacks `build/runtime/etc/openlinux.conf`, so the repository’s current runtime packaging/tests do not reproduce the published archive without resolving that discrepancy.

### Ranked approaches

| Rank | Approach | Current result | Main blocker |
|---:|---|---|---|
| 1 | **A. OEM userspace deployment** | Best preservation potential; technically plausible for scripts/native ARM services that use the OEM kernel, but not established on the router. | Authorized shell/access and a usable writable/executable location. Current V1.2 is only a monitor. |
| 2 | **B. USB deployment** | Transfer is confirmed. Direct execution from USB is unproven and likely blocked on the common filesystems whose mount commands specify `noexec`. Copy/extract to `/tmp` is a stronger conditional option. | Shell access; live `/tmp` mount flags/capacity; local visibility and target start test. |
| 3 | **D. OEM RootFS integration** | A historical additive RootFS candidate fits the fixed compressed span and retains OEM content. It is useful for research, not currently deployable. | No proven automatic hook, no legitimate update/signing path, no recovery, and no target boot. |
| 4 | **E. Modified firmware package** | Host-side assembly has produced same-size experimental containers preserving original kernel bytes. This does not establish acceptance, bootability, or recovery. | OEM authentication/format semantics, flash map, exact boot protocol, and independent recovery. |
| 5 | **C. Existing third-party firmware** | No build for the exact ARM/HiSilicon HG630 V2 VER.B board was found. The public OpenWrt “HG630” entry is a different Broadcom/MIPS family and says “Not supported.” | No exact board support, DSL stack, board data, boot adaptation, or verified recovery. |

The ordering prioritizes preservation and evidence rather than theoretical feature coverage. Approaches D and E share the OEM platform but differ in whether the objective is an integrated RootFS image or a complete updater container.

## Confirmed platform and runtime constraints

### Exact supplied firmware evidence

Repository analyses identify the supplied package as `HG630V2-12V100R001.bin`, software `V100R001C298B010`, SHA-256 `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`. The original image is not stored in Git; the extracted RootFS is available in the operator workspace at `/home/ayad/build-output/rootfs`.

From the extracted kernel/modules and analyses:

- ARM 32-bit EABI5 Linux 2.6.30, little-endian userspace, HiSilicon SD56xx/SD5610x family. Exact SoC stepping, RAM, physical flash, bootloader identity, and exact VER.B PCB are not proven by package strings.
- The OEM RootFS uses BusyBox 1.9.1 and uClibc 0.9.32.1-git. Its BusyBox ELF is ARM EABI5. The shell runtime can use POSIX shell and OEM applets; any new native executable needs an ABI-matched ARM EABI/uClibc toolchain and audited libraries.
- The RootFS includes Huawei/HiSilicon network and PHY modules, Triductor DSL modules/tools (`tri_ctl.ko`, `ipcdrv.ko`, `xdslcmd`, `xtmcmd`), Ethernet SDK components, and multiple optional Wi-Fi modules. The active Wi-Fi chipset and which optional driver is used on this exact board are still unknown.
- Startup uses OEM `/etc/profile`: temporary mounts, device creation, `startbsp`, `hi_xpon`, `hsanportinit`, `insmod_all.sh`, `/dev/caldata -> /dev/mtd9`, then `/bin/mic`. This runtime sequence is the known DSL/network preservation path. `/dev/mtd9` semantics are not mapped, so calibration protection cannot be inferred from the symlink alone.
- There is no proven container boundary. `chroot`, if present, would only change pathname resolution; Linux 2.6.30 namespace/cgroup support and configuration are unknown. OpenLinux must be treated as an additional set of processes sharing the OEM kernel, network stack, devices, and global state, not as an isolated second machine.

### Runtime implementation status

- V1.2 `openlinux-runtime-v1.2.tar.gz` is 4,417 bytes with SHA-256 `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`. It contains shell scripts/configuration and a monitor scaffold; it does not contain the planned OpenLinux network/service payload. Its `NETWORK_MODE` must remain disabled.
- Runtime state is package-contained under `$BASE/var`; it does not need writable OEM `/var`. It requires `/bin/sh`, BusyBox commands, `/proc`, a writable package root, `/dev/caldata` link, and a process named `mic` for its readiness check.
- Existing `build/experimental/openlinux-overlay` is an older userspace integration prototype. Its network action is deliberately dry-run; its init hook says it is not called by OEM `rcS`. The expected overlay `etc/openlinux/openlinux.conf` is absent in the tracked tree. Do not conflate this prototype with the V1.2 tar archive.
- Existing QEMU success is on VExpress A9 with a different kernel/DTB and static BusyBox. It does not validate HiSilicon boot, DSL, Ethernet, Wi-Fi, or the OEM kernel.

## Approach A — OEM userspace deployment

### Access options

| Method | Evidence/status | Practical conclusion |
|---|---|---|
| SSH | `/bin/sshd` is in RootFS; inspected OEM startup files do not launch it. CMS strings suggest SSH management state exists. **Present but disabled/unverified.** | No assumed SSH route; do not enable or modify settings in this phase. |
| Telnet | `/bin/telnetd` exists; `insmod_all.sh` sends `atpsync dynapp telnetd true`; account shell is `/bin/false`. Effect and live state are unknown. **Possible but unverified.** | Not an established authorized shell. |
| UART/service console | `inittab` respawns `-/bin/sh`; the tty-bound `tty2` entry is commented. `/dev/ttyAMA0` and `ttyAMA1` are provisioned, but exact board pads/routing/electrical levels/login are undocumented in supplied evidence. **Possible but unverified.** | Obtain exact VER.B service documentation through Huawei/authorized service. A similar HG658c/HG630B console report is not a pinout for this unit. |
| Vendor `mic`/dynamic app | OEM starts `/bin/mic`; `insmod_all.sh` uses `atpsync dynapp ...`; binary strings show process/fork/exec/restart behavior and service names. | `mic` is the vendor service manager, but no documented extension/registration ABI or safe third-party service contract is established. Do not register OpenLinux through guessed RPC/config. |
| Admin web maintenance | Firmware UI implements typed firmware, configuration, certificate, storage flows. Internal `sys.exec` in diagnostics does not create a documented remote shell. | No supported web shell or arbitrary-file execution route found. Vulnerability-based access is out of scope and not an acceptable deployment path. |
| FTP | Operator confirms upload/download and login. Firmware config supports chroot and a configurable starting folder. | Transfer only. FTP is not a shell and upload success proves neither file execution nor local path mapping. |

No access method is confirmed as an operator-accessible shell for this exact VER.B unit. Existing vendor services should not be reconfigured to obtain one.

### Running as an additional OEM userspace layer

This is the strongest eventual route for preserving DSL/Ethernet/Wi-Fi: leave the vendor kernel, modules, startup ordering, and network services authoritative; launch only separately named OpenLinux processes after OEM readiness. Manual start after `mic` and `/dev/caldata` are present is the least coupled model. The current launcher’s readiness markers are useful gates but do not confirm DSL/Wi-Fi health.

The old shell service prototype includes experimental network/DHCP/firewall/SSH controls. Those must not be activated alongside Huawei services without verified interface ownership, firewall ownership, DHCP/DNS integration, and process coexistence. For the current scaffold, only its monitor can be considered, with `NETWORK_MODE=disabled`.

**Assessment:** technically feasible as shared-kernel userspace in principle; actual startup is **BLOCKED** by shell access and target validation. This approach preserves OEM firmware if it uses verified RAM/USB storage and no persistent config changes.

## Approach B — USB-based deployment

### Existing USB path

V1.3 confirms the operator can log into FTP, see two Lexar volumes, download the archive, and upload `test.txt`. Static firmware analysis maps USB account roots through `/mnt`; CMS strings include USB mount command/path construction. Exact live mount paths, active filesystem types, ownership and mount flags have not been collected.

The CMS mount-option strings specify `noexec` for NTFS, VFAT, HFS+, and ext3. The ext2 command string does not show an explicit option, but this does not prove that the connected Lexar partitions are ext2 or that their live mount is executable. FAT-like filesystems also do not store Unix owner/mode bits normally. Direct archive execution is therefore not established.

### Conditional options after authorized shell access

1. **Extract/copy into `/tmp` (preferred USB-assisted experiment):** `/etc/profile` mounts `/tmp` as tmpfs without an explicit `noexec` option. FTP can stage the archive on USB; an authorized shell could read it and extract into a new directory on `/tmp`, then set/check the script modes and run the monitor. This avoids depending on USB execute support and is naturally volatile. Live `/tmp` flags, available RAM, and execution still need read-only verification on target. Do not use `/var` or `/mnt` as presumed RAM alternatives without checking whether USB mounts cover them.
2. **Run from ext2 USB:** potentially viable only if the actual medium is ext2 and the live mount lacks `noexec`, is writable, and preserves modes. The CMS ext2 string is insufficient evidence; target verification is mandatory.
3. **Run directly from existing NTFS/VFAT/HFS+/ext3 volume:** not a supported assumption; firmware mount strings explicitly set `noexec`. A shell interpreter can read a script on some noexec mounts, but V1.2’s launcher checks executable status and expects its daemon file executable. Noexec/mode semantics mean direct use is not established.
4. **Extract to OEM rootfs:** original SquashFS is read-only; not an available write target without a firmware rebuild.

OEM BusyBox has `tar` and gzip-related strings, making extraction plausible, but target extraction/options were not run. A V1.2 archive is small enough to make RAM staging practical in size terms; available target RAM and tmpfs capacity remain unknown. All options still require an authorized shell; FTP by itself cannot start a process.

**Assessment:** USB is a useful carrier, not a proven runtime. USB-to-`/tmp` is the leading no-flash trial once shell access is established and `/tmp` is confirmed executable and sufficiently writable.

## Approach C — Existing third-party firmware

Search date: 2026-11-11. Search covered OpenWrt device support, HG630 V2/VER.B/firmware version strings, SD5610x/SD56xx, public code-hosted projects, and community firmware/recovery references.

| Candidate | Exact target match | Kernel/arch and hardware support | Image/boot/recovery evidence | Result |
|---|---|---|---|---|
| [OpenWrt Huawei HG630 device page](https://openwrt.org/toh/huawei/hg630) | No. It groups HG630, HG630-52 and HG630b variants; its table describes Broadcom BCM63168 MIPS/CFE family and labels devices “Not supported.” | BCM63xx MIPS drivers cannot run on this firmware’s ARMv7/HiSilicon SD56xx kernel. DSL/Wi-Fi/board data for this unit are not represented. | No supported image/DTB/flash layout or exact VER.B recovery. Page describes an unrelated CFE platform. | **Reject as incompatible evidence.** Same retail string is insufficient. |
| [OpenWrt HG658c V2 issue #25771](https://github.com/openwrt/openwrt/issues/25771) | No. Different HG658c V2, VER.A, different firmware; user report describes HiSilicon SD5116/Hi5610. | Related platform discussion, not a build. The issue itself reports no upstream HiSilicon support and no open-source xDSL stack; it does not supply an image. | Hi-Boot/UART/NAND material is for that other board and cannot be copied to HG630 V2 VER.B. | **Research lead only; not installable firmware.** |
| [Huawei MUT unbrick tool](https://github.com/Rezurmas/huawei-mut-unbrick-tool) | No verified match. Its README's HG630V2 preset labels the SoC Broadcom and asks for a generic restore pack; that conflicts with the supplied target RootFS/kernel’s ARM/HiSilicon evidence. | Host recovery utility, not firmware. | Community code claims multicast recovery support, but model preset/layout details are partly speculative and do not verify exact C298B010/VER.B compatibility. | **Not a compatible firmware or verified recovery method. Do not use on this target based on its model name.** |
| [Firmware Mod Kit HG630V2 request #182](https://github.com/rampageX/firmware-mod-kit/issues/182) | Refers to HG630V2, but asks to add extraction/rebuild support. | Generic firmware-modification tooling; no device runtime, kernel, or drivers. | Open request does not provide an image, target boot method, flash map, or recovery. | **Tooling request only, not firmware.** |

No exact third-party firmware image/repository supporting Huawei HG630 V2 VER.B + this ARM/SD5610x firmware + working DSL was found. The popular OpenWrt HG630 profile is a different hardware family. A future port would require board-specific boot support and an open or legally usable DSL/Wi-Fi driver stack; those pieces are not present in mainline evidence reviewed here. **Assessment: no candidate currently viable for preserving all requested functions.**

## Approach D — Integrate OpenLinux into OEM RootFS

### Capacity and ABI

- Fixed RootFS reserved span: 5,931,008 bytes, from package offset `0x305cf` to original kernel offset `0x5d85cf`. Original SquashFS internal bytes used: 5,930,917. The package has only 91 bytes of original slack.
- A historical sorted additive overlay candidate at `/home/ayad/build-output/custom-build/overlay-final-4.2-sort-20261110/rootfs.squashfs` is 5,914,624 bytes on disk and 5,914,229 internal bytes, leaving 16,779 bytes below the fixed internal limit. It adds four files and was host-extracted/compared against the staged overlay. This is a build-output artifact, not tracked source and not a target-tested RootFS.
- The candidate is an older service prototype, not the V1.2 package. Rebuilding V1.2 into this span has not been demonstrated. The compressed margin is small; the existing runtime package is tiny, but adding an unimplemented native service/dependencies can exceed it. No OEM files should be deleted to force a fit.
- POSIX shell files can use OEM BusyBox/uClibc environment. Any compiled service should match ARM EABI5, OEM uClibc 0.9.32.1-git, loader path and kernel ABI. Do not replace OEM BusyBox, libc, loader, drivers, `mic`, DSL stack or network daemons without independent proof.

### Integration and preserved functions

- Safe automatic hook: **not established**. OEM `rcS` only sets PATH/prints. `/etc/profile` is reached through the respawn shell and executes the critical hardware initialization. Adding a command there can repeat on shell respawn; changing `rcS` risks changing boot sequencing. The existing OpenLinux `/etc/init.d/openlinux` hook is not called by OEM startup.
- `mic` is launched after hardware setup, but no supported third-party service registration ABI or config schema was found. Its presence does not establish that a custom app may be registered safely.
- Manual launch from a verified shell after OEM startup is the least risky first test. Automatic startup should wait for exact service manager documentation and a proven one-shot, failure-isolated hook.
- Retaining the original RootFS files, kernel and modules is a necessary preservation property, not proof of working DSL/Ethernet/Wi-Fi. Active Wi-Fi driver selection, calibration partition mapping, and full runtime service health must be checked on target. No RootFS write or target boot has occurred.

**Assessment:** technically plausible to integrate additive scripts into the OEM RootFS while retaining vendor stack; offline capacity evidence exists for one older overlay. Automatic launch and actual hardware function preservation are **BLOCKED/UNKNOWN**.

## Approach E — Build a modified firmware image

### What has been built and what it proves

- The supplied container is 7,563,600 bytes. Package structure places SquashFS at `0x305cf` and original ARM uImage at `0x5d85cf`; the original kernel header and payload CRCs validate.
- Existing builders can replace only the reserved RootFS byte span while retaining package length and original kernel/suffix bytes. Previous output includes `HG630V2-12V100R001-openlinux-final-experimental.bin` (SHA-256 `222cc9cd1aa0406826dd81d5237e1634690564014fcafa4e072451193dce4e3e`) marked `EXPERIMENTAL_NON_FLASHABLE`.
- Same-size assembly, SquashFS extraction, and unchanged kernel bytes prove host artifact properties only. They do not prove Huawei updater acceptance, component selection, correct root MTD, kernel mount, DSL bring-up, or recovery.

### Blocking update/boot/recovery gates

1. **OEM package contract:** metadata sections have unknown semantics; extents exceed package length, so they are not physical offsets. The branch connecting section IDs to MTD/update modes is unresolved.
2. **Integrity/authentication:** updater code references security wrappers and RSA/SHA primitives; signed byte range, outer checksum, public key, required signature, and legitimate signing key are unknown. No supported unsigned update path is proven.
3. **Physical flash and boot:** actual flash part/geometry, partition table, bootloader identity/board ID, MTD mapping, root mount args, and ATAGS/device-tree handoff for this VER.B unit remain unknown. Package `board_id=1212` is not proof of CFE/Hi-Boot ID.
4. **Recovery:** no verified exact-board console, bootloader recovery procedure, full flash backup/read-back method, or tested restore route is available. A router settings backup is not a full flash backup. A generic community recovery preset is not proof.
5. **Function preservation:** no hardware boot has shown DSL sync, Ethernet switching, Wi-Fi/calibration, or OEM service coexistence after a RootFS change.

### Safe future phase boundary

Only after a separately authorized phase establishes exact hardware and bootloader identity, legitimate update/signing/recovery contract, full verified backup and independent restore, exact RootFS mount compatibility, and a spare identical test unit should a candidate image be considered for a controlled test. Until then, keep all outputs `EXPERIMENTAL_NON_FLASHABLE`; do not upload them to Software Upgrade or multicast recovery tools and do not write MTD/bootloader/calibration.

**Assessment:** image construction is a useful laboratory path; deployment/flash is **BLOCKED**. It is less safe and less practical than OEM userspace until all gates close.

## Practical route and acceptance gates

1. Obtain a documented, authorized shell mechanism for exact HG630 V2 VER.B. Do not activate SSH/Telnet or use a vulnerability or upload endpoint.
2. From that shell, perform read-only inventory: kernel release/architecture, `/proc/mounts`, `/proc/filesystems`, interface names, free RAM/tmpfs capacity, `/dev/caldata` link, `mic` state, and visible service/DSL/Wi-Fi health. Collect no credentials or calibration contents.
3. Stage unchanged V1.2 package by the already working FTP transfer; extract into a new directory under `/tmp` only after confirming its mount is writable and executable. Verify archive hash, modes, dependencies and readiness markers; run only the network-disabled monitor manually; check status/logs; stop and remove its package-owned files. This demonstrates only the monitor, not a full OpenLinux network environment.
4. Before adding services, define which OEM service owns LAN/WAN interfaces, firewall, DHCP/DNS and Wi-Fi. Keep OpenLinux network scripts in dry-run until there is a reviewed handoff design and rollback plan.
5. If persistent boot integration remains necessary, first use a separate identical spare router and verified recovery environment. Then investigate a no-deletion OEM RootFS overlay preserving vendor binaries and the original kernel; do not integrate through `mic` or OEM startup until its supported extension point is documented.
6. Treat full modified firmware flashing as a later, separately approved project phase after signature, MTD, calibration, boot and recovery evidence is proven. Build and review the image before that approval; no flashing is authorized by this investigation.

## Evidence index

Local tracked evidence:

- `analysis/openlinux/v1.1/hardware-platform.md`, `analysis/platform/report.md`, `analysis/boot-validation/report.md` — ARM/HiSilicon platform evidence and remaining hardware unknowns.
- `analysis/openlinux/v0.4/init-order.md`, `vendor-dependencies.md`, `compatibility-audit.md` — OEM startup, service manager and userspace compatibility.
- `analysis/openlinux/v1.3/usb-runtime-investigation.md` — FTP, USB paths/options, shell access and runtime-specific findings.
- `analysis/server-run/rootfs-size-investigation.md`, `overlay-fit-report.md` — fixed span and host-only fit experiment.
- `analysis/openlinux/v1.0/flash-format.md`, `analysis/openlinux/v1.1/updater-static-analysis.md`, `recovery-status.md`, `docs/RECOVERY.md` — package/update and recovery blockers.
- `analysis/openlinux/v1.2/runtime-implementation.md`, `runtime-validation.json` — runtime behavior and VExpress-only validation.

Public source review:

- [OpenWrt Table of Hardware: Huawei HG630](https://openwrt.org/toh/huawei/hg630) describes a Broadcom BCM63168/MIPS family and marks these models unsupported; it does not support this extracted ARM/HiSilicon unit.
- [OpenWrt issue #25771 for Huawei HG658c V2](https://github.com/openwrt/openwrt/issues/25771) is an adjacent but different HiSilicon model and a porting discussion, not a compatible firmware image.
- [Huawei MUT unbrick tool](https://github.com/Rezurmas/huawei-mut-unbrick-tool) is a community transfer/recovery utility, not firmware. Its HG630V2 preset calls it Broadcom, conflicting with the inspected target platform; compatibility is not established.
- [Firmware Mod Kit HG630V2 support request #182](https://github.com/rampageX/firmware-mod-kit/issues/182) requests generic tool support and supplies neither an image nor a tested device recovery path.

Search absence is bounded to the sources and terms listed above; it is not proof that no private, regional, ISP or unindexed image exists. Any newly supplied candidate must be compared by exact PCB/hardware revision, SoC, kernel ABI, bootloader, flash layout, DSL/Wi-Fi stack and recovery procedure before being ranked as compatible.
