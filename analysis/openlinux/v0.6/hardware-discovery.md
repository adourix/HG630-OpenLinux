# HG630 V2 hardware discovery session

This guide is observation-only. It does not instruct the operator to flash,
erase, write MTD, alter bootloader variables, or interrupt boot.

## Adapter and header safety

- Use a USB-UART adapter with 3.3 V TTL signaling and selectable/verified logic
  levels. Do not use RS-232 voltage levels.
- With the router powered off, identify a likely header by board silkscreen,
  continuity, and voltage measurement. Do not connect adapter VCC.
- Connect only common ground and crossed data lines after voltage compatibility
  is established: board TX to adapter RX, board RX to adapter TX.
- If the header or voltage cannot be identified confidently, stop. This project
  does not infer a pinout from generic HG630 photographs.

## Serial observation

Start with a passive terminal capture and no transmitted characters. Candidate
baud rates may be tested by observation only; 115200 8N1 is a common starting
point, not a verified HG630 setting. Record the working rate from recognizable
boot text, not from assumption.

Capture power-on through the complete Linux startup. Do not press keys to stop
autoboot until a recovery procedure and the exact prompt behavior are known.
If a bootloader prompt appears naturally, record its banner/version and wait;
do not issue commands.

## Read-only shell collection

If the original firmware reaches a shell, manually run and save output from:

```sh
uname -a
cat /proc/cpuinfo
cat /proc/cmdline
cat /proc/meminfo
cat /proc/mtd
cat /proc/mounts
cat /proc/filesystems
cat /proc/modules
cat /proc/partitions
cat /proc/net/dev
ls -l /dev
ls -l /sys/class/net
dmesg
```

The repository contains [hardware_discovery.sh](../../../tools/hardware_discovery.sh),
which emits the same categories using BusyBox-compatible read-only commands.
Review the script before use. Redirect its output only to a host-side capture
path selected by the operator; the script itself performs no file writes.

## Identification targets

The session should seek direct evidence for SoC revision, RAM size, flash type
and capacity, UART/console, machine name, command line, MTD partitions, and
mount arguments. Existing static facts—board ID 1212, SD56xx strings, `/dev/mtd9`
calibration reference, and uImage load address—must be compared with live output
but not substituted for it.

## Recovery boundary

Before any future experimental boot, preserve a complete original UART log,
verify an independent serial recovery path, and document the OEM recovery method.
No experimental firmware deployment is part of this discovery session.
