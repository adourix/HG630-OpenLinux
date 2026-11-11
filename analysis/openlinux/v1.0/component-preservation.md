# V1.0 component preservation

The experimental candidate was assembled only with the existing same-span
builder. It copied the original package prefix, replaced the reserved RootFS
span, and copied the original uImage and suffix unchanged.

## VERIFIED preservation

- Original firmware SHA256 was pinned before assembly.
- Original uImage bytes are byte-identical in the candidate; preserved uImage
  SHA256 is `13a3432e8d2bbce07c5d0a49e157d77c3c183cad445dfb16be3c3bcaaa75ebc7`.
- uImage header and payload CRCs remain valid.
- Metadata prefix, unknown fields, uImage offset, and suffix are preserved.
- No bootloader, calibration partition, MTD device, or physical router was
  accessed.

## RootFS comparison

The V0.4-derived RootFS has 1,265 extracted entries versus 1,257 in the
original extracted RootFS. The controlled additions are OpenLinux-owned paths
under `etc/init.d/openlinux`, `etc/openlinux`, `usr/libexec/openlinux-services`,
and `usr/sbin/openlinuxctl`; directory metadata changes are expected from the
overlay build. Vendor DSL, network, library, module, init, and calibration
files were not intentionally replaced by the overlay.

This is file-level and host extraction evidence only. Kernel mount and hardware
compatibility remain UNKNOWN because the original kernel's ARM BCJ support and
root-MTD parameters are unresolved.
