# Implementation status

Current phase: offline reverse engineering. This is not a completed firmware port.

## Current Debian-server limitation

The expected firmware input and `~/build-output/` directory are not present on the migrated server. The branch contains reproducible extraction, inventory, ABI-detection, and Docker tooling, but no new firmware extraction or DSL inventory can be verified until the original input is made available at a local path.

## Delivered
- Device identity, feasibility, DSL and recovery requirements documented.
- OEM update package SHA-256 and embedded offsets documented.
- Read-only Python parser for U-Boot uImage and SquashFS superblock metadata.
- Unit tests and GitHub Actions CI.
- Latest CI run completed successfully: 3 unit tests and Python syntax check passed.

## Verified from the supplied image
- Size: 7,563,600 bytes.
- SHA-256: d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222.
- SquashFS v4 superblock at 0x305cf; LZMA compression ID 4; 1,257 inodes; 1 MiB block size; bytes_used 5,930,917.
- uImage at 0x5d85cf; kernel name Linux-2.6.30; payload size 1,434,088 bytes; load and entry address 0x81208000.
- Both uImage header and payload CRCs validate.
- Package string board_id=1212 is observed but is not proven to equal the physical CFE board ID.

## Not delivered
- Extracted root filesystem.
- Kernel source/config matching the OEM build.
- DSL driver/firmware/daemon dependency inventory.
- Verified exact VER.B PCB, CFE board ID or flash partition layout.
- Working DSL-preserving replacement kernel/userspace.
- Device Tree or board support.
- Any flashable firmware.

## Current blocker
The available local execution environment has no SquashFS extractor installed. The image uses SquashFS v4 with LZMA compression (compression ID 4). Extraction should be performed with a compatible trusted extractor in an isolated Linux environment. A generic upstream unsquashfs build may not support every vendor LZMA variant; tool compatibility must be verified before declaring extraction successful.

## Next engineering task
Extract and inventory the root filesystem locally. Identify DSL kernel modules, firmware blobs, control daemons, shared libraries and init scripts. Do not publish proprietary binaries or the router configuration backup.
