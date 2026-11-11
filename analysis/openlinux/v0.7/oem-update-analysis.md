# V0.7 OEM update architecture analysis

Classification: VERIFIED, PARTIALLY VERIFIED, UNKNOWN, or BLOCKED. Analysis is
static and read-only; no OEM executable was run and no MTD device was opened.

## Package contents

**VERIFIED:** The original package is 7,563,600 bytes with:

- metadata/header text beginning near `0x314`, including `board_id=1212`;
- a SquashFS 4.0/XZ filesystem at `0x305cf`, `5,930,917` bytes used;
- a legacy U-Boot ARM uImage at `0x5d85cf`, with a 1,434,088-byte LZMA payload;
- a 91-byte gap between the filesystem end and uImage start;
- trailing package bytes after the uImage payload.

The embedded uImage header CRC and payload CRC are valid. These are component
integrity checks, not proof of the OEM package authentication contract.

**VERIFIED:** The same metadata and component ordering are present in the V0.4
experimental artifact. Its original kernel bytes and uImage offset were
preserved by `tools/build_firmware.py`.

## Metadata interpretation

**VERIFIED:** The metadata contains repeated `main_offset/main_size` and
`slave_offset/slave_size` records under section identifiers including `20001`,
`20002`, `20003`, `20005`, `20011`, `20100`, `20101`, and `30002`.

**VERIFIED:** The nonzero records form an apparent address range ending at
`0xfd0000`, while the update package ends at `0x736950`. Therefore these values
cannot all be direct offsets into the update file.

**UNKNOWN:** The values may describe a device address space, update-area
coordinates, or another vendor abstraction. The parser does not establish
physical flash addresses, partition boundaries, or payload selection semantics.

**UNKNOWN:** `main` and `slave` names alone do not prove dual-bank booting,
rollback, or recovery behavior. No direct branch from a section record to a
specific MTD number has been recovered.

## Upgrade implementation evidence

**VERIFIED:** `upg` directly references security wrappers including
`ATP_SEC_VerifyData`, `ATP_SEC_CreateSignatureContext`, and
`ATP_SEC_KM_GetKey`. It also references separate generic, configuration,
bootloader, area, and partition flash APIs.

**VERIFIED:** `libbhalapi.so` has an `ATP_MTD_Getfd` path that bounds a logical
index at 15 and constructs static `/dev/mtd0` through `/dev/mtd15` names.
Erase uses `MEMERASE`-related code and separate read/write helpers exist.

**PARTIALLY VERIFIED:** The updater can support multiple update modes and
logical MTD selection. The caller arguments that connect metadata section IDs
to those modes are not fully resolved.

**UNKNOWN:** Whether kernel and RootFS are written together, whether RootFS can
be selected independently, which areas are protected, and the exact erase/write
ordering for this package.

## Integrity and authentication

**VERIFIED:** The embedded uImage CRC32 values validate. The original and V0.4
SquashFS superblocks parse as version 4.0, XZ, 1 MiB blocks.

**INFERRED:** RSA and SHA-256 are candidates for the OEM security path because
`libmsgapi.so` imports CyaSSL RSA and SHA-256 primitives alongside the security
wrappers.

**UNKNOWN/BLOCKED:** RSA modulus size, padding, signature encoding, signed byte
range, public-key source, outer checksum, and failure policy. A valid OEM update
cannot be generated or accepted on the current evidence. No signature check is
bypassed.
