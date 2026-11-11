# Non-destructive hardware validation plan

This is a read-only observation plan. It authorizes no flash write, bootloader
environment change, MTD erase/write, or experimental firmware installation.

## Preparation

1. Identify the exact HG630 V2 board revision and photograph SoC/flash/UART
   markings without powering modifications.
2. Use a 3.3 V-compatible USB-TTL adapter with verified voltage levels; never
   connect RS-232 levels directly to the board.
3. Connect only GND, board TX to adapter RX, and board RX to adapter TX after
   locating the header with power removed. Do not connect adapter VCC.
4. Capture the original boot log at candidate rates, beginning with 115200 8N1
   only as a measurement starting point; the correct rate remains UNKNOWN.

## Read-only observations

If the existing firmware reaches a shell, collect and preserve output from:

```sh
cat /proc/cpuinfo
cat /proc/meminfo
cat /proc/cmdline
cat /proc/mtd
cat /proc/mounts
dmesg
uname -a
```

These commands are observational. Do not run `mtd`, `flash_erase`, `nandwrite`,
`upg`, `reboot`, `fw_setenv`, or any vendor flash/update command. Preserve raw
UART output and hashes outside Git before interpretation.

## Hardware identification checks

Correlate `/proc/cpuinfo`, kernel `Machine:` output, `/proc/mtd`, boot console
arguments, RAM size, and UART device with the static SD56xx evidence. A valid
result must identify the board and show the existing firmware booted normally;
absence of one field is not permission to infer it.

## Recovery requirements

Before any future boot experiment, establish an independent serial recovery
path, known-good original firmware recovery procedure, power-cycling procedure,
and a way to stop before any bootloader write/update command. The original
firmware and V0.1–V0.4 artifacts must remain preserved. A failed boot log alone
does not justify a flash attempt.
