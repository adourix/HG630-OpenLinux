# Report 5 — ARM ABI and isolated build design

The package-level uImage evidence records ARM architecture ID 2. The server-run inventory records 227 little-endian ARM ELF files, but its committed ABI result contains no raw ELF flags or attributes and therefore does not identify the float ABI. The corrected `tools/detect_abi.py` parses each ELF header directly, records architecture and raw `e_flags`, and decodes `.ARM.attributes` when present. It distinguishes:

- `arm-linux-gnueabi` for base AAPCS/soft-float binaries;
- `arm-linux-gnueabihf` for binaries using VFP hard-float calling conventions;
- an explicit undetermined result when the extracted evidence is mixed, absent, or incomplete. It never treats an ARM architecture ID alone as hard- or soft-float evidence.

The Debian 13 `build/Dockerfile` installs both toolchains, SquashFS tooling, binutils, Python, and the existing tests. It is an analysis/non-flashable environment only; it does not install services on the host or generate a firmware image.
