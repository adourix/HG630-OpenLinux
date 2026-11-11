# Report 4 — DSL stack

## Confirmed from the server-run inventory

The extracted-rootfs inventory contains 1,140 files, 227 ARM ELF files, 43 kernel modules, and one firmware candidate (`etc/tri_image.bin`). The following are confirmed filesystem components because they are present in `analysis/server-run/rootfs-inventory.json`:

- `bin/xdslcmd`;
- DSL status/control CLI endpoints under `home/cli/api/ecs/power/` and `home/cli/debug/test/power/`;
- WAN/DSL configuration templates `etc/upnp/WanDslIfCfg.xml`, `etc/upnp/WanDslLink.xml`, `etc/upnp/WanPppConn.xml`, and the related WAN connection XML files;
- SD56xx WAN control paths under `home/cli/debug/sdk/sd56xx/`, including `get_wan`, `clr_wan`, WAN-station attributes, and WAN-ID operations;
- vendor kernel modules under `lib/extra/` and `lib/kernel/`, including the `hi_kcfe_*` control/forwarding family, `hi_ksoft_qos.ko`, and `tri_ctl.ko`.

These names establish that DSL/WAN control, configuration, and vendor kernel integration are present in the rootfs. They do not, by themselves, identify the modem firmware format, the exact module-to-daemon dependency graph, or a stable ABI.

## Remaining unknowns

The inventory does not establish which module trains the DSL line, where `tri_image.bin` is loaded, which daemon owns synchronization, the required kernel symbols/vermagic/ioctls, the shared-library closure, or whether the listed CLI endpoints are production paths. Init ordering and runtime behavior also remain unverified. The committed ABI JSON records 227 ARM ELF files but no hard- or soft-float markers, so the userspace ABI remains inconclusive pending corrected representative-ELF evidence.

DSL remains a mandatory acceptance requirement. A replacement userspace or kernel must preserve the original kernel/DSL ABI until the dependency graph is identified and DSL synchronization, WAN session, reconnect, and sustained traffic are tested on hardware. No hardware was accessed or modified.
