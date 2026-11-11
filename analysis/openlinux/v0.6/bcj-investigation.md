# ARM BCJ and SquashFS investigation

## Controlled image tests

Two small SquashFS 4.0 images were created from the same stage with deterministic
timestamps and 1 MiB blocks:

| Image | XZ options | `bytes_used` | File size | Result |
|---|---|---:|---:|---|
| `xz.squashfs` | XZ, no filter | 128,528 | 131,072 | host extraction VERIFIED |
| `xz-arm-bcj.squashfs` | XZ + ARM BCJ | 123,014 | 126,976 | host extraction VERIFIED |

`unsquashfs -s` reports `Filters selected: arm` only for the second image. The
extracted ARM BusyBox hashes are identical (`7695b0427fa6c8d24d9181451ae214e54771bba7bd85f00d836c8c872fc36951`). This proves that the build tool writes distinct XZ compressor metadata and that development-host extraction supports both forms.

## Original and V0.4 comparison

The original filesystem is SquashFS 4.0, XZ, 1 MiB blocks, raw flags 704, and
has no reported filter. V0.4 is SquashFS 4.0, XZ, 1 MiB blocks, raw flags 1216,
and reports the ARM filter. V0.4's `bytes_used` is 5,780,643 and its file is
zero-padded to the 5,931,008-byte fixed span.

## Kernel evidence

The decompressed original kernel contains `squashfs_xz_init`, `xz_dec_init`,
`xz_dec_run`, XZ error strings, and SquashFS 4.0 strings. These are direct
evidence for generic XZ decompression and the original filesystem format.

No kernel `.config`, `IKCFG` payload, `CONFIG_XZ_DEC_ARM`, BCJ registration, or
`Filters selected` equivalent was recovered. The kernel strings do not expose a
direct ARM BCJ decoder symbol. Therefore:

- ordinary XZ support: **VERIFIED STATIC**;
- ARM BCJ support in the target kernel: **UNKNOWN**;
- V0.4 hardware mount compatibility: **BLOCKED/UNKNOWN**.

The V0.4 BCJ image is not reclassified as compatible merely because modern
`unsquashfs` extracts it.

## Build recommendation

Keep `--bcj arm` explicit and non-default. The only configuration directly
matched by both original filesystem and kernel evidence is ordinary XZ, 1 MiB
blocks, SquashFS 4.0, no xattrs. That configuration may exceed the fixed OEM
component span after OpenLinux additions, so it is a compatibility candidate
only if it fits; no misleading candidate was created in this milestone.
