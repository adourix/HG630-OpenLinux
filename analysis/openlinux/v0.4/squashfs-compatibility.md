# SquashFS compatibility

## Comparison

The original filesystem and V0.3 are both SquashFS 4.0, little-endian, XZ,
with 1 MiB blocks and 14 fragments. The original has no reported XZ filter;
V0.3 reports `Filters selected: arm`, because V0.3 used `mksquashfs -Xbcj arm`
to fit the expanded RootFS into the verified component span.

V0.3 also has 1,265 inodes versus 1,257 in the original and uses different
superblock flags, expected from the added OpenLinux files and XZ options. Both
have seven IDs and no stored xattrs. V0.3's filesystem data ends at byte
5,780,187 and the remaining 150,821 bytes are deterministic padding to the
5,931,008-byte reserved span.

## Kernel evidence

**VERIFIED:** the decompressed vendor kernel contains SquashFS 4.0 strings,
`squashfs_xz_init`, `xz_dec_init`, `xz_dec_run`, and XZ error paths. It also
contains the `lzma` string and the standard error for unsupported compression.
The original XZ filesystem is therefore strongly supported by static kernel
evidence.

**UNKNOWN:** no embedded `IKCFG` marker or readable `.config` was recovered,
and the kernel strings do not prove whether the vendor 2.6.30 SquashFS XZ
decoder accepts the ARM BCJ filter. The observed `squashfs_xz_init` strings
mention dictionary/options handling but do not prove filter support.

## Decision

The ordinary XZ format is **VERIFIED-compatible by matching original evidence**.
V0.3's ARM BCJ filter is **UNKNOWN/BLOCKED** for the target kernel. The build
pipeline keeps BCJ optional rather than making it the default. V0.3/V0.4
experimental images must not be treated as hardware-bootable until a matching
kernel or device validates the filter.
