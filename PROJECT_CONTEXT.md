# HG630-OpenLinux recovered mission state

Updated: 2026-11-10 20:00 America/New_York

## Recovery status

- Recovered after the previous Codex session exited.
- No `AGENTS.md` exists under `/root/projects` or this repository.
- No earlier `PROJECT_CONTEXT.md` existed; this file is the recovery record.
- Git branch: `codex/hybrid-server-work`, at `1ce224a` (`Fix AEABI attributes parsing and ABI evidence`).
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
