# V1.1 DSL preservation assessment

## VERIFIED static inventory

- `ipcdrv.ko` identifies itself as a Triductor DSL packet module and exports
  DSL status/event symbols.
- `tri_ctl.ko`, `tri_image.bin`, `libtriapi.so`, `xdslcmd`, `tridiag`,
  `tricmd`, and `triboot` are present.
- `xdslcmd` exposes DSL status, line mode, profile, SRA, bitswap, trellis,
  diagnostics, and retrain operations.
- `hsanportinit` references `/var/dslinit.sh`, `nas0`, DSL initialization, and
  SD56xx port APIs.
- Vendor modules and startup scripts carry the 2.6.30 ARMv7 vermagic and are
  loaded by `startbsp`/the vendor profile.
- Ethernet functionality is represented by SD56xx SDK, Ethernet, PHY, port,
  and flow-control modules. Several Wi-Fi candidate modules are included.

## Compatibility conclusion

The DSL stack is tightly coupled to the original kernel module ABI, vendor
libraries, device nodes, and board initialization. A modern upstream kernel
replacement is not justified. The technically conservative path is a hybrid
vendor-kernel build: preserve the original kernel, modules, firmware, init,
DSL tools, calibration references, and hardware startup; add OpenLinux-owned
userspace only after passive target discovery.

DSL synchronization, PPPoE, Ethernet switching, and Wi-Fi remain UNKNOWN at
runtime because no target boot or hardware observation has occurred. The
presence of multiple Wi-Fi drivers does not identify the installed chipset.
