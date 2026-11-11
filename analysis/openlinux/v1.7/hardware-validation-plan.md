# V1.7 later hardware validation plan

No router operation was performed for V1.7. This plan is for a later separately authorized maintenance session; the current task explicitly disallows execution on the device.

## Read-only commands (do not mount, start services, or alter config)

From an already documented, authorized shell only, record outputs without exposing credentials or calibration contents:

```sh
uname -a
cat /proc/version
cat /proc/cmdline
cat /proc/filesystems
cat /proc/mounts
ls -l /dev/ptmx /dev/pts /bin/sshd /bin/sh
cat /etc/inittab
cat /etc/fstab
awk -F: '{print $1, $3, $4, $6, $7}' /etc/passwd1
awk -F: '{print $1, $3}' /etc/group1
/bin/sshd -V
/bin/sshd -h
/bin/ip addr show
```

Run the package diagnostic with explicit proc/dev roots if needed:

```sh
/absolute/path/openlinux/bin/openlinuxctl ssh-check
/absolute/path/openlinux/bin/openlinuxctl ssh-status
```

These commands are diagnostic only; `sshd -h`/`-V` must exit without opening a listener. Verify the LAN management address and interface mapping with the OEM's documented read-only network tools. Do not publish `/proc`, account hashes, keys, or full config backups. Record whether `devpts` appears in `/proc/filesystems` and `/proc/mounts`; record a controlled PTY allocation result only after a separate reviewed test plan exists. Do not copy passwords or shadow contents into the report.

## State-changing checks — currently prohibited

The following are **not authorized by this plan**: mounting devpts; writing `authorized_keys`; creating accounts; generating host keys; starting/stopping Dropbear; changing `sshusers.cfg`; changing firewall/ACL; editing startup; touching MTD or firmware. Those require separate authorization, a vendor-supported shell/access path, proven recovery, and a verified account/host-key design. Never upload an experimental firmware image through the web updater.
