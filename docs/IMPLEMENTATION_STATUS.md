# Implementation status

Current phase: offline reverse engineering. This is not a completed firmware port.

## Delivered in repository
- Device identity and limitations documented.
- OEM firmware SHA-256 and observed embedded section offsets documented.
- Read-only Python parser for legacy uImage and SquashFS headers.
- Unit tests and GitHub Actions workflow.

## Verification
- Three unit tests pass locally in the development workspace.
- The parser validates uImage header and payload CRCs.
- It is deliberately not a firmware extractor, image builder or flasher.

## Not delivered yet
- Extracted root filesystem.
- Kernel source/config matching the OEM build.
- DSL driver/firmware/daemon inventory.
- Verified exact VER.B PCB, CFE board ID and flash partition map.
- Device Tree / board support.
- DSL-preserving replacement kernel or userspace.
- Flashable firmware.

## Next engineering task
Extract the SquashFS v4 LZMA filesystem in an isolated local workspace. Inventory ELF architecture, shared-library dependencies, kernel modules and DSL initialization. Do not publish proprietary binaries or the router configuration backup.
