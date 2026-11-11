# OpenLinux V0.6 hardware discovery and boot compatibility

Date: 2026-11-10

## Result

V0.6 closes the software-side investigation that can be completed without the
router. It proves that modern SquashFS tooling distinguishes ordinary XZ from
ARM-BCJ XZ and that both extract on the development host. It does not prove that
the original 2.6.30 kernel accepts ARM BCJ. No safer fixed-span compatibility
candidate was built because ordinary XZ may exceed the OEM replacement span and
BCJ remains unproven.

## Classification

- Original uImage structure/CRC: **VERIFIED**.
- ARMv7/Linux 2.6.30/HiSilicon SD56xx family: **VERIFIED**.
- Generic XZ SquashFS support in kernel: **VERIFIED STATIC**.
- ARM BCJ support in kernel: **UNKNOWN**.
- V0.4 ARM BCJ metadata: **VERIFIED**.
- Actual kernel RootFS mount: **UNKNOWN/BLOCKED**.
- Compatible QEMU system machine: **BLOCKED**.
- Hardware identity, RAM, flash, UART, machine ID, root MTD, and command line:
  **UNKNOWN** pending read-only serial discovery.

## Hardware preparation

The read-only collector [hardware_discovery.sh](../../../tools/hardware_discovery.sh)
and [hardware-discovery.md](hardware-discovery.md) prepare a safe discovery
session. They do not transmit commands, interrupt autoboot, write files on the
router, access MTD, or alter bootloader state.

## Preserved artifacts

V0.1 through V0.5 artifacts remain preserved. No firmware was rebuilt or
deployed in V0.6. The controlled BCJ test images are external analysis outputs
under `/home/ayad/build-output/v06-bcj-tests/` and are not firmware candidates.
