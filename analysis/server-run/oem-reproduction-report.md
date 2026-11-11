# OEM RootFS reproduction report

Status: `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`.

The original firmware and carved RootFS were verified before the experiment. The firmware SHA-256 is `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`; the carved SquashFS SHA-256 is `68dcfa5c1b53bd09fcd00ea52bdcd3fb1da25d53446915cd6fd2f3aba22bb534`. No original input, kernel, driver, library, or firmware package was modified.

## Method

Historical SquashFS-tools 4.2, 4.3, and 4.4 were downloaded from their SourceForge archives; 4.6.1 was built from the upstream tagged source. Each was built in an isolated temporary directory using GCC 14.2.0 and a locally built static XZ Utils 5.2.5 liblzma. The reproducible build helper is `tools/experiments/build_historical_squashfs.sh`; the matrix runner is `tools/experiments/oem_reproduction.py`.

The common command was:

```text
mksquashfs SOURCE IMAGE -noappend -comp xz -no-xattrs -b 1M -processors 1 -no-progress
```

For versions supporting it, the normalized variant added `-all-time 1490771239 -mkfs-time 1490771239`. The original profile is SquashFS 4.0, XZ, 1 MiB blocks, fragments enabled, no xattrs, duplicate checking enabled, and no demonstrated BCJ filter.

## Results

| processor | mode | internal bytes_used | difference from OEM | extracted metadata/content |
|---|---:|---:|---:|---|
| OEM | — | 5,930,917 | 0 | reference |
| 4.2 | native | 5,930,941 | +24 | exact match |
| 4.3 | native | 5,929,517 | −1,400 | exact match |
| 4.4 | native | 5,929,517 | −1,400 | exact match |
| 4.4 | normalized | 5,929,345 | −1,572 | exact match |
| 4.6.1 | native | 5,929,517 | −1,400 | exact match |
| 4.6.1 | normalized | 5,929,345 | −1,572 | exact match |

Every rebuilt image had 1,257 inodes and 14 fragments and compared equal to the extracted OEM RootFS for path, type, mode, UID/GID, regular-file hash/size, symlink target, device numbers, and timestamps. None was byte-identical to the OEM image. The closest size result is 4.2 native, but it is still 24 bytes larger internally and therefore is not an OEM reproduction.

The complete overlay experiment measured 5,933,497 internal bytes, 2,489 bytes over the 5,931,008-byte reserved span. Individual measured contributions were +500 for `etc/init.d/openlinux`, +272 for `etc/openlinux/openlinux.conf`, +272 for the network service script, and +3,120 for `usr/sbin/openlinuxctl`. These deltas interact; they are not additive. The controller remains the dominant contributor, and removing it is not an approved feature tradeoff.

## Interpretation

The evidence supports ordinary XZ as the compatibility-preserving choice, but it does not identify the OEM mksquashfs version or complete encoding recipe. Timestamp normalization changes the result but does not close the gap. The exact XZ encoder implementation/settings, traversal/order details, metadata packing behavior, and target-kernel filter registration remain unresolved. Host extraction is not kernel mount, boot, updater acceptance, or hardware validation.

The technically justified next action is to obtain vendor build provenance or actual Huawei kernel source/configuration and, specifically, prove any alternate XZ filter support before testing it. Preserve the OEM kernel and all vendor components; do not use BCJ or delete required OpenLinux functionality based on host-side size alone.
