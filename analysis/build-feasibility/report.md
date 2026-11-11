# Custom firmware build feasibility

## Outcome

The integrated builder produced an experimental same-layout image:

`/home/ayad/build-output/custom-build/firmware-run-001/HG630V2-experimental.bin`

SHA-256: `349d448549c468145df58176c4e787d5a192b5dbde6135496fa8e4027f84fcc4`

This image is **EXPERIMENTAL_NON_FLASHABLE**. OEM signature and outer-container integrity requirements remain unresolved. No router or MTD device was accessed.

## Assembly invariants

### VERIFIED

- Original firmware input SHA-256 is `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`.
- Original SquashFS is version 4.0 at offset `0x305cf`; original uImage is at `0x5d85cf`.
- The run-007 custom RootFS is independently validated by SquashFS superblock inspection and complete extraction.
- The custom RootFS is exactly `5,931,008` bytes, matching the reserved byte span from the original SquashFS offset to the original uImage offset. This permits replacement without moving the preserved kernel.
- The metadata prefix, unknown header bytes, original uImage, and package suffix are copied unchanged.
- The original uImage remains `Linux-2.6.30`, ARM, LZMA-compressed, load/entry `0x81208000`, payload size `1,434,088` bytes.
- Preserved uImage header CRC32 and payload CRC32 both validate in the assembled output.
- The original uImage byte hash is preserved: `13a3432e8d2bbce07c5d0a49e157d77c3c183cad445dfb16be3c3bcaaa75ebc7`.

## Existing component integration

- RootFS builder: VERIFIED. It preserves special files, links, ownership, modes, timestamps, vendor libraries, kernel modules, and boot scripts; run-007 was previously compared against the source with only the intentional overlay difference.
- RootFS validator: VERIFIED for structure and extraction. It does not establish DSL or hardware behavior.
- Firmware inspector/validator: VERIFIED for embedded SquashFS and uImage structure/CRC; OEM metadata ranges remain semantically unresolved.
- Kernel extraction: VERIFIED as a byte-preserving carve of the original uImage and LZMA payload. Kernel source/config, boot arguments, and runtime mount behavior are not available from this host-side evidence.
- Flash layout and MTD analysis: VERIFIED as static evidence only; no physical partition map or section-to-MTD assignment is established.

## Validation levels

| Level | Status | Evidence |
|---|---|---|
| RootFS build validated | VERIFIED | run-007 SquashFS build and full extraction |
| Kernel structure validated | VERIFIED | preserved uImage header/payload CRC32 and byte hash |
| Firmware container structure validated | VERIFIED | same offsets, embedded SquashFS, preserved uImage, unchanged metadata/suffix |
| OEM update acceptance validated | UNKNOWN | signature and outer integrity contract unresolved |
| Kernel boot validated | UNKNOWN | no QEMU-compatible board model or boot test completed |
| Actual HG630 V2 hardware boot validated | BLOCKED | hardware access and flashing are out of scope |

## Requirements still unresolved

- OEM signature algorithm details: key size/source, signature encoding, padding, signed byte range, and failure policy.
- OEM outer checksum/authentication and exact metadata semantics.
- Exact mapping of metadata section IDs to MTD devices and protection rules.
- Kernel boot arguments, root device, mount parameters, and emulation viability.

The builder therefore rejects size-changing replacements that would move unknown package structures and does not claim OEM update compatibility. The generated image is evidence of reproducible assembly and structural validation only.
