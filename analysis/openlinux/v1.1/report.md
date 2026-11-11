# OpenLinux V1.1 report

## Result

V1.1 improves the evidence base but does not produce a flashable image. The
release classification remains **RESEARCH_ONLY**. No new image was built;
rebuilding the unchanged V1.0 experimental bytes would add no evidence.

## Proven

- SD56xx/SD5610x family and ARMv7 Linux 2.6.30 vendor kernel are verified.
- The kernel uImage, LZMA payload, load/entry addresses, and CRCs are verified.
- The vendor DSL stack is identified statically as Triductor-based and tied to
  2.6.30 ARMv7 modules, firmware/data, tools, and device initialization.
- SD56xx Ethernet SDK/PHY modules and multiple optional Wi-Fi drivers are
  present. The active Wi-Fi chipset is not established.
- The package component map is verified; physical flash layout is not.
- The update mechanism and cryptographic wrappers are present, but OEM
  authentication and metadata-to-MTD semantics remain unresolved.
- The release-classification validator now rejects a `FLASHABLE` manifest
  unless all target, authentication, recovery, and RootFS gates are VERIFIED.

## Not proven

Exact silicon/PCB revision, RAM/flash geometry, bootloader handoff, command
line, root MTD, active Wi-Fi hardware, target-kernel BCJ support, DSL runtime,
PPPoE, hardware boot, recovery, OEM signature acceptance, and a RootFS-only
update path.

## Recommended architecture

Preserve the original Huawei kernel and vendor DSL/Ethernet/Wi-Fi stack while
developing an additive userspace. Do not select an upstream replacement kernel
or generate a deployment image until hardware and recovery evidence closes the
gates.

No router, physical MTD, bootloader environment, or updater was accessed.
