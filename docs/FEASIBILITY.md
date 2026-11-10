# Technical feasibility assessment

## Executive summary

A Linux firmware investigation is feasible. A replacement firmware that preserves the integrated DSL modem is unproven and has a high technical risk until the original DSL stack is identified.

The vendor image identifies a Linux 2.6.30 kernel. DSL functionality on Broadcom DSL SoCs may depend on kernel drivers, firmware blobs, proprietary user-space components and board-specific data. Replacing only the root filesystem or kernel can break DSL synchronization.

## Directly observed from the owner's device and image

- Product: Huawei HG630 V2.
- Hardware revision: VER.B.
- Software version: V100R001C298B010.
- Firmware supplied: HG630V2-12V100R001.bin.
- Package contains `board_id=1212` (semantics not fully established).
- Legacy U-Boot uImage header names `Linux-2.6.30`.
- SquashFS little-endian magic at offset 0x305cf.
- uImage magic at offset 0x5d85cf.

## Not confirmed for this exact VER.B PCB

- SoC stepping and package marking.
- RAM size and layout.
- Flash part, capacity, erase geometry and partition map.
- CFE version and CFE board identifier.
- Integrated Wi-Fi chip and calibration data location.
- DSL PHY/AFE revision.
- Exact DSL driver and firmware compatibility requirements.

Do not turn specifications documented for another HG630 variant into hard-coded device facts.

## Candidate strategies

### A. OpenWrt port

Potentially attractive if the exact SoC is supported by a maintained target and required drivers are available. DSL is the principal blocker. Upstream Ethernet or SoC support does not prove DSL support.

### B. Vendor-kernel-derived Linux system

Potentially offers the best chance of retaining the original DSL stack by preserving the original kernel ABI and proprietary components. Risks include obsolete kernel, old toolchain, security exposure, vendor build dependencies and licensing constraints.

### C. Hybrid diagnostic/recovery system

Could be an intermediate deliverable after boot process, flash map, image format and recovery method are understood. It must never overwrite calibration, bootloader or DSL-critical partitions.

## Recommendation

Do not choose the final base prematurely. First inventory the root filesystem, kernel modules, DSL binaries, shared libraries, init scripts and configuration templates. Map dependencies before choosing OpenWrt or a vendor-derived kernel.

## Hard release gates

1. Exact PCB and flash layout confirmed.
2. Original bootloader and complete flash backup/recovery path understood.
3. Reproducible build produces an image within partition limits.
4. DSL driver and firmware demonstrably compatible.
5. DSL sync, WAN session, routing, NAT and LAN tested.
6. Wi-Fi functionality and calibration handling validated or declared unsupported.
7. Recovery procedure independently tested.

## Safety

No vendor firmware binary, router configuration backup or experimental flash image belongs in this repository. Tools must operate on local copies and default to read-only behavior.
