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

- configuration validation: VERIFIED by host tests and ARM user-mode execution;
- network inspection, static/DHCP validation, and dry-run command generation:
  VERIFIED; no default state changes;
- DHCP/DNS generation with OpenLinux-owned static lease and host inputs:
  VERIFIED; no dnsmasq binary exists in the OEM RootFS, so no daemon restart is
  attempted;
- firewall backend detection and proposed-rule validation: VERIFIED against the
  preserved vendor `/bin/iptables`; no rules are flushed or applied;
- SSH status/config validation: VERIFIED against the preserved `/bin/sshd`, but
  SSH remains disabled by default;
- `/proc` monitor and bounded log status interfaces: implemented and tested;
- service dependency ordering and actual boot-time invocation: UNKNOWN until
  the vendor boot sequence is mapped;
- kernel or hardware integration: UNKNOWN/BLOCKED.

The V0.3 component report is [v0.3-report.md](v0.3-report.md), with the small
build summary in [v0.3-manifest.json](v0.3-manifest.json).
