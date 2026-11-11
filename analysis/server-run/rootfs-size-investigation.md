# HG630 V2 RootFS size and compatibility investigation

## Findings (2026-11-10)

### VERIFIED — constraint and size accounting

The original package places SquashFS at `0x305cf` (198,095) and the preserved Linux 2.6.30 uImage at `0x5d85cf` (6,129,103). Their difference reserves **5,931,008 bytes**. Original SquashFS `bytes_used` and carved-file length are 5,930,917, leaving 91 bytes before the kernel. The firmware SHA-256 is `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`; carved RootFS SHA-256 is `68dcfa5c1b53bd09fcd00ea52bdcd3fb1da25d53446915cd6fd2f3aba22bb534`.

| Image | Internal `bytes_used` | File size | Inodes / fragments | SHA-256 |
|---|---:|---:|---:|---|
| OEM original | 5,930,917 | 5,930,917 | 1,257 / 14 | `68dcfa5c…` |
| Rebuilt baseline, normalized timestamps | 5,929,345 (reported) | 5,931,008 | 1,257 / 14 | run-specific |
| Integrated overlay (100% dictionary) | 5,933,493 | 5,935,104 | 1,264 / 14 | `95731be5…` |
| Preserved timestamps, baseline diagnostic | 5,929,517 | 5,931,008 | 1,257 / 14 | `9d5b9940…` |
| Integrated without `openlinuxctl` | 5,930,417 | 5,931,008 | 1,263 / 14 | `d0e082e8…` |

Outer file size is rounded/padded by mksquashfs to a 4 KiB boundary; it is distinct from superblock `bytes_used`. A 5,931,008-byte file can still have an internal filesystem below the limit. Conversely, an image with internal bytes_used above 5,931,008 cannot fit even before outer alignment. The exact dictionary run has internal size 5,933,493 and file size 5,935,104, exceeding the span by 2,485 and 4,096 bytes respectively.

### VERIFIED — ABI

`analysis/server-run/abi.json` covers 227 ELF files: all are ELF32 ARM, little endian, EABI version 5 (`e_flags=0x05000002` for 184; 43 are `0x05000000`). The ELF attributes identify ARMv4T/ARM9 class instructions (for example BusyBox says ARMv4T); target kernel/modules identify ARMv7. These are not contradictory: the userspace code targets an older compatible ISA. The detector has no soft/hard float calling-convention evidence for any ELF, so the aggregate is correctly ambiguous; do not infer hard-float. 121 ELF entries use `/lib/ld-uClibc.so.0`, 18 use `ld-uClibc.so.0`, 141 are identified as uClibc, and 86 are static or otherwise lack libc evidence. OEM libc symlinks resolve to `libuClibc-0.9.32.1-git.so`; the interpreter similarly resolves to `ld-uClibc-0.9.32.1-git.so`. Exact toolchain ABI should be preserved; do not replace OEM libc or linker.

The four overlay files are POSIX shell/text, not ELF binaries, so add no ELF interpreter/libc dependency. They rely on BusyBox shell/awk and commands already audited in `analysis/openlinux/v0.4/compatibility-audit.json`. They add 13,136 source bytes and seven inode entries when parent directories are included. `openlinuxctl` is the largest at 10,951 bytes; no binary or obvious redundant generated payload exists. The network script deliberately only reports dry-run status. No file is individually removable as a safe optimization without changing the requested feature set.

### VERIFIED — source of size growth

One-file-at-a-time builds on the same normalized baseline yielded internal bytes_used: config 5,929,617 (+272), init hook 5,929,845 (+500), controller 5,932,465 (+3,120), network script 5,929,617 (+272). The combined set without the controller is 5,930,417 (+1,072), six new inodes; full integration adds seven inodes and reaches 5,933,493 (+4,148). These deltas are not additive: SquashFS file packing, shared tail fragments, directory/inode metadata and XZ stream boundaries interact. The controller is the dominant measured contributor. Removing it alone is insufficient: the remaining overlay still exceeds the OEM internal bytes_used by 500 bytes, and its aligned file reaches the span exactly, leaving no room for any additional data.

The validator report for `no-ctl.squashfs` shows no missing or changed OEM paths and all four intentional additions, but `match=false` because newly created parent directories `etc/openlinux` and `usr/libexec` are reported as extra directory entries. This is a validation-report categorization issue, not an observed OEM file difference. Full extraction succeeds; this establishes host SquashFS readability only.

### VERIFIED — compression experiments

Host `mksquashfs` is 4.6.1. OEM and rebuilds share SquashFS 4.0, little endian, XZ compressor ID 4, 1 MiB blocks, 14 fragments, 7 UID/GID IDs, no xattrs, duplicates removed, and no BCJ filter. OEM flags are 704; ordinary-XZ rebuilt images also report 704. The first 30 observed XZ stream headers in each image have identical bytes `fd377a585a0000016922de36`. This verifies matching visible stream-header/dictionary properties, not identical compressor implementation or complete encoder parameters.

The full-stage dictionary matrix, each extracted successfully with host unsquashfs:

| XZ dictionary | Internal bytes_used | File size | Result vs reserved span |
|---|---:|---:|---|
| 100% (default) | 5,933,493 | 5,935,104 | over |
| 75% | 5,935,395 | 5,939,200 | over |
| 50% | 5,944,475 | 5,947,392 | over |
| 25% | 5,982,243 | 5,984,256 | over |

Reducing dictionary size makes this content larger. `-Xcompression-level` is unsupported for XZ by this host tool. Disabling duplicate checking is not a valid optimization: the old no-duplicates experiment grew internal size (5,935,269 vs 5,933,493) and changes SquashFS semantics/flags. The no-BCJ image remains the only format directly matched by evidence. The original decompressed kernel has `squashfs_xz_init`, `xz_dec_init`, and `xz_dec_run` strings, establishing static generic XZ support. Kernel config/source and ARM BCJ registration were not found; ARM BCJ support remains UNKNOWN, so BCJ is not a justified production solution despite prior host-side size wins.

### INFERRED — why exact OEM reproduction is not established

The rebuild retains paths, file types, symlinks, hardlinks, modes and ownership. A pseudo-metadata dump shows the source RootFS preserves original per-entry timestamps, while the baseline builder applies `-all-time 1490771239` to every entry; 1,254 comparable entries differ in timestamp. A separate preserved-time build (no `-all-time`) is internally 5,929,517 bytes, 1,400 below OEM. This shows timestamp normalization changes output, but does not alone explain the OEM-to-rebuild difference. OEM SquashFS timestamps cluster around 1490770xxx and its superblock time is 1490771239. Host build ordering, mksquashfs version, file ordering, compressor encoder behavior, and exact source extraction metadata may also differ. There are 1,257 inodes in both original and baseline, 1,264 integrated; fragments remain 14. No evidence demonstrates that changing mksquashfs order or metadata would produce a smaller, target-compatible image while retaining all OEM semantics.

## Recommendation and blockers

Keep all OEM files and ordinary XZ, and do not adopt BCJ or delete controller functionality to force a fit. Next evidence-led step: recover a matching SquashFS-tools/mksquashfs version or original build recipe, then compare per-file inode timestamps/modes/ownership and file ordering against the OEM filesystem using independent extraction metadata. A candidate must be at most 5,931,008 bytes internally and pass OEM-vs-candidate path/type/content/metadata comparison plus extraction. If that cannot fit, obtain target-kernel source/config proving an alternate XZ filter before testing it. No current integrated ordinary-XZ candidate fits.

**UNKNOWN / BLOCKED:** exact OEM compressor options/version/order, target XZ decoder configuration and ARM BCJ registration, exact EABI float calling convention, runtime hook invocation and actual kernel mount/boot, outer updater authentication, flash mapping and recovery path. Do not change OEM init ordering or DSL/Ethernet startup. Preserve `EXPERIMENTAL_NON_FLASHABLE`; host extraction is not hardware validation or flashability evidence.

## Commands and artifacts

Builds were made only under `/home/ayad/build-output/custom-build/run-investigation-*`; prior runs were not overwritten. Commands used ordinary XZ with `-no-xattrs -b 1M -all-time 1490771239 -mkfs-time 1490771239 -processors 1`; dictionary variants added `-Xdict-size 75%`, `50%`, or `25%`. Images were inspected with `unsquashfs -s`, independently hashed, and fully extracted. Tool versions: mksquashfs/unsquashfs 4.6.1; XZ Utils 5.8.1. No code changes were made, so no new tests were needed; the required suite was run and passed 69/69.
