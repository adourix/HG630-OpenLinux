# HG630-OpenLinux project context

## V1.6 OEM SSH/PTTY audit — 2026-11-11

- **VERIFIED static:** `/bin/sshd` is Dropbear 2014.65 with Huawei/ATP-specific customizations, ARM EABI5/uClibc dynamic ABI, and all declared dependency libraries present in the supplied RootFS. It contains public-key, authorized_keys, shell-channel, PTY, and SFTP-related strings; this does not prove those functions work on the router.
- **VERIFIED static:** inspected OEM startup does not launch `sshd` or mount devpts. `/etc/devicetable` creates `/dev/ptmx` and legacy pty nodes, while extracted `/dev/pts` is empty. The exact HG630 kernel config was not supplied, so Unix98 PTY/devpts support is UNKNOWN.
- **INFERRED:** missing devpts mount (or missing kernel support) is the strongest explanation for the earlier related-HG630 “Server refused to allocate pty” observation; its exact cause on the exact VER.B target is not established.
- **SECURITY BLOCKER:** root's supplied shadow field is empty. Never enable SSH password auth or Dropbear `-B`; use of the vendor daemon is not target-ready until its exact key-only policy, unique host key path, account restrictions, PTY behavior, and supported start mechanism are verified.
- **Disposition:** do not add a second SSH daemon or change OEM startup. Reuse of the existing customized Dropbear is preferred for future evaluation; no SSH enablement or target deployment occurred. See [V1.6 SSH/PTTY audit](analysis/openlinux/v1.6/oem-ssh-pty-audit.md).
- No exact hardware/kernel config was inferred from the separate VExpress build. Firmware, RootFS, settings, router services, MTD, and flash were not changed.
- **IMPLEMENTED:** restored the previously missing tracked `build/runtime/etc/openlinux.conf` with network mode disabled and allowed it through `.gitignore`; normalized runtime source modes. `tools/package_runtime.py` now reproduces the known V1.2 archive exactly (4,417 bytes; SHA-256 `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`) at `/home/ayad/build-output/openlinux-runtime-v1.2-rebuilt.tar.gz`.
- **TESTS:** full suite passes 93 tests (one optional VExpress QEMU test skipped because its inputs were not supplied). The suite does not test target SSH, PTY, or router behavior.

## V1.5 full deployment strategy — 2026-11-11

- **VERIFIED from the supplied OEM firmware analyses:** target userspace is ARM EABI5/uClibc on the HiSilicon SD56xx/SD5610x Linux 2.6.30 platform. The OEM `profile`/`startbsp`/`mic` path owns hardware and network initialization. No safe supported `mic` extension or one-shot automatic OpenLinux hook is known.
- **VERIFIED from prior host build evidence:** an older additive RootFS overlay fit the fixed span with 16,779 internal bytes remaining, preserving OEM files in host comparisons. It is not the V1.2 payload and was not target booted. Existing same-size firmware assemblies remain `EXPERIMENTAL_NON_FLASHABLE`.
- **INFERRED:** best future route is an additive userspace on the OEM kernel, manually started after an authorized shell and OEM readiness checks. USB-to-`/tmp` is the leading conditional staging option; live mount flags and target execution remain unknown.
- **UNKNOWN/BLOCKED:** no exact-board authorized shell, third-party image, verified flash/recovery procedure, OEM signing contract, or physical target deployment is established. OpenWrt's public HG630 profile describes Broadcom/MIPS variants, not this extracted ARM/HiSilicon firmware.
- **BLOCKED:** V1.2 is a monitor scaffold, not the full OpenLinux service payload; tracked `build/runtime/etc/openlinux.conf` is absent although the prior archive contains a config. Do not integrate/flash until the source/archive discrepancy and firmware/recovery gates are resolved.
- Details: [V1.5 deployment strategy](analysis/openlinux/v1.5/deployment-strategy.md) and [machine-readable options](analysis/openlinux/v1.5/deployment-options.json). No device, service, firmware, or MTD was modified.

## V1.3 USB runtime investigation — 2026-11-11

- **VERIFIED from operator observation:** USB is recognized, `bftpd` FTP login/download/upload works, and the FTP root shows two Lexar partitions. The V1.2 archive SHA-256 matches the expected `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`.
- **VERIFIED from extracted firmware:** USB CMS strings map storage management through `/mnt`; the explicit NTFS, VFAT, HFS+, and ext3 mount options include `noexec`. The ext2 mount string has no visible options. FTP-generated configuration includes chroot and a configurable starting folder.
- **UNKNOWN:** live local mount paths, filesystem types/options, FTP user's local mapping, execution of uploaded files, and an operator-accessible shell on this exact VER.B unit. SSH binary exists without an inspected startup launch; telnet has a dynamic-app request but live activation/access is unproven. `inittab` respawns `/bin/sh` without proving an accessible tty.
- **BLOCKED:** safe USB runtime deployment is not established. FTP transfer is not shell execution, and no live `exec` support was tested. Obtain the documented authorized exact-board console method, then inspect live mount information read-only.
- Details: [V1.3 USB runtime investigation](analysis/openlinux/v1.3/usb-runtime-investigation.md) and [machine-readable options](analysis/openlinux/v1.3/usb-runtime-options.json). No router configuration or service was changed; no target runtime test was performed.

Updated: 2026-11-11 America/New_York

## OEM-preserving runtime scaffold milestone — 2026-11-11

### VERIFIED

- Added a relocatable, shell-only runtime under `build/runtime/`, a deterministic packager in `tools/package_runtime.py`, operator launcher/shutdown/uninstall commands, manifest generation, host-mock tests, and V1.2 implementation/validation documentation.
- Runtime package `openlinux-runtime-v1.2.tar.gz` is outside Git at `/home/ayad/build-output/openlinux-runtime-v1.2.tar.gz`, size 4,417 bytes, SHA-256 `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`.
- Package defaults to network disabled and implements no network binding or interface changes. It verifies `/dev/caldata` symlink and a `mic` process in procfs before starting, uses an atomic package-private lock, refuses duplicates, verifies the child command line before signalling it, and limits state/uninstall actions to OpenLinux-owned paths.
- The complete repository suite passed 93 tests with the optional VExpress A9 QEMU runtime test enabled, including package extraction/control integration, host process mocks, and clean/unowned-file uninstall coverage. Tests do not execute OEM ARM binaries.
- `tools/package_runtime.py` manifest includes hashes, sizes, modes, dependencies and ownership rules. Package build is deterministic. No firmware or OEM RootFS file was modified; `EXPERIMENTAL_NON_FLASHABLE` is unchanged.

### INFERRED

- The readiness sentinels indicate the inspected profile advanced past its calibration-link setup and `mic` launch. They do not verify DSL, Wi-Fi, all Huawei services, or hardware compatibility.
- A writable external or RAM-backed directory can host the relocatable package if the operator independently confirms it. No router storage/transport path is established.

### UNKNOWN / BLOCKED

- No compiled OpenLinux ARM payload or target-compatible shared library set exists in the repository. A matching ARM EABI5/uClibc 0.9.32.1-git cross compiler/sysroot and identified service source/dependencies are still needed.
- No physical-router test was performed. A fresh runtime initramfs passed on QEMU VExpress A9 using the preserved non-OEM Linux 6.12 kernel/DTB and separately built static BusyBox. VExpress is not the HG630 HiSilicon platform; this QEMU pass does not prove HG630 compatibility.
- Network, DNS/DHCP, firewall, SSH, interface ownership, routing, vendor-service interactions and runtime behavior on Linux 2.6.30 remain unverified. Keep services disabled and retain `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`.

## V1.2.1 runtime deployment discovery — 2026-11-11

### VERIFIED

- Added `analysis/openlinux/v1.2.1/deployment-discovery.md` and machine-readable `deployment-options.json` after static inspection of the extracted OEM RootFS, `/etc/webimg`, `/etc/webidx`, startup files, OEM BusyBox applets, and kernel module tree.
- The actual V1.2 archive at `/home/ayad/build-output/openlinux-runtime-v1.2.tar.gz` remains unchanged: 4,417 bytes, SHA-256 `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`. Host-side tar inspection confirmed each manifest-listed payload file size/hash; manifest self-hash is intentionally null.
- `/etc/profile` configures tmpfs at `/tmp`, `/var`, and `/mnt`; these paths are volatile. Static web forms show `uploadimage.cgi` for firmware upgrade, `uploadconfigfile.cgi` for configuration restore, and `uploadcertification.cgi` for certificates. None is a general-purpose runtime file store.
- OEM BusyBox contains `wget`, `ftpget`, `ftpput`, `tftp`, and `tar` applet evidence. `/bin/sshd`, `/bin/telnetd`, `/bin/bftpd`, and `/bin/usbmount` are present. Their presence does not prove they run or are authorized access methods.

### INFERRED

- BusyBox tar/gzip support makes extraction of the unchanged package plausible, but OEM extraction was not executed; target extraction remains PARTIALLY VERIFIED.
- `/dev/caldata` symlink and respawned `/bin/sh` in inittab suggest startup shell state, but do not establish an operator-accessible console.

### UNKNOWN / BLOCKED

- No legitimate router transfer-and-execution path or safe persistent writable runtime location is established. USB storage host/mass-storage support is unproven; inspected kernel tree lacks evident USB host/mass-storage and FAT/VFAT modules, while filesystem module load lines are commented. SSH/Telnet/FTP daemons are not launched by inspected startup files.
- Conditional JFFS2 mounts at `/config` and `/etc/tri_image_up` are not established as general-purpose writable storage and are not recommended for runtime data.
- Admin upload endpoints remain firmware/configuration/certificate-specific. Do not use them to distribute the runtime, and do not exploit web behavior.
- No OEM binary was executed; no router contacted; no artifact, firmware, flash, startup script, or configuration changed. The runtime package remains research-only and contains no OpenLinux service payload.
- Next operator action: establish through vendor documentation or authorized service channel whether this exact HG630 V2 has an approved serial/service-console shell and connection procedure.

## OEM updater static-analysis milestone — 2026-11-10

### VERIFIED

- Added `analysis/openlinux/v1.1/updater-static-analysis.md` and companion JSON with SHA-256 inventory of `upg`, direct updater libraries/runtime dependencies, firmware, relevant RootFS configuration, and certificate/key files (private-key contents are not included).
- Confirmed `upg` is ELF32 ARM little-endian EABI5 and directly imports security and flash APIs. Static call sites include `ATP_SEC_KM_GetKey`, `ATP_SEC_CreateData`, `ATP_SEC_CreateSignatureContext`, `ATP_SEC_VerifyData`, `ATP_FLASH_Upgrade`, `ATP_FLASH_UpgradeBootloader`, `ATP_FLASH_UpgradeCfg`, MTD erase/write helpers, and `BSP_FLASH_UnProtect`.
- `libbhalapi.so` exports MTD selection and erase/read/write and generic/configuration/bootloader/area update helpers. `ATP_MTD_Getfd` dispatches logical indices 0–15 to static `/dev/mtd0`–`/dev/mtd15` paths.
- `libmsgapi.so` contains `ATP_SEC_VerifyData` and related wrappers, with RSA, SHA-256, and MD5 primitive references. The verifier calls digest processing and then an unresolved indirect callback.
- The extracted RootFS has `/etc/root.pem`, `/etc/servercert.pem`, and `/etc/serverkey.pem`; certificate inspection identifies a root/HTTPS server certificate pair. No call-site evidence links this certificate chain to firmware-update trust.
- Startup files show `inittab` invoking `/etc/init.d/rcS` and respawning `/bin/sh`; `rcS` is minimal, while `/etc/profile` performs vendor mounts, `startbsp`, `hi_xpon`, `hsanportinit`, module initialization, calibration link setup, and `mic` launch.
- Original firmware hash remains `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`; experimental image hash is `222cc9cd1aa0406826dd81d5237e1634690564014fcafa4e072451193dce4e3e` and remains `EXPERIMENTAL_NON_FLASHABLE`.
- No OEM binary was executed; no MTD device was opened; no firmware or flash was modified.

### INFERRED

- RSA-family verification and SHA-256 are plausible candidates based on imports, but the exact updater algorithm and signature contract are not resolved.
- The respawned shell suggests a manual operator-controlled launch may be possible after boot. Console access, privileges, service interactions, and safe coexistence are not verified.

### UNKNOWN / BLOCKED

- No supported RootFS-only update path is proven. The observed component ID and area-write API do not establish OEM acceptance of a RootFS-only package.
- Full-package requirement, section-ID to MTD mapping, offset address-space semantics, main/slave bank selection, mandatory/optional kernel or bootloader updates, erase geometry, rollback, and recovery remain UNKNOWN.
- No authorized OEM firmware-signing private key or documented signing path is available. Signature size/encoding/padding, digest contract, signed byte range, public-key origin, and outer checksum remain UNKNOWN; legitimate authentication of a custom image is BLOCKED.
- Keep the existing `EXPERIMENTAL_NON_FLASHABLE` classification. The next evidence needed is vendor-authorized documentation/service access defining RootFS-only eligibility and signing; until then continue only non-flashing userspace compatibility research with the original kernel and a verified recovery path.

## OEM RootFS reproduction milestone — 2026-11-10

### VERIFIED

- Original firmware and carved RootFS were hash-verified before use; originals were preserved.
- Built and tested SquashFS-tools 4.2, 4.3, 4.4, and 4.6.1 in isolated temporary directories with GCC 14.2.0 and locally built XZ Utils 5.2.5. Historical GCC compatibility patches and exact build guidance are recorded in `tools/experiments/build_historical_squashfs.sh`.
- All six generated images extract with exact path/type/content/mode/ownership/timestamp/device metadata equality against the extracted OEM RootFS, but none is byte-identical to OEM.
- Best size candidate is 4.2 native at 5,930,941 internal bytes, 24 bytes above OEM 5,930,917. 4.3/4.4/4.6.1 native are 5,929,517; normalized 4.4/4.6.1 are 5,929,345.
- Fresh per-file and complete overlay experiments show complete overlay 5,933,497 internal bytes, 2,489 bytes above the 5,931,008-byte reserved span. `openlinuxctl` is the largest individual measured contributor.
- Preserved-kernel inspection proves generic XZ decoder and SquashFS XZ glue strings. ARM BCJ registration and exact dictionary support remain unproven.
- Added `analysis/server-run/oem-reproduction-report.md`, `analysis/server-run/oem-reproduction-results.json`, `analysis/server-run/kernel-xz-compatibility.md`, historical build/matrix/kernel/overlay scripts, and automated tests.

### INFERRED

- SquashFS-tools 4.2 is the closest tested historical size candidate, but the +24-byte difference and differing image hash rule out OEM equivalence.
- The remaining difference is likely a combination of OEM compressor implementation/settings, traversal/order, and metadata packing; timestamps alone do not explain it.

### UNKNOWN / BLOCKED

- OEM tool provenance and exact XZ encoder recipe remain unknown.
- The Huawei kernel's `tbcj` strings do not prove ARM BCJ registration or safe support. Do not enable BCJ.
- No host-side result proves kernel mount, boot, updater acceptance, flashability, or hardware behavior. Keep `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`.

## Complete overlay fit milestone — 2026-11-10

### VERIFIED

- A complete OpenLinux overlay built with SquashFS-tools 4.2 and ordinary XZ fits using deterministic `-sort` ordering. The winning candidate is 5,914,229 internal bytes, leaving 16,779 bytes in the 5,931,008-byte span; SHA-256 is `1f0760422f5f94b5da8ad7670725e1c2fc6fe0134d6649b96e5f2a2dbca2515e`.
- The candidate retains 1,264 inodes, 14 fragments, no xattrs, duplicate checking, ordinary XZ, and all four overlay files. A repeat build produced the same hash after normalizing the 4.2 superblock creation timestamp to the OEM value.
- OEM-path comparison found no missing, extra, or changed OEM entries/metadata. Extracted candidate behavior matched the original overlay behavior tests.
- Tested XZ dictionaries and metadata/fragment settings; none improved size or preserved the original profile. 4.2 `-sort` variants were the successful optimization.
- Fixed overlay builds to restore timestamps on existing OEM directories after adding children; strict validation now records and compares integer mtimes.
- Verified required BusyBox applets and shell behavior under `qemu-arm`; no OEM file/library/kernel/driver was changed. Comment/blank-line stripping was behavior-equivalent and saved 533 source bytes, but original readable sources were retained.
- Added `analysis/server-run/overlay-fit-report.md`, `analysis/server-run/overlay-fit-results.json`, optimization/behavior scripts, and regression tests.

### INFERRED

- The size gain comes from SquashFS file-order/compressor packing under `-sort`, not from a different XZ filter or removed functionality. Sorting is format-compatible because it changes inode/order packing only.
- Existing OEM directories are not a safe alternate host for the overlay; using them does not remove the payload and risks vendor semantics. RAM/network loading remains a fallback architecture requiring post-boot transport and is not a reliable early-boot path.

### UNKNOWN / BLOCKED

- Target Huawei kernel mount behavior, updater acceptance, flash mapping, boot, and hardware behavior remain unverified. The fitting candidate is still `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`.
- ARM BCJ and exact target XZ dictionary support remain UNKNOWN; the fitting candidate uses neither BCJ nor alternate metadata semantics.

## RootFS size and compatibility investigation — 2026-11-10

### VERIFIED

- Added `analysis/server-run/rootfs-size-investigation.md` covering ABI, overlay, size, compression, Linux 2.6.30 compatibility evidence and blockers.
- Current branch was clean at commit `4da095caa79038cf3018207efbd919d654d9be8b` before the report/context edits.
- The ABI report covers 227 ELF32 little-endian ARM binaries. EABI5 is recorded, but float calling convention remains ambiguous. OEM libc symlinks resolve to uClibc 0.9.32.1-git and the OEM dynamic interpreter.
- Per-file ordinary-XZ tests show `openlinuxctl` is the largest individual size contributor; the full overlay is over the 5,931,008-byte reserved span. No overlay code or OEM component was changed.
- A no-controller test image has no missing or changed OEM files. The comparison mismatch is caused by expected new parent directories being listed as extras.
- Dictionary experiments 100/75/50/25 percent all extracted on the host and all exceeded the span; smaller dictionaries worsened size. Ordinary XZ remains the evidence-backed compatibility choice. ARM BCJ support in the target kernel remains UNKNOWN.
- Existing output artifacts were preserved; new diagnostic outputs are in `/home/ayad/build-output/custom-build/run-investigation-*`.
- `python3 -m unittest discover -s tests -v`: 69/69 passed. No tests were added because no code changed.

### INFERRED

- Timestamp normalization is one contributor to non-reproducibility: preserving source timestamps yielded 5,929,517 internal bytes versus normalized baseline 5,929,345, but the OEM is 5,930,917. Exact OEM compressor/version/order recipe remains unknown.

### UNKNOWN / BLOCKED

- No integrated ordinary-XZ candidate presently fits. Keep `EXPERIMENTAL_NON_FLASHABLE`; updater acceptance, target boot/mount, flash mapping, and recovery requirements are unproven.

## Historical recovery status

- Recovered after the previous Codex session exited.
- No `AGENTS.md` exists under `/root/projects` or this repository.
- No earlier `PROJECT_CONTEXT.md` existed; this file is the recovery record.
- The recovery snapshot below records an earlier state; current milestone state is recorded in the milestone sections at the end of this document.
- Initial Git status on recovery was clean relative to the branch except for the existing untracked work:
  - `tools/build_rootfs.py`
  - `build/components/boot-marker/`

## Background build recovery

At the first recovery check, these two background processes were active:

```text
PID 3946420: python3 tools/build_rootfs.py ... --output /home/ayad/build-output/custom-build/run-001 ...
PID 3948296: python3 -u tools/build_rootfs.py ... --output /home/ayad/build-output/custom-build/run-002 ...
```

Neither process was stopped, signaled, restarted, or overwritten. Both exited naturally before the follow-up artifact check. No `build_rootfs.py` process is now running.

Both runs copied the source RootFS into `stage-rootfs` and stopped before producing final output:

- `run-001/stage-rootfs` exists; `run-001/rootfs.squashfs` is absent; `run-001/build-report.json` is absent.
- `run-002/stage-rootfs` exists; `run-002/rootfs.squashfs` is absent; `run-002/build-report.json` is absent.
- The boot-marker overlay and its manifest are present at `/home/ayad/build-output/custom-build/overlays/boot-marker/`.
- Source RootFS is `/home/ayad/build-output/rootfs`; source SquashFS is `/home/ayad/build-output/carved/rootfs.squashfs`, SHA-256 `68dcfa5c1b53bd09fcd00ea52bdcd3fb1da25d53446915cd6fd2f3aba22bb534`.

The script reaches `mksquashfs` only after copying the stage. The exact blocker was then reproduced safely in a new `run-003`: `shutil.copytree(..., copy_function=shutil.copy2)` opened the source character device `/dev/console` and blocked in `read(2)`. `run-003` was interrupted, leaving its incomplete stage preserved. The original two runs also stopped during this stage-copy phase; no generated RootFS image was completed in either.

## Completed work recovered

- Firmware carving, RootFS extraction/inventory, and ABI evidence are recorded under `analysis/server-run/` and in `analysis/01-*` through `analysis/05-*`.
- The original kernel/uImage is to remain preserved; no flashing or device write is authorized.
- The pending build experiment is an overlay-only SquashFS generation with the harmless marker component. It is not a flashable firmware image.

## Continuation rules

- Never touch `run-001` or `run-002`; they are preserved as incomplete recovery evidence.
- Do not launch duplicate builders. Verify with `pgrep` immediately before starting a new uniquely named run.
- Use a single SquashFS processor for the continuation build to avoid concurrent/default parallelism exhausting resources.
- Validate the resulting image, marker, report, source hash, and Git status before proceeding.

## Next successful step

The build tool was updated to recreate regular files and special device/FIFO entries without opening them, and to make the `mksquashfs` processor count explicit (default one worker). Exactly one continuation run was then made in the new `run-004` directory.

## Successful continuation: run-004

- Output: `/home/ayad/build-output/custom-build/run-004/rootfs.squashfs`
- SHA-256: `0daceafcd1a289f61ffb5fce51f0081734c1f0d7c2859773cb7a6ef1327fd7b5`
- Size: `5,931,008` bytes
- Report: `/home/ayad/build-output/custom-build/run-004/build-report.json`
- Staged file/symlink count: `1,146`
- Compression: xz, 1 MiB blocks, one processor
- `unsquashfs -s` validation passed.
- Extracted-image validation passed: overlay marker is present; `/dev/console` and `/dev/null` are preserved as character devices.
- Repository tests: 11/11 passed.

This is an overlay-only RootFS build experiment. Do not package, flash, or claim a bootable/flashable firmware image from it. The original kernel is not included or modified.

## Builder hardening milestone — 2026-11-10

### VERIFIED

- Added `AGENTS.md` with durable safety, testing, artifact-preservation, and documentation instructions.
- Hardened `tools/build_rootfs.py` to preserve regular-file hardlinks, symlinks, mode/timestamps, UID/GID ownership, FIFOs, character devices, and block devices without opening special files.
- The builder now rejects unsupported socket entries, refuses an output directory inside the source RootFS, and validates both the SquashFS superblock and a complete extraction into a temporary directory.
- Added `tests/test_build_rootfs.py`; the complete test suite passes 15/15.
- Built `/home/ayad/build-output/custom-build/run-005/rootfs.squashfs` and independently repeated it as run-006.
- Run-005 and run-006 are byte-identical: SHA-256 `28296f73c210383cd2adf2dfdffdd0f760e1bb3dd28e88d5bd3cc3f2dec704c7`, size 5,931,008 bytes.
- Run-005 and run-006 passed `unsquashfs -s` plus full extraction validation; the marker and `/dev/console`/`/dev/null` device nodes are present.

### INFERRED

- The run-005/run-006 hash change from run-004 is explained by ownership preservation: the old builder produced one SquashFS UID/GID entry, while the corrected builder preserves seven source UID/GID entries. Repeatability across run-005/run-006 supports deterministic output.

### UNKNOWN / BLOCKED

- These are still overlay-only RootFS artifacts. They do not include or modify the original Linux 2.6.30 kernel and are not complete or flashable firmware images.
- OEM update-container validation, exact partition layout, DSL stack compatibility, and hardware boot/DSL/Wi-Fi validation remain unresolved.

### Commands and artifacts

```text
python3 -m unittest discover -s tests -v                 # 15/15 passed
python3 tools/build_rootfs.py ... --output .../run-005 --processors 1
python3 tools/build_rootfs.py ... --output .../run-006 --processors 1
sha256sum .../run-005/rootfs.squashfs .../run-006/rootfs.squashfs
```

## Artifact comparison milestone — 2026-11-10

### VERIFIED

- Added `tools/validate_rootfs.py`, which emits a JSON report containing image hash/size, SquashFS summary, extraction evidence, entry counts, and missing/extra/changed path lists.
- Comparison covers entry type, mode, UID/GID, regular-file SHA-256 and size, symlink targets, and device major/minor numbers. Intentional overlay differences can be named explicitly.
- The validator detected that the first hardened implementation cleared setuid bits during post-copy ownership restoration. Ownership is now applied before final mode restoration.
- The complete test suite remains 15/15 passed.
- Fresh run-007 output: `/home/ayad/build-output/custom-build/run-007/rootfs.squashfs`, SHA-256 `05240eabcc5f559fe92ef5a89f08ae33bcd978dc4977ae85143ab1a50de8f97b`, size 5,931,008 bytes.
- Run-007 preserves `/bin/busybox` mode `04755`; `unsquashfs` structure and extraction validation pass.

### INFERRED

- The run-007 hash supersedes run-005/run-006 for the corrected builder because it preserves setuid/setgid bits that ownership restoration had cleared in those earlier experimental artifacts. Run-005 and run-006 remain preserved evidence and are not overwritten.

### UNKNOWN / BLOCKED

- Comparing run-007 to the unmodified source reports only `/etc` as changed when the boot-marker overlay is applied; this is an intentional overlay directory metadata difference and can be accepted with `--allow-difference etc`.
- RootFS comparison still does not establish kernel boot, OEM container integrity, DSL compatibility, or hardware behavior.

### Commands

```text
python3 tools/validate_rootfs.py .../run-007/rootfs.squashfs \
  --source /home/ayad/build-output/rootfs \
  --allow-extra etc/openlinux-build-marker \
  --allow-difference etc
```

Next concrete task: inspect the original firmware/container parser coverage and add explicit structural tests for the observed SquashFS-to-uImage layout without inventing an OEM checksum or flash format.

## OEM metadata parser milestone — 2026-11-10

### VERIFIED

- Added `tools/inspect_firmware.py` for read-only byte parsing, header capture, metadata field locations/raw bytes, region boundary and overlap checks, SquashFS recognition, and uImage header/data CRC checks.
- Added `tools/validate_firmware.py` to verify the expected original SHA-256, metadata/bounds, SquashFS superblock extent, and uImage bounds and CRC32 values.
- Added seven synthetic OEM parser tests. Full repository suite: 22 passed.
- Original firmware SHA-256 remains `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222` (7,563,600 bytes).
- Metadata begins around offset `0x314`. `board_id=1212` is decimal at value offset `0x33e` (830). Offset and size values use explicit `0x` hexadecimal syntax. The report preserves every field value and surrounding raw bytes.
- SquashFS starts at `0x305cf`, reports 5,930,917 bytes, and ends at `0x5d85b4`, within the package. Its version is 4.0 and compression ID is 4.
- uImage starts at `0x5d85cf`; payload is 1,434,088 bytes and ends at `0x7368b7`. Header and payload CRC32 checks pass.
- Some metadata ranges extend beyond the update package file boundary. The validator flags the bounds check while all embedded SquashFS/uImage checks pass. This is a warning about unresolved metadata semantics, not evidence that the metadata should be edited.
- Reports saved at `analysis/oem-firmware/metadata-report.json`, `analysis/oem-firmware/metadata-report.md`, and `analysis/oem-firmware/validation-report.json`.

### UNKNOWN

- The metadata region table may describe physical flash regions, a larger device address space, or another layout; its semantics are unverified. The parser labels these as metadata ranges, not proven partitions.
- Outer container checksums/authentication, encryption, bootloader acceptance behavior, and a reconstructable OEM packaging recipe remain unknown.

### Commands

```text
python3 tools/inspect_firmware.py /home/ayad/firmware-input/HG630V2-12V100R001.bin --json analysis/oem-firmware/metadata-report.json
python3 tools/validate_firmware.py /home/ayad/firmware-input/HG630V2-12V100R001.bin
/tmp/hg630-test-venv/bin/python -m pytest -q tests
```

Next task: investigate metadata range address-space semantics through exact offset arithmetic, independent image carving, and comparison with any available trusted board/flash documentation. Do not infer a physical partition map from names alone.

## Metadata address-space arithmetic — initial investigation

### VERIFIED

- The nonzero table entries chain contiguously in an apparent address range from `0x000000` through `0xfd0000` (15.8125 MiB maximum end).
- `[20011]` main `0x0+0x20000` ends where `[20003]` main begins; `[20003]` main/slave then meet at `0x40000`; `[20002]` main ends at `0x1a0000`, where `[20001]` main begins; `[20001]` main ends at `0x7c0000`, where `[20002]` slave begins; the latter ends at `0x920000`, where `[20001]` slave begins.
- `[20001]` slave ends at `0xf40000`, where zero-size IDs `[20100]` and `[20101]` are recorded, followed by entries ending at `0xfa0000` and `0xfd0000`.
- The package itself is only `0x736950` bytes. Thus its table values cannot all be direct byte offsets into this update file. The observed SquashFS/uImage data occupies package offsets `0x305cf..0x5d8574` and `0x5d85cf..0x7367f7`; metadata extents do not directly correspond to those embedded package offsets.

### INFERRED

- The regular, contiguous `0x0..0xfd0000` arithmetic is consistent with a larger address space than the update file, such as an intended device layout, but does not establish physical flash addresses or actual partition boundaries. Section IDs, update selection rules, and how component payloads map onto these ranges remain unknown.

### Next evidence needed

- Trusted documentation or source for this exact firmware parser/upgrade implementation, or a verified full flash map from the exact HG630 V2 board. Until then these remain metadata ranges and no reconstruction offset should be derived from them.

## Flash Layout Reconstruction

### VERIFIED

- Implemented `tools/analyze_flash_layout.py`. It emits candidate start/end/size, evidence source, confidence/status, capacity comparisons, and overlap findings while explicitly leaving physical-flash verification false.
- Saved machine-readable findings to `analysis/flash-layout/evidence.json` and the human-readable analysis to `analysis/flash-layout/report.md`.
- Static RootFS evidence: `/etc/profile` links `/dev/caldata` to `/dev/mtd9`. Static vendor binary/library symbols include MTD and update operations such as `ATP_MTD_Getfd`, `ATP_MTD_ReadBuffromOffset`, `ATP_FLASH_WriteArea`, `UPG_FlashPartWrite`, and `FOMGetAllFlashSize`.
- No concrete `/proc/mtd` partition listing or `mtdparts=` declaration was found in the searched extracted RootFS strings. No vendor firmware utilities were executed.
- Added five synthetic tests for contiguous regions, gaps, partial overlaps, capacity candidates, and unknown semantics. Complete suite passes 27 tests.

### INFERRED

- Metadata extents span `0x000000..0xfd0000`; candidate 16 MiB accommodates that end, while 8 MiB does not. Neither capacity is established for this device.
- `[20005]` (`0xf40000..0xfa0000`) overlaps `[20004]` and `[30002]` (`0xf70000..0xfd0000`) over `0xf70000..0xfa0000`. This could reflect aliases or update modes; the records alone cannot resolve it.

### UNKNOWN / BLOCKED

- Exact physical flash chip/model/capacity, erase geometry, bootloader type/version, MTD names and boundaries, and the meaning of region section IDs remain unverified. These proposals are not a verified partition map.
- Required next evidence: exact-board source/config with MTD declarations, or trusted live `/proc/mtd` and boot command line from the exact VER.B hardware, ideally corroborated by chip markings.
- Next implementation task after delivery: statically inspect the identified upgrade binary and libraries for metadata parsing, validation calls, component selection, and write targets.

## OEM `upg` static-analysis milestone — 2026-11-10

### VERIFIED

- Added `tools/analyze_upgrade_binary.py`, a read-only ELF32 ARM analyzer. It parses section/dynamic-symbol metadata, decodes ARM `B`/`BL` instructions, follows one level of literal-pool pointers into `.rodata`, and maps direct PLT calls to imported API names without executing the binary.
- Added four synthetic helper tests. The complete repository suite passes 31 tests with `python3 -m unittest discover -s tests -v`.
- The analyzed executable is `/home/ayad/build-output/rootfs/bin/upg`, SHA-256 `73ea3d4711d481599e58e5737ab80ce08e032ddd7ca48803063df4dedb6ba385`, 27,648 bytes, ELF32 little-endian ARM EABI5, entry `0x9780`.
- The analyzer decoded 448 direct ARM call instructions, identified 31 function-start candidates, and recorded 88 imported APIs with direct call sites. Local generated results are preserved outside Git at `analysis/generated/upg-static/upg-analysis.json` and `analysis/generated/upg-static/report.md`.
- Direct call-site evidence confirms use of security APIs including `ATP_SEC_CreateData`, `ATP_SEC_CreateSignatureContext`, `ATP_SEC_KM_GetKey`, `ATP_SEC_VerifyData`, and `ATP_SEC_DeleteContext`.
- Direct call-site evidence confirms use of flash/MTD APIs including `ATP_MTD_Getfd`, `ATP_MTD_Erase`, `ATP_MTD_WriteBufToOffset_Upg`, `ATP_FLASH_Write`, `ATP_FLASH_WriteArea`, `ATP_FLASH_Upgrade`, `ATP_FLASH_UpgradeCfg`, `ATP_FLASH_UpgradeBootloader`, and `BSP_FLASH_UnProtect`.
- Directly referenced strings include `main_offset`, `main_size`, `slave_offset`, `slave_size`, `Erase Flash Error`, `Write Flash Error`, and messages distinguishing kernel/image single-system handling.

### INFERRED

- The executable contains distinct internal helper paths around the security calls (`0xc304..0xc370`) and flash/MTD calls (`0xb06c..0xb4d0`), but imported-library semantics and exact argument meanings remain external to this binary.
- The presence of separate `ATP_FLASH_UpgradeBootloader`, `ATP_FLASH_UpgradeCfg`, and `ATP_FLASH_Upgrade` imports suggests separate upgrade modes exist; the analyzer does not yet prove which metadata section selects each mode.

### UNKNOWN / BLOCKED

- CRC/checksum algorithm: UNKNOWN. No CRC-named import or self-contained CRC implementation was identified by this first-pass scan.
- Signature algorithm and key format: UNKNOWN. Security calls are proven, but implementations are in linked libraries that have not yet been recovered and analyzed. High-entropy `.rodata` is recorded only as candidate data, not identified key material.
- Exact firmware-header parser control flow, board-ID/version comparisons, MTD number selection, erase/write ordering, rollback/recovery behavior, and cryptographic acceptance rules remain unresolved.
- No ARM executable was run, no host MTD was accessed, and no router was contacted.

### Next concrete task

Analyze the linked `libupgapi`, security, flash, and configuration libraries statically if preserved in the extracted RootFS; correlate their call contracts with the `upg` call sites and update the report with only directly supported argument/branch evidence. If the required library is absent, document that evidence gap and continue with static analysis of available bootloader/rootfs binaries.

## Linked-library follow-up — 2026-11-10

### VERIFIED

- The extracted RootFS does not contain a file named `libupgapi.so`; the required upgrade APIs are distributed across available libraries. `upg` needs `libcyassl.so.5`, `libmsgapi.so`, `libcfmapi.so`, `libbhalapi.so`, and other vendor libraries.
- `libmsgapi.so` exports `ATP_SEC_VerifyData`, `ATP_SEC_CreateSignatureContext`, `ATP_SEC_CreateData`, `ATP_SEC_SignData`, `ATP_SEC_DigestData`, and key-management APIs. Its dynamic symbol table imports CyaSSL RSA primitives (`CyaSSL_RSA_verify`, `CyaSSL_RSA_sign`, RSA key creation/size), SHA-256 primitives, MD5 primitives, and AES/DES3 primitives.
- `libmsgapi.so` contains direct calls from security wrappers to other security APIs and indirect context callbacks. This proves the security subsystem has digest/signature/encryption paths, but the first-pass call decoder cannot resolve every GOT/function-pointer dispatch.
- `libbhalapi.so` exports `ATP_MTD_Getfd`, `ATP_MTD_Erase`, `ATP_MTD_WriteBufToOffset_Upg`, `ATP_FLASH_Write`, `ATP_FLASH_WriteArea`, `ATP_FLASH_Upgrade`, `ATP_FLASH_UpgradeCfg`, `ATP_FLASH_UpgradeBootloader`, `UPG_FlashPartWrite`, and `FOMGetAllFlashSize`.
- `libbhalapi.so` contains literal device names `/dev/mtd0` through `/dev/mtd15`, `MEMERASE` failure handling, low-level MTD read/write errors, and flash protect/unprotect paths. This is direct static evidence that MTD selection supports at least that device-number range; it is not a verified board partition map.
- The analyzer now accepts ELF shared objects with `.bss`/`SHT_NOBITS` sections and resolves ARM PLT imports in ET_DYN libraries. The full test suite remains 31/31 passing.

### INFERRED

- RSA plus SHA-256 are the strongest current candidates for the firmware/security signature path because both primitive families are imported by `libmsgapi.so` alongside the exported signature wrappers. This remains an inference until the relevant wrapper's indirect context dispatch and data format are traced end-to-end.
- The flash library's explicit `/dev/mtd0`–`/dev/mtd15` table is consistent with the prior `upg`/RootFS evidence, but names and offsets are likely selected by higher-level area tables or runtime configuration; no exact partition assignment is established.

### UNKNOWN / BLOCKED

- The exact signature padding/mode, digest coverage, public-key source, firmware-header field offsets consumed by the wrappers, and acceptance return-code policy remain UNKNOWN.
- The exact mapping from update section IDs (`20001`, `20002`, etc.) to MTD device numbers or flash areas remains UNKNOWN.
- Generated library reports are preserved locally under ignored `analysis/generated/upg-static/`; proprietary binaries remain outside Git.

### Phase 2 report update

- Updated `analysis/flash-layout/report.md` with the verified `libbhalapi.so` export list and `/dev/mtd0`–`/dev/mtd15`/`MEMERASE` string evidence. The flash map remains `layout_verified=false`; no MTD number has been assigned to an OEM metadata section.

## OEM signature and flash-write analysis milestone — 2026-11-10

### VERIFIED

- Added `tools/analyze_upgrade_security.py` and `tools/analyze_mtd_write_path.py`, plus two synthetic tests. Full repository suite passes **33/33**.
- Security report: [analysis/upgrade-re/security-report.md](analysis/upgrade-re/security-report.md). It traces `ATP_SEC_VerifyData` at `libmsgapi.so+0x14648`, `ATP_SEC_VerifyDataEx` at `+0x14d2c`, and `ATP_SEC_CreateSignatureContext` at `+0x14be8`, including direct calls and unresolved indirect context dispatches.
- `ATP_SEC_VerifyData` checks input/context lengths, calls `ATP_SEC_DigestDataEx`, then invokes a function pointer from the security context. `ATP_SEC_CreateSignatureContext` allocates 36 bytes and stores mode-dependent fields/callback pointers.
- `libmsgapi.so` imports CyaSSL RSA, SHA-256, and MD5 primitives. Static paths `/etc/root.pem`, `/etc/servercert.pem`, and `/etc/serverkey.pem` are present, but no path is proven to be the firmware-update public key.
- Flash report: [analysis/upgrade-re/flash-write-report.md](analysis/upgrade-re/flash-write-report.md). `ATP_MTD_Getfd` at `libbhalapi.so+0x3ce8` compares the logical index with 15 and dispatches indices 0–15 through an ARM jump table to `/dev/mtdN` paths.
- Function-level call references are recorded for MTD get-fd, erase, read, write, area-write, generic upgrade, configuration upgrade, bootloader upgrade, and partition-write functions.
- Existing validator evidence remains VERIFIED for embedded uImage header/data CRC32. No OEM outer-container checksum has been identified.

### INFERRED

- SHA-256 and RSA are the strongest candidates for the signature path because the linked security library imports both primitive families alongside the verification wrappers.
- The MTD path uses logical device indices and static device-name construction; higher-level upgrade functions likely choose between full, area, configuration, bootloader, and partition writes based on runtime arguments/state.

### UNKNOWN / BLOCKED

- RSA modulus/key size, signature encoding/length, padding scheme, public-key source, signed byte range, header exclusions, and exact failure/recovery behavior remain unresolved because the decisive context dispatches and runtime key loading are indirect.
- No exact update-section-to-MTD mapping is proven. Calibration exclusion, bootloader protection policy, erase geometry, and full-vs-partial package selection remain unresolved.
- A Python signature-verification tool is BLOCKED: the public key, signature bytes/format, digest coverage, and padding are not sufficiently established. No private key was generated or extracted, and no cryptographic bypass was attempted.
- Generated JSON reports are preserved outside Git under `analysis/generated/upgrade-re/`; the requested human-readable Markdown reports are committed under `analysis/upgrade-re/`.

## Integrated custom firmware build milestone — 2026-11-10

### VERIFIED

- Added `tools/build_firmware.py` and three synthetic assembly tests. Full repository suite passes **36/36**.
- The builder requires the known original firmware SHA-256 by default, validates the custom RootFS through SquashFS structure plus complete extraction, and refuses to overwrite an existing output.
- It preserves the original metadata prefix, unknown header bytes, original uImage, and suffix. It rejects a replacement RootFS whose size would move the original uImage or require invented gap/offset semantics.
- Run-007 custom RootFS is exactly `5,931,008` bytes, matching the original SquashFS-to-uImage reserved span. A same-layout experimental image was assembled at `/home/ayad/build-output/custom-build/firmware-run-001/HG630V2-experimental.bin`.
- Experimental image SHA-256: `349d448549c468145df58176c4e787d5a192b5dbde6135496fa8e4027f84fcc4`, size 7,563,600 bytes.
- The preserved uImage remains byte-identical with SHA-256 `13a3432e8d2bbce07c5d0a49e157d77c3c183cad445dfb16be3c3bcaaa75ebc7`; its header and payload CRC32 checks pass. Kernel name is `Linux-2.6.30`, LZMA compression, load/entry `0x81208000`.
- Added [analysis/build-feasibility/report.md](analysis/build-feasibility/report.md) and [analysis/build-feasibility/manifest.json](analysis/build-feasibility/manifest.json).

### INFERRED

- Same-offset assembly is the safest currently justified integration strategy because it leaves all unresolved metadata coordinates and the original kernel position untouched.
- The resulting RootFS preserves the original hardware-specific files because the existing overlay build starts from the complete extracted RootFS and run-007 had already passed source comparison with only the intentional overlay difference.

### UNKNOWN / BLOCKED

- OEM update acceptance remains UNKNOWN: signature, outer checksum/authentication, and metadata-to-MTD semantics are unresolved.
- Kernel boot arguments, root device, mount parameters, QEMU boot, and actual HG630 V2 hardware boot remain UNKNOWN/BLOCKED.
- The generated image is explicitly `EXPERIMENTAL_NON_FLASHABLE`; no flashing, MTD access, or cryptographic bypass was attempted.

## Kernel/boot validation milestone — 2026-11-10

### VERIFIED

- Preserved kernel is a legacy U-Boot ARM uImage named `Linux-2.6.30`, LZMA-compressed, with load and entry address `0x81208000`, payload size 1,434,088 bytes, and valid header/data CRC32.
- The extracted RootFS uses BusyBox for `/init` and `/sbin/init`; `/etc/inittab` invokes `/etc/init.d/rcS`, and the current `rcS` only sets `PATH` and prints `RCS DONE`.
- The extracted RootFS contains three kernel modules under `lib/kernel`; the broader inventory records the vendor DSL/network module set. No kernel module loading or service initialization was executed.
- The decompressed kernel identifies the vendor platform with `SD56XX`, `sd5610x_iomux_*`, `sd5610x_gpio_*`, `sd56xx System Timer`, and `sd56xx_reboot_reg` strings. Vendor modules reference `hi_kernel_sd56xx_*` and were built with `2.6.30 ... ARMv7` vermagic. The HiSilicon SD56xx/SD5610x family is VERIFIED; the exact silicon revision remains UNKNOWN.
- QEMU 10.0.13 `qemu-system-arm` and `qemu-arm` were installed from Debian trixie. QEMU exposes no SD56xx/SD5610x machine. The custom artifact hash was rechecked as `349d448549c468145df58176c4e787d5a192b5dbde6135496fa8e4027f84fcc4` without rebuilding.
- ARM user-mode QEMU executed the preserved RootFS BusyBox and the staged `/etc/init.d/rcS`, which printed `RCS DONE` and returned 0. This is partial user-space validation only.
- Added [analysis/boot-validation/report.md](analysis/boot-validation/report.md) and [analysis/boot-validation/boot-log.txt](analysis/boot-validation/boot-log.txt).

### UNKNOWN / BLOCKED

- No compatible QEMU machine model, kernel boot arguments, root device, or mount parameters were established. Bounded `versatilepb` and `virt` attempts produced no kernel console output; passing the original LZMA uImage directly was rejected by QEMU's image loader as compression type 3.
- Kernel boot, RootFS mount during kernel boot, service initialization with vendor devices, and hardware boot remain UNKNOWN/BLOCKED. User-mode BusyBox execution must not be treated as kernel or hardware boot evidence.

## OpenLinux userspace and V0.2 build milestone — 2026-11-10

### VERIFIED

- Added the first additive OpenLinux userspace component under [build/experimental/openlinux-overlay/rootfs](build/experimental/openlinux-overlay/rootfs): BusyBox-compatible `openlinuxctl`, service configuration, a dry-run network hook, and an additive init hook. The original vendor kernel, libraries, modules, DSL stack, and original `rcS` remain untouched.
- `openlinuxctl` validates `SERVICE_NETWORK`, `SERVICE_DNS`, `SERVICE_SSH`, `SERVICE_FIREWALL`, and `SERVICE_WEB` values, reports status, and only invokes explicitly enabled hooks. All services default to disabled; the network hook refuses hardware changes unless an explicit test variable is set, and still exits with an unverified-hardware warning.
- Added host tests in `tests/test_openlinux_userspace.py`; the full suite passes **39/39**.
- The component executed under ARM user-mode QEMU from the newly built RootFS: status output reported all five services disabled and boot logging completed successfully. This is userspace-only validation.
- Built RootFS V0.2 at `/home/ayad/build-output/custom-build/run-008/rootfs.squashfs`, size `5931008`, SHA256 `c2d9dfe353e01da7be59ab32efe0b8465cecb6a5f13c480846a390d9b6b677ea`.
- Assembled a new experimental firmware at `/home/ayad/build-output/custom-build/firmware-run-002/HG630V2-v0.2-experimental.bin`, SHA256 `c0fbddcdbf524878a07826544a44dfaeaf3dbfa2c3c57606ac03dd3e9faf8d4a`. The original kernel and same-offset container structure were preserved; the builder manifest marks it `EXPERIMENTAL_NON_FLASHABLE`.
- Added [analysis/platform/report.md](analysis/platform/report.md), [analysis/openlinux/README.md](analysis/openlinux/README.md), and [build/experimental/README.md](build/experimental/README.md).

### INFERRED

- The additive supervisor is a safe integration seam for future DHCP/DNS/SSH/firewall/web components because it does not assume vendor device names or replace the vendor startup path.

### UNKNOWN / BLOCKED

- The new init hook is not claimed to run during actual router boot: the original `rcS` does not currently invoke it, and wiring service startup into vendor boot ordering requires further static/hardware evidence.
- DHCP, DNS, SSH, firewall, web administration, service dependency ordering, and kernel-device integration remain unimplemented or UNKNOWN. No service is enabled by default.
- Exact SD5610x machine ID, ATAGS/device-tree protocol, RAM layout, UART, interrupt controller, timer, clock, and RootFS mount parameters remain UNKNOWN.

## OpenLinux V0.3 core services milestone — 2026-11-10

### VERIFIED

- Extended `openlinuxctl` with network status/validation/dry-run application, DHCP/DNS generation, static lease/local host inputs, firewall backend/rule validation, SSH status/validation, `/proc` monitoring, bounded OpenLinux logging, and service-supervisor boot logging.
- RootFS inventory verified the preserved `/bin/ip`, `/sbin/udhcpc`, vendor `/bin/iptables`, `/bin/sshd`, and vendor `dns`/`dhcps` binaries. No OEM `dnsmasq` or `nft` binary was found. OEM files and daemons remain untouched.
- Added component tests covering invalid configuration, interface validation, DHCP generation, static leases/local hosts, firewall rules, SSH validation, monitoring, dry-run guarantees, and supervisor logging.
- V0.3 RootFS built and extracted successfully at `/home/ayad/build-output/custom-build/run-012/rootfs.squashfs`, size `5931008`, SHA256 `80304d7848b7732b46e290f8f8845129340da31a7cfd7831e3ee25c89dd7e79e`.
- V0.3 firmware assembled separately at `/home/ayad/build-output/custom-build/firmware-run-003/HG630V2-v0.3-experimental.bin`, SHA256 `cfe1afd5f628db281fbefe36da0936995e8deb05c8de4d76fbb164244417fb74`; manifest/hash verification passed and the artifact is `EXPERIMENTAL_NON_FLASHABLE`.
- ARM user-mode QEMU executed the V0.3 status, network validation, DHCP generation, firewall backend detection, SSH status, and dry-run commands. This validates userspace execution only.
- Added [analysis/openlinux/v0.3-report.md](analysis/openlinux/v0.3-report.md). The fixed-span build required explicit XZ ARM BCJ compression and deterministic zero padding; the exact kernel's BCJ support remains unverified.

### INFERRED

- The preserved vendor `iptables` binary is the only verified firewall backend suitable for a future integration path; the OpenLinux abstraction avoids assuming nftables.
- OpenLinux-owned generated configuration can coexist with OEM configuration because no OEM file or daemon is replaced.

### UNKNOWN / BLOCKED

- Actual DHCP/DNS daemon operation, firewall rule application, SSH exposure, vendor interface names, init-time service ordering, kernel SquashFS BCJ support, kernel boot, OEM update acceptance, and hardware compatibility remain UNKNOWN/BLOCKED.
- The prior run-009/run-010 default-compressor builds exceeded the fixed span and were safely rejected by the assembly tool; those external build directories remain preserved as evidence. No previous artifact was overwritten.

## OpenLinux V0.4 integration and boot-readiness milestone — 2026-11-10

### VERIFIED

- Current HEAD before this milestone was `7c97e49`; branch `codex/hybrid-server-work` was clean and tracked `origin`.
- OEM init inventory follows actual calls: BusyBox `/etc/inittab` runs `/etc/init.d/rcS`, respawns `-/bin/sh`, and the shell profile performs mounts, `makedevs`, `startbsp`, `hi_xpon`, background `hsanportinit`, background `/etc/insmod_all.sh`, `/dev/caldata -> /dev/mtd9`, and `mic`. `insmod_eth.sh` is present but not called by the observed path.
- Added [analysis/openlinux/v0.4/init-inventory.json](analysis/openlinux/v0.4/init-inventory.json), [init-order.md](analysis/openlinux/v0.4/init-order.md), and [vendor-dependencies.md](analysis/openlinux/v0.4/vendor-dependencies.md).
- Hardened the additive OpenLinux hook with absent/invalid configuration safety, bounded timeout, failure logging, and failure isolation. The hook is not injected into OEM `rcS` or `/etc/profile`; automatic boot integration remains UNKNOWN/BLOCKED.
- Original and V0.3/V0.4 SquashFS are version 4.0, little-endian, XZ, 1 MiB blocks. The original kernel contains SquashFS XZ and `xz_dec_*` evidence. V0.3/V0.4 ARM BCJ filter support remains UNKNOWN because no kernel config or target-kernel runtime is available.
- Corrected the V0.3 userspace runtime dependency issue: the OEM BusyBox does not list `sed`, `wc`, `mv`, `tr`, or `timeout`; V0.4 scripts use only verified shell/BusyBox facilities.
- Added [tools/simulate_openlinux_boot.py](tools/simulate_openlinux_boot.py) and boot-isolation tests covering OEM-only, disabled, missing/invalid config, supervisor failure, timeout, missing binary, and logging failure. The staged V0.4 simulation preserved `RCS DONE`, returned OEM status 0, and isolated the OpenLinux hook.
- Added [analysis/openlinux/v0.4/compatibility-audit.json](analysis/openlinux/v0.4/compatibility-audit.json), [compatibility-audit.md](analysis/openlinux/v0.4/compatibility-audit.md), [squashfs-comparison.json](analysis/openlinux/v0.4/squashfs-comparison.json), and [squashfs-compatibility.md](analysis/openlinux/v0.4/squashfs-compatibility.md).
- Built V0.4 RootFS at `/home/ayad/build-output/custom-build/run-013/rootfs.squashfs`, size `5931008`, SHA256 `db620f72a514c62cccc9cd3ae6cb7d27151abec59cb4cb58b4c1aee393777785`.
- Assembled V0.4 experimental firmware at `/home/ayad/build-output/custom-build/firmware-run-004/HG630V2-v0.4-experimental.bin`, SHA256 `9ec2d00ffa546c7b0d3be228c0867fba7ffac2a5e354c6b22d249d1035ab5cb1`; complete manifest/hash verification passed and the label remains `EXPERIMENTAL_NON_FLASHABLE`.
- Added [analysis/openlinux/v0.4/report.md](analysis/openlinux/v0.4/report.md) and [v0.4/manifest.json](analysis/openlinux/v0.4/manifest.json).

### INFERRED

- `/bin/mic` is the vendor service manager because the profile calls it after hardware setup and its static strings reference fork/exec/restart plus SSH, DHCP, DNS, firewall, and management services. Exact service ordering remains unproven.
- The safest current integration point is no automatic integration: changing `rcS` or `/etc/profile` could replace or repeat OEM initialization. The isolated hook is ready for future evidence-backed invocation.

### UNKNOWN / BLOCKED

- Exact vendor service launch order, shutdown order, watchdog behavior, machine boot integration, and kernel RootFS mounting remain UNKNOWN.
- ARM BCJ XZ filter acceptance by the original 2.6.30 SquashFS decoder remains UNKNOWN/BLOCKED; no production default was changed.
- User-mode QEMU validated selected ARM userspace commands only. Kernel boot, mounts, modules, DSL, Wi-Fi, firewall kernel behavior, OEM update acceptance, and hardware boot remain UNKNOWN/BLOCKED.

## OpenLinux V0.5 boot compatibility research — 2026-11-10

### VERIFIED

- Current HEAD at milestone start was `4216636`, on `codex/hybrid-server-work`, with a clean working tree and `origin` configured.
- Original uImage fields were revalidated: legacy U-Boot ARM/Linux kernel, LZMA compression, valid header/data CRCs, payload 1,434,088 bytes, load/entry `0x81208000`, name `Linux-2.6.30`.
- Decompressed kernel evidence confirms Linux 2.6.30/ARMv7, HiSilicon SD56xx/SD5610x strings, generic `root=`/`console=` parameters, generic ATAGS parser strings, SquashFS XZ support, and XZ decoder symbols. No FDT magic was found in the payload.
- Original and V0.4 SquashFS are version 4.0, little-endian, XZ, 1 MiB blocks. V0.4's `unsquashfs -s` output proves an ARM BCJ filter is present; the original has no reported filter.
- Added [analysis/openlinux/v0.5/evidence.json](analysis/openlinux/v0.5/evidence.json), [report.md](analysis/openlinux/v0.5/report.md), [squashfs-deep-analysis.md](analysis/openlinux/v0.5/squashfs-deep-analysis.md), [kernel-analysis.md](analysis/openlinux/v0.5/kernel-analysis.md), [boot-protocol.md](analysis/openlinux/v0.5/boot-protocol.md), [qemu-feasibility.md](analysis/openlinux/v0.5/qemu-feasibility.md), and [hardware-test-plan.md](analysis/openlinux/v0.5/hardware-test-plan.md).

### PARTIALLY VERIFIED

- The kernel supports generic ATAGS parsing, but no artifact proves that the HG630 bootloader supplies ATAGS. No artifact proves a device-tree handoff either.
- Ordinary XZ is strongly supported by kernel strings and the original filesystem. ARM BCJ is proven in the V0.4 image but not in the target kernel.
- ARM user-mode execution remains useful for selected userspace checks; it is not kernel or hardware boot validation.

### UNKNOWN / BLOCKED

- Kernel `.config`, machine ID, RAM base/size, UART address/IRQ/baud, command line, initrd use, root MTD partition, mount flags, and bootloader handoff remain UNKNOWN.
- V0.4 ARM BCJ XZ compatibility is UNKNOWN/BLOCKED. The recommended proven format is ordinary XZ without BCJ, but its expanded image may exceed the verified fixed span.
- No QEMU system machine models HiSilicon SD56xx/SD5610x; meaningful kernel boot emulation is BLOCKED.
- Hardware validation requires read-only UART/proc/dmesg observation and an independent recovery path. No physical MTD, flash, bootloader environment, or router was accessed.

## OpenLinux V0.6 hardware discovery and BCJ research — 2026-11-10

### VERIFIED

- Current HEAD at start was `455c8e0`; previous artifacts and firmware were preserved.
- Controlled development-host SquashFS tests generated ordinary XZ and XZ+ARM-BCJ images from the same stage. Both extracted successfully and produced identical extracted BusyBox hashes. `unsquashfs -s` reported `Filters selected: arm` only for the BCJ image.
- Original kernel strings contain `squashfs_xz_init`, `xz_dec_init`, and `xz_dec_run`; no kernel config, ARM BCJ config, or BCJ-specific symbol was found.
- Added [analysis/openlinux/v0.6/bcj-investigation.md](analysis/openlinux/v0.6/bcj-investigation.md), [squashfs-test-matrix.json](analysis/openlinux/v0.6/squashfs-test-matrix.json), [evidence.json](analysis/openlinux/v0.6/evidence.json), and [report.md](analysis/openlinux/v0.6/report.md).
- Added the BusyBox-ash-compatible, read-only [tools/hardware_discovery.sh](tools/hardware_discovery.sh), with tests. It only reads `/proc`, `/sys`, `/dev`, module directories, and dmesg; it does not write MTD, bootloader state, or router files.
- Added [hardware-discovery.md](analysis/openlinux/v0.6/hardware-discovery.md) with safe UART identification, passive capture, read-only collection, and recovery requirements.
- Full test suite passes **54/54** after V0.6 additions.

### PARTIALLY VERIFIED

- Development-host extraction proves the filesystem metadata distinction and host tool behavior, not target-kernel decompressor behavior.
- Ordinary XZ remains the only filesystem configuration directly matched by original filesystem and kernel evidence. No compatibility candidate was built because ordinary XZ may exceed the fixed component span and BCJ support is unproven.

### UNKNOWN / BLOCKED

- ARM BCJ support in the original 2.6.30 kernel, kernel configuration, machine ID, RAM size/base, flash type/capacity, UART, bootloader version, root MTD partition, and command line remain UNKNOWN pending hardware or matching source artifacts.
- No compatible QEMU system machine exists. No router, MTD, bootloader, UART, or firmware write was accessed in this milestone.

## OpenLinux V0.7 OEM-preserving deployment feasibility — 2026-11-10

### VERIFIED

- Current HEAD at milestone start was `588d59c` on `codex/hybrid-server-work`; previous artifacts were preserved.
- Added `tools/analyze_deployment_feasibility.py` and synthetic tests. It parses the known firmware structures and inventories only extracted RootFS text/configuration files without executing OEM programs or accessing MTD.
- The original package contains metadata, SquashFS at `0x305cf`, uImage at `0x5d85cf`, and suffix bytes. Embedded uImage header/data CRCs validate. The metadata extents reach `0xfd0000`, beyond the package size, so they are not direct package offsets.
- Static RootFS evidence confirms BusyBox init, `/etc/inittab` sysinit/respawn, vendor `/etc/profile` startup, conditional `mtdblock7`/`mtdblock12` mounts, `/dev/caldata -> /dev/mtd9`, and preserved vendor services/libraries/modules.
- Added V0.7 reports and machine-readable [evidence.json](analysis/openlinux/v0.7/evidence.json).
- Full test suite passes after V0.7 additions; no original firmware, prior artifact, router, MTD, or bootloader was modified/accessed.

### PARTIALLY VERIFIED

- Same-layout RootFS replacement preserves the original kernel and metadata in a non-flashable experimental artifact.
- An additional userspace layer is viable for staged/operator-controlled testing against the preserved RootFS, but persistent launch and storage are not established.
- The updater exposes separate generic/area/configuration/bootloader paths and logical MTD indices 0–15, but higher-level selection remains unresolved.

### UNKNOWN / BLOCKED

- Exact meaning of `main_*`/`slave_*`, dual-image behavior, section-to-MTD mapping, RootFS-only update support, root MTD/mount parameters, OEM signature/outer checksum, and recovery behavior remain UNKNOWN/BLOCKED.
- Original-kernel ARM BCJ support remains UNKNOWN; V0.4 used ARM BCJ and is not claimed kernel-compatible.
- Recommended current architecture is Approach C: non-persistent, operator-controlled userspace development while preserving the OEM RootFS. No Approach A/B deployment is authorized.

## OpenLinux V0.9 first bootable emulator image — 2026-11-10

### VERIFIED

- Current HEAD at milestone start was `36bfe23`; original firmware and V0.1–V0.8 artifacts were preserved.
- Installed a Debian ARM EABI5 cross-toolchain and Linux source externally under `/home/ayad/build-output/openlinux-v09`.
- Built Linux 6.12.116 ARM `vexpress_defconfig`, a V2P-CA9 DTB, and a static ARM BusyBox 1.37.0.
- Added `tools/build_qemu_image.py` and tests. It creates a standalone gzip-newc-cpio initramfs with BusyBox init, OpenLinux status/monitor/logging, and all services disabled by default.
- Booted the bundle with QEMU 10.0.13 `vexpress-a9`, 256 MiB RAM, the V2P-CA9 DTB, and PL011 `ttyAMA0`. The kernel unpacked the initramfs, executed init, ran OpenLinux status/monitor/logging, reached `OPENLINUX_READY`, and provided an interactive shell. Full log: [analysis/openlinux/v0.9/boot-logs/vexpress-a9-boot.log](analysis/openlinux/v0.9/boot-logs/vexpress-a9-boot.log).
- V0.9 kernel SHA256: `b7ec99aa772542c52e85bdc2ffd04065a18e6b0b16c3ec519beb5fca2366aca1`.
- V0.9 initramfs SHA256: `84b8e52875f2831f57a58b7bd6fad2634e01e18db99b850907f00fe83d83b98c`.
- V0.9 DTB SHA256: `cb35d197143510bcdadf022f925c23735c4e453f4aa7a207cfbc2b6fb99cb24d`.
- Added [analysis/openlinux/v0.9/report.md](analysis/openlinux/v0.9/report.md), [boot-targets.md](analysis/openlinux/v0.9/boot-targets.md), [build-manifest.json](analysis/openlinux/v0.9/build-manifest.json), and [hg630-compatibility.md](analysis/openlinux/v0.9/hg630-compatibility.md).

### PARTIALLY VERIFIED

- The emulator image provides shell, status, memory/uptime/mount reporting, and bounded logging. Network, SSH, DHCP, DNS, firewall, and web services remain disabled and were not hardware-tested.
- The emulator's `poweroff` command did not terminate QEMU reliably; clean shutdown is not claimed.

### UNKNOWN / BLOCKED

- This image targets QEMU `vexpress-a9`, not HiSilicon SD5610x. It proves no HG630 kernel, RootFS mount, DSL, Ethernet, Wi-Fi, calibration, OEM update, or router hardware behavior.
- Actual HG630 boot remains blocked by unknown machine handoff, RAM, root MTD, command line, BCJ support, OEM signature, and recovery evidence. No router-specific bootable image was produced.

## OpenLinux V1.0 flashability decision — 2026-11-10

### VERIFIED

- Audited the original package with the existing read-only parser. Original
  SHA256 is `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`.
- Verified the embedded SquashFS at `0x305cf`, the legacy ARM/LZMA uImage at
  `0x5d85cf`, uImage header/data CRCs, and original kernel uImage SHA256
  `13a3432e8d2bbce07c5d0a49e157d77c3c183cad445dfb16be3c3bcaaa75ebc7`.
- Generated the V1.0 component map, flash-format, signature, preservation,
  checklist, recovery, and build-manifest documents.
- Generated `/home/ayad/build-output/custom-build/firmware-run-v10/HG630V2-OpenLinux-v1.0-experimental.bin` using the existing same-span builder. Its SHA256 is
  `9ec2d00ffa546c7b0d3be228c0867fba7ffac2a5e354c6b22d249d1035ab5cb1`.
  It preserves the original kernel and unknown package bytes, and is identical
  to the prior V0.4 experimental artifact because the inputs are unchanged.

### PARTIALLY VERIFIED

- The V0.4-derived RootFS contains the controlled OpenLinux additions while
  retaining the observed vendor DSL/network/library/module/init inventory.
  Host extraction and file-level comparison do not prove target-kernel mount or
  hardware compatibility.

### UNKNOWN / BLOCKED

- The OEM signature key/material, signed byte range, RSA encoding/padding,
  outer checksum, main/slave semantics, section-to-MTD mapping, RootFS-only
  update path, root MTD, ARM BCJ support, and recovery procedure remain
  unresolved.
- A genuinely installable HG630 V2 image is **BLOCKED**. No artifact is labeled
  FLASHABLE, no OEM trust mechanism was bypassed, and no physical router/MTD or
  bootloader environment was accessed.


## Firmware package reconstruction milestone — 2026-11-11

### VERIFIED FROM OWNER-PROVIDED OEM BINARY

- Exact OEM package SHA-256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`; size 7,563,600 bytes.
- Package magic: `10 32 54 76`; product/version strings identify HG630 V2 / V100R001C298B010.
- Four observed 44-byte big-endian component records begin at `0x7c). They are contiguous: component 17 at `0x5cf` size `0x20000`; component 3 at `0x205cf` size `0x10000`; RootFS component 1 at `0x305cf` size `0x5a8000`; kernel component 2 at `0x5d85cf` size `0x15e228`.
- RootFS internal bytes_used is 5,930,917; its calculated end is `0x5d8574`, leaving 91 bytes before the uImage header.
- Original uImage header and payload CRC32 both validate. It is Linux 2.6.30, payload size 1,434,088, load/entry `0x81208000`.
- uImage ends at `0x7367f7`; 345 bytes remain. The first 89 bytes are zero and final 256 bytes are high entropy. Treat the latter only as a possible signature blob; signature semantics/key are unknown.
- Component table parser was added to `tools/firmware_inspect.py`, scoped only to this observed HG630 V2 package layout.

### IMPLEMENTED

- Added `tools/rebuild_firmware.py` to replace only the reserved RootFS slot while preserving the package prefix and all bytes from the original kernel offset through EOF.
- The reconstruction tool verifies exact OEM SHA-256/size, observed component table and RootFS/kernel extents, candidate SquashFS 4.0/XZ/1 MiB profile and fit, and original uImage CRCs.
- It emits a JSON report and remains hard-coded to `EXPERIMENTAL_NON_FLASHABLE`; it does not rewrite unknown Huawei checksums or signatures.
- By default it runs `unsquashfs` structural/extraction validation and can compare the extracted candidate against the staged RootFS.
- Added `tests/test_rebuild_firmware.py` and component-table tests in `tests/test_firmware_inspect.py`.
- Corrected the decimal RootFS start/end arithmetic in `docs/ANALYSIS.md` (198,095 start; 6,129,012 end; 91-byte gap).
- Added `analysis/server-run/firmware-reconstruction-report.md` and README instructions.

### UNKNOWN / BLOCKED

- Huawei header fields before the observed component table and any package-level checksum semantics remain unknown.
- The final 256-byte high-entropy tail may be signature material, but no signature algorithm, signed range, or public key has been identified.
- The reconstruction utility has not yet been executed against the winning RootFS artifact on the user's build host; that artifact is not stored in the Git repository.
- No updater acceptance, target-kernel mount, router boot, flash map, recovery path, or hardware behavior has been demonstrated.
- Keep `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`. Do not flash.
