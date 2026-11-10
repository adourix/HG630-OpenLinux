# Report 5 — ARM ABI and isolated build design

The package-level uImage evidence records ARM architecture ID 2, but the correct userspace cross ABI is not determined until representative rootfs ELF files are inspected. The new `tools/detect_abi.py` reads ELF AEABI attributes with `readelf` and distinguishes:

- `arm-linux-gnueabi` for base AAPCS/soft-float binaries;
- `arm-linux-gnueabihf` for binaries using VFP hard-float calling conventions;
- an explicit undetermined result when the extracted evidence is mixed or incomplete.

The Debian 13 `build/Dockerfile` installs both toolchains, SquashFS tooling, binutils, Python, and the existing tests. It is an analysis/non-flashable environment only; it does not install services on the host or generate a firmware image.
