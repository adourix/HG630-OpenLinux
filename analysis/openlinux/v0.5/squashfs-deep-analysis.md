# SquashFS deep analysis

## Binary fields

The original carved filesystem has magic `hsqs`, version 4.0, little-endian
fields, XZ compression ID 4, 1 MiB block size, 1 MiB block log, 1,257 inodes,
14 fragments, seven IDs, raw flags 704, and 5,930,917 bytes used. It has no
stored xattrs.

V0.4 has the same magic/version/endianness/compression ID/block size and 1,265
inodes, 14 fragments, seven IDs, no stored xattrs, and raw flags 1216. Its
SquashFS bytes-used field is 5,780,643; the file is padded to 5,931,008 bytes.
`unsquashfs -s` reports `Filters selected: arm`, proving that V0.4 uses the ARM
XZ BCJ filter. The original reports no XZ filter.

## Kernel comparison

The decompressed original kernel contains `squashfs_xz_init`, `xz_dec_init`,
`xz_dec_run`, XZ error paths, and the SquashFS 4.0 version string. This is direct
static evidence for ordinary XZ SquashFS support. It does not prove that the
kernel's XZ decoder accepts the ARM BCJ filter; no embedded config or filter
registration evidence was recovered.

## Recommendation

**VERIFIED-compatible recommendation:** use SquashFS 4.0, little-endian, XZ,
1 MiB blocks, no BCJ filter, no xattrs, and preserve the existing kernel offset.

**UNKNOWN/BLOCKED constraint:** the no-BCJ image may not fit the 5,931,008-byte
reserved span after userspace changes. Padding cannot solve an over-size
filesystem. BCJ makes the image fit but is not proven consumable by the kernel.
Do not silently change the production default or call a BCJ image hardware
compatible.
