# V1.1 hardware platform evidence

## VERIFIED local evidence

- The package under analysis is `HG630V2-12V100R001.bin`, software
  `V100R001C298B010`, SHA256
  `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`.
- The preserved kernel is ARM EABI5 Linux 2.6.30. Its build string is
  `gcc version 4.4.6 (crosstool-NG 1.13.2 - hsan-5115)`.
- Kernel strings and vendor modules identify the HiSilicon SD56xx/SD5610x
  family. This does not establish the exact silicon revision.
- The vendor RootFS contains SD56xx SDK modules and APIs, Triductor DSL
  modules (`ipcdrv.ko`, `tri_ctl.ko`, `xdslcmd`), and several optional Wi-Fi
  implementations. The active Wi-Fi chipset is not selected by static file
  presence alone.
- The owner-supplied hardware identity is HG630 V2 VER.B. No PCB photograph,
  chip marking, RAM probe, flash probe, or serial boot log is available.

## UNKNOWN

Exact SoC revision, RAM size/base, flash part/capacity, DSL AFE/PHY revision,
Ethernet switch PHY population, active Wi-Fi chipset, UART pins, bootloader
version, and board-data layout remain UNKNOWN. The package `board_id=1212` is a
package field, not proof of a bootloader board ID.

Related HG630 reports must not be transferred: a public HG630B UART report
identifies a different Broadcom BCM63168/MIPS platform. The project therefore
does not use that profile for this SD5610x device.

## Source-release search

No exact HG630 V2 VER.B / `V100R001C298B010` official GPL source archive was
located in the searched public results. Huawei's general open-source notice is
not evidence of a product-specific source release. Matching vendor source,
kernel configuration, and board files remain a requested external dependency.

Search references: [Huawei open-source notice](https://developer.huawei.com/consumer/en/doc/quickApp-Guides/quickapp-v2-open-source-software-notice-0000001668157297/)
and the [related HG630B UART report](https://john.geek.nz/2014/06/huawei-hg630b-connecting-to-the-uart/).
The latter is explicitly not used as this device's hardware profile.
