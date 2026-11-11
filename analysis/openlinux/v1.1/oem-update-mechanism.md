# V1.1 OEM update mechanism

## VERIFIED static evidence

- `upg` references board/version/firmware checks, `ATP_SEC_*` security wrappers,
  generic/area/configuration/bootloader update paths, and flash error strings.
- `libbhalapi.so` supports logical MTD indices 0 through 15 and erase/read/write
  helpers using `/dev/mtd*` paths.
- `libmsgapi.so` imports RSA, SHA-256, and MD5 primitives.
- The original package's embedded uImage CRCs validate.

## UNKNOWN / BLOCKED

The actual parser branch connecting metadata section IDs to update modes and
MTD targets remains unresolved. Main/slave records do not prove dual-bank
booting or rollback. RootFS-only acceptance, full-image acceptance, protected
regions, erase/write ordering, outer checksum coverage, signature coverage,
key source, and failure recovery are not proven.

No legitimate signing credential or documented unsigned OEM path was found.
The OEM route is BLOCKED for a custom package; no authentication bypass is
attempted.
