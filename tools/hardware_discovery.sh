#!/bin/sh
# Read-only HG630 discovery collector. BusyBox ash compatible.
# It writes nothing, opens no MTD device, and does not interrupt boot.

section() { echo; echo "===== $1 ====="; }
show_file() { file=$1; if [ -r "$file" ]; then cat "$file"; else echo "UNAVAILABLE: $file"; fi; }

section "uname"
uname -a 2>/dev/null || echo unavailable
section "cpuinfo"
show_file /proc/cpuinfo
section "cmdline"
show_file /proc/cmdline
section "meminfo"
show_file /proc/meminfo
section "mtd"
show_file /proc/mtd
section "mounts"
if command -v mount >/dev/null 2>&1; then mount 2>/dev/null || show_file /proc/mounts; else show_file /proc/mounts; fi
section "filesystems"
show_file /proc/filesystems
section "modules"
show_file /proc/modules
section "partitions"
show_file /proc/partitions
section "devices"
ls -l /dev 2>/dev/null || echo unavailable
section "network_proc"
show_file /proc/net/dev
section "network_sysfs"
ls -l /sys/class/net 2>/dev/null || echo unavailable
section "vendor_modules"
ls -l /lib/extra /lib/kernel 2>/dev/null || echo unavailable
section "dmesg"
dmesg 2>/dev/null || echo unavailable
section "end"
echo "READ_ONLY_COLLECTION_COMPLETE"
