# OEM init order and integration boundary

## Verified path

The BusyBox init configuration contains:

```text
::sysinit:/etc/init.d/rcS
::respawn:-/bin/sh
#::ctrlaltdel:/bin/umount -a -r
```

`rcS` only establishes `PATH` and prints `RCS DONE`. It does not call
`startbsp`, `insmod_all.sh`, `insmod_eth.sh`, or an OpenLinux hook.

The respawned shell sources `/etc/profile` in the normal BusyBox shell
environment. The profile is the observed hardware startup path:

1. sets `PATH` and `LUA_PATH`;
2. mounts tmpfs on `/dev`, `/var`, `/tmp`, `/mnt`, and proc/sysfs;
3. runs `makedevs`;
4. runs `/bin/startbsp`, which creates device nodes and loads HiSilicon,
   Huawei, Ethernet, DSL, and Wi-Fi modules;
5. runs `hi_xpon`;
6. starts `hsanportinit` in the background;
7. starts `/etc/insmod_all.sh` in the background;
8. links `/dev/caldata` to `/dev/mtd9`;
9. starts `/bin/mic`, the vendor dynamic application manager.

This ordering is based on actual script calls, not filenames. `mic` strings
reference `sshd`, `dhcps`, `iptables`, `ddns`, and restart/process-management
operations, but exact application order is **INFERRED**, not proven. The vendor
DSL, Ethernet, Wi-Fi, firewall, DHCP, DNS, web, CWMP, and management services
therefore remain owned by the profile/startbsp/mic path.

## OpenLinux decision

The existing `/etc/init.d/openlinux` file is not called by the OEM path. This is
the safest current state: it cannot reorder or interrupt OEM startup. V0.4
hardens the hook for explicit simulation/manual invocation with missing-config
handling, validation, bounded timeout, failure logging, and exit-zero failure
isolation. It is deliberately **not** injected into `rcS` or `/etc/profile`.

Adding it to `/etc/profile` would risk repeated execution whenever the shell
respawned, while changing `rcS` would replace the only verified sysinit script.
No evidence establishes a one-shot vendor application-manager callback. Safe
automatic integration is therefore **UNKNOWN/BLOCKED**.
