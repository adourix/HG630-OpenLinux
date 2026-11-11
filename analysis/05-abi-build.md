# Report 5 — ARM ABI and isolated build design

The package-level uImage evidence records ARM architecture ID 2. The corrected server run records 227 little-endian ARM ELF files. All 227 have raw `e_flags=0x05000002` (`Version5 EABI`) and valid `aeabi` attribute sections, but none has `Tag_ABI_VFP_args` or an explicit hard/soft float flag. The result is therefore still inconclusive; `e_flags=0x05000002` alone is not a calling-convention decision.

The corrected `tools/detect_abi.py` parses each ELF header directly, records architecture and raw `e_flags`, decodes `.ARM.attributes` using the AEABI subsection tag and length boundaries, and records dynamic metadata separately:

- representative executables use `/lib/ld-uClibc.so.0` and list their `DT_NEEDED` libraries;
- `libtriapi.so` needs `libc.so.0` and has no interpreter, as expected for a shared library;
- the uClibc shared object provides filename evidence for version `0.9.32.1-git`.

The detector distinguishes:

- `arm-linux-gnueabi` for base AAPCS/soft-float binaries;
- `arm-linux-gnueabihf` for binaries using VFP hard-float calling conventions;
- an explicit undetermined result when the extracted evidence is mixed, absent, or incomplete. It never treats an ARM architecture ID alone as hard- or soft-float evidence.

The Debian 13 `build/Dockerfile` installs both toolchains, SquashFS tooling, binutils, Python, and the existing tests. It is an analysis/non-flashable environment only; it does not install services on the host or generate a firmware image.
