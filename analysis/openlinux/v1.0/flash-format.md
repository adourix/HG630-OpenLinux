# V1.0 OEM flash-format assessment

Classification: VERIFIED where stated; UNKNOWN/BLOCKED where stated. This is
static, read-only analysis of the preserved package and recovered binaries.

## Verified package structure

- Original SHA256: `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`
- Package size: `7,563,600` bytes.
- Metadata/header inspection range: `0x000000..0x000600`; `board_id=1212`.
- SquashFS 4.0 begins at `0x305cf`, uses XZ, 1 MiB blocks, and occupies
  `5,930,917` bytes through `0x5d8573`.
- Legacy U-Boot ARM uImage begins at `0x5d85cf`; its payload is LZMA,
  `1,434,088` bytes, and ends at `0x7368b7`.
- Embedded uImage header CRC and payload CRC are VERIFIED. Header load and
  entry addresses are both `0x81208000`; name is `Linux-2.6.30`.
- There are a 91-byte gap before the uImage and trailing package bytes after
  the payload. Their semantics are UNKNOWN.

## Metadata semantics

`main_offset/main_size` and `slave_offset/slave_size` records occur under
multiple section IDs. Some extents reach `0xfd0000`, beyond the package end.
Therefore they are not proven file offsets and are not treated as physical
MTD addresses. Their section meaning, active/slave behavior, and component
selection are UNKNOWN.

## Update mechanism result

The updater and `libbhalapi.so` expose generic, area, configuration,
bootloader, and logical MTD operations. Static evidence does not resolve the
branch that maps a package section to an MTD index or prove a RootFS-only path.
The OEM update route is BLOCKED until that mapping and the authentication
contract are established. No MTD device was opened and no updater was run.
