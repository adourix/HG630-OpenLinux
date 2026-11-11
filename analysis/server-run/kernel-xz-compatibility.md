# Huawei kernel XZ compatibility

Status: `EXPERIMENTAL_NON_FLASHABLE` / `RESEARCH_ONLY`.

The inspected kernel is the preserved Huawei Linux 2.6.30 ARMv7 uImage payload at `/home/ayad/build-output/boot-validation/run-001/kernel.decompressed`. The evidence collector is `tools/experiments/kernel_xz_inspect.py`; its machine-readable output is the adjacent `kernel-xz-evidence-20261110.json` artifact outside Git.

## Observed RootFS properties

The OEM SquashFS superblock reports version 4.0, compression ID 4 (XZ), 1,048,576-byte blocks, 14 fragments, and 1,257 inodes. A scan found 30 observable XZ stream headers. The first 12-byte XZ stream header is `fd377a585a0000016922de36`; repeated headers establish the visible stream/check-header pattern, not the complete LZMA2 property or stream boundary map.

## Observed kernel evidence

Kernel strings include `squashfs_xz_init`, `xz_dec_init`, `xz_dec_reset`, `xz_dec_run`, and the generic XZ decoder test strings. This verifies that the binary contains generic XZ decoder code and SquashFS XZ glue. It does not prove the accepted dictionary size, vendor decoder modifications, or every compressor option.

The binary also contains strings resembling `tbcj`, but no symbol table, registration path, configuration, or source evidence was recovered that proves ARM BCJ is registered for SquashFS XZ. Therefore ARM BCJ support is `UNKNOWN`, exact dictionary support is `UNKNOWN`, and BCJ remains excluded from the RootFS build experiments.

## Conclusion

Ordinary XZ with no BCJ is the only tested profile directly supported by the observed SquashFS format and generic decoder evidence. No claim is made that a host-generated image will mount or boot on the router. Kernel source/configuration, a controlled target mount test, or authoritative Huawei build evidence is required before changing filters or asserting compatibility.
