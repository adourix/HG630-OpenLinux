# OpenLinux userspace

The first userspace component is an additive BusyBox-compatible supervisor at
`/usr/sbin/openlinuxctl`. It validates service configuration, reports service
state, and runs only explicitly enabled service hooks. Services are disabled by
default, and the network hook is a dry-run until SD5610x device names and vendor
startup ordering are verified.

The overlay adds `/etc/init.d/openlinux`; the original boot script, vendor
libraries, kernel, modules, DSL stack, and hardware initialization remain
untouched.

Status:

- configuration validation: implemented and host-testable;
- ARM user-mode execution: covered where `qemu-arm` and the preserved RootFS
  are available;
- service dependency ordering: UNKNOWN until the vendor boot sequence is mapped;
- DHCP/DNS/SSH/firewall/web implementations: not yet implemented;
- kernel or hardware integration: UNKNOWN/BLOCKED.
