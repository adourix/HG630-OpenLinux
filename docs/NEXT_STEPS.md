# Next steps

## Phase 0 — Preserve evidence

- [ ] Keep the original firmware binary locally and verify its SHA-256.
- [ ] Keep the router configuration backup local and private.
- [ ] Record exact router UI hardware/software versions.
- [ ] Obtain a vendor firmware source and published checksum, if available.
- [ ] Capture firmware update page details without starting an update.

## Phase 1 — Static firmware analysis

- [ ] Run `tools/firmware_inspect.py` on the original image.
- [ ] Install a compatible SquashFS 4.0 LZMA extractor in an isolated environment.
- [ ] Extract root filesystem to a local ignored directory.
- [ ] Inventory ELF executables, shared libraries and kernel modules.
- [ ] Identify DSL driver modules, DSL firmware and DSL management daemons.
- [ ] Identify Ethernet and wireless drivers and firmware.
- [ ] Extract init scripts and boot configuration.
- [ ] Determine architecture, endianness, ABI, libc and toolchain.

## Phase 2 — Platform and flash map

- [ ] Confirm exact PCB revision without assuming model-name equivalence.
- [ ] Confirm SoC independently.
- [ ] Find exact CFE board identifier.
- [ ] Determine flash chip and geometry.
- [ ] Derive partition map from image metadata and trusted platform source.
- [ ] Identify calibration/NVRAM/board-data regions and protect them.
- [ ] Document serial-console method only from verified evidence.

## Phase 3 — DSL feasibility

- [ ] Identify DSL kernel module names and exported dependencies.
- [ ] Identify firmware files and expected paths.
- [ ] Identify proprietary management/control daemons.
- [ ] Identify required shared libraries and ioctl interfaces.
- [ ] Verify availability of matching GPL kernel source/config/toolchain.
- [ ] Assess whether DSL can run on an upstream kernel.
- [ ] If not, evaluate a vendor-kernel-derived minimal userspace.

## Phase 4 — Build and test

- [ ] Create reproducible build container/toolchain.
- [ ] Build user-space tooling without touching device flash.
- [ ] Add a host-side image parser test suite.
- [ ] Add static analysis and license inventory.
- [ ] Build a non-flashable development artifact first.
- [ ] Define recovery plan before any device write.

## V1.1 evidence-driven blockers

- [ ] Obtain an exact-board passive UART capture without interrupting boot.
- [ ] Record `/proc/cpuinfo`, `/proc/meminfo`, `/proc/mtd`, `/proc/cmdline`,
      mounts, loaded modules, and read-only DSL/Wi-Fi inventory.
- [ ] Obtain matching Huawei GPL source/configuration, if available, and
      compare the SD5610x machine setup and SquashFS XZ options.
- [ ] Identify the installed Wi-Fi module from hardware or live module state;
      do not choose among the bundled candidates by filename.
- [ ] Establish flash part, erase geometry, MTD partitions, root MTD, and
      protected calibration/board-data regions from independent evidence.
- [ ] Resolve the OEM signature format and legitimate acceptance path; do not
      bypass authentication or invent credentials.
- [ ] Verify an independent recovery and rollback procedure before any write.
- [ ] Only then evaluate a target-compatible RootFS and signed package.

Current phase: V1.1 platform, boot-chain, flash-layout, DSL-preservation, and
OEM-authentication research. No flashable image is authorized.
