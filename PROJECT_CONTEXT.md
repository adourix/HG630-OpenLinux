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
