# Vendor startup dependencies

| Component | Evidence | Classification |
|---|---|---|
| BusyBox init | `/etc/inittab`, `/init`, `/sbin/init` | VERIFIED |
| Runtime mounts | `/etc/profile` mount commands | VERIFIED |
| Device nodes | `makedevs`, `startbsp` `mknod` calls | VERIFIED |
| HiSilicon SDK/network/PHY | `startbsp` insmod list and matching modules | VERIFIED |
| DSL/XPON | `hi_xpon`, `hi_k*` modules, `xdslcmd`/`xtmcmd` tools | VERIFIED/INFERRED |
| Ethernet/Wi-Fi | `startbsp`, `insmod_all.sh`, `hsanportinit` | VERIFIED/INFERRED |
| Vendor application manager | `/bin/mic`, fork/exec/restart strings | VERIFIED |
| DHCP/DNS/firewall | `mic` strings plus `/bin/dhcps`, `/bin/dns`, `/bin/iptables` | INFERRED launch order |
| Web/CWMP/UPnP | binaries and libraries present; no direct init call | VERIFIED present, UNKNOWN launch order |
| Calibration | `/dev/caldata -> /dev/mtd9` in `/etc/profile` | VERIFIED reference, partition semantics UNKNOWN |
| Shutdown | ctrlaltdel entry commented; BusyBox handlers present | VERIFIED/UNKNOWN order |
| Watchdog | no dedicated watchdog entry found | UNKNOWN runtime behavior |

The vendor path assumes `/proc`, `/sys`, `/dev`, tmpfs, module loading,
`/dev/mtd9`, `/var`, and hardware-specific character devices. OpenLinux must
not start before those assumptions are satisfied. V0.4 consequently keeps the
hook outside the OEM path and leaves all service enablement opt-in.
