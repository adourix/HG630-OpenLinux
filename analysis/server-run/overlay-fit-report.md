# Complete OpenLinux overlay fit report

Status: `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`.

## Result

A complete overlay candidate now fits without deleting features, changing OEM files, changing OEM libraries/kernel/drivers, enabling BCJ, or changing startup order. The winning profile uses SquashFS-tools 4.2, ordinary XZ, 1 MiB blocks, fragments, duplicate checking, no xattrs, and a deterministic `-sort` file that assigns all four overlay files priority `100`.

The candidate has `5,914,229` internal bytes, leaving `16,779` bytes inside the `5,931,008`-byte reserved span. Its padded outer file is `5,914,624` bytes. SHA-256 is `1f0760422f5f94b5da8ad7670725e1c2fc6fe0134d6649b96e5f2a2dbca2515e`; an independent repeat produced the same hash after setting the SquashFS 4.0 superblock timestamp to the OEM value `1490771239` because 4.2 predates `-mkfs-time`.

Exact command:

```text
mksquashfs STAGE ROOTFS.SQUASHFS -noappend -comp xz -no-xattrs -b 1M -processors 1 -no-progress -sort SORT_FILE
```

`SORT_FILE` is:

```text
etc/init.d/openlinux 100
etc/openlinux/openlinux.conf 100
usr/libexec/openlinux-services/network 100
usr/sbin/openlinuxctl 100
```

After creation, the reproducible 4.2 compatibility step sets superblock bytes 8–11 to little-endian `1490771239`; the matrix runner documents and performs this because 4.2 has no `-mkfs-time` option. This changes only the SquashFS creation timestamp and does not alter compressed data or the filesystem layout.

## Matrix

| variant | internal bytes | result |
|---|---:|---|
| 4.2 complete overlay baseline | 5,935,161 | over by 4,153 |
| XZ dictionary 75% | 5,937,063 | over |
| XZ dictionary 50% | 5,946,143 | over |
| no inode compression | 5,988,918 | over |
| no fragment compression | 14,167,193 | over |
| no data compression | 7,671,491 | over |
| no fragments | 6,429,053 | over and incompatible with OEM fragment profile |
| always-use-fragments | 5,937,466 | over and not OEM-equivalent |
| no duplicate checking | 5,936,869 | over and not OEM-equivalent |
| sort overlay first | 5,914,501 | fits |
| sort overlay last | 5,914,229 | fits; winner |
| sort controller first | 5,914,533 | fits |
| sort controller last | 5,914,473 | fits |

The four ordering variants all retained the same 1,264 entries and 14 fragments. `-sort` changes filesystem ordering and compressed packing, not path semantics. It remains compatible with the observed SquashFS 4.0 format and original XZ flags; no alternate filter is used.

## Required validation

The winner was extracted and compared against the staged complete overlay: no missing, extra, or changed entries. Comparing it against the OEM RootFS with the four overlay files and their new parent directories explicitly allowed found no missing OEM paths, extra OEM paths, or changed OEM metadata. Directory timestamp restoration is now enforced by `tools/build_rootfs.py`, and the validator records integer mtime values.

The original and candidate OpenLinux scripts produced equal normalized behavior across status, invalid configuration, DHCP generation, network dry-run, boot logging, and network apply-requested cases. Removing only full-line comments and blank lines saved 533 source bytes and produced equal behavior, but the readable original sources were retained because ordering alone provides ample space.

The preserved OEM BusyBox 1.9.1 was executed under `qemu-arm`; its own help output listed `awk`, `mkdir`, `echo`, `kill`, `sleep`, `cp`, `test`, `rm`, `sh`, `ifconfig`, `udhcpc`, and `cat`. `awk`, shell pipelines, `command`, and `printf` behavior were directly exercised. This is userspace emulation evidence only, not router or kernel validation.

No suitable OEM location was found that would host the files without adding the same data or changing vendor semantics. RAM/network loading remains an architectural fallback, not a reliable boot path: it would require an already-working post-boot transport and cannot be assumed to provide persistent or early-boot availability. The fitting sorted SquashFS candidate is therefore the preferred research result, while remaining non-flashable and unvalidated on hardware.
