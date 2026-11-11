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
