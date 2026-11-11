# V1.0 flashability checklist

| Requirement | Status | Evidence |
|---|---|---|
| Original kernel preserved byte-for-byte | VERIFIED | uImage SHA256 and CRC comparison |
| RootFS structurally valid | VERIFIED | SquashFS parse and extraction |
| ARMv7/EABI userspace | PARTIALLY VERIFIED | static inventories and ARM user-mode tests |
| Original kernel root-MTD/mount parameters | UNKNOWN | no bootloader/hardware evidence |
| SquashFS ARM BCJ support in target kernel | UNKNOWN | generic XZ symbols only |
| Metadata main/slave semantics | UNKNOWN | extents exceed package size |
| Section-to-MTD mapping | UNKNOWN | static callers unresolved |
| RootFS-only OEM update path | UNKNOWN | no proven selection branch |
| OEM outer checksum | UNKNOWN | not identified |
| OEM signature algorithm/coverage/key | BLOCKED | no complete call/data flow or key |
| Legitimate signing credential | BLOCKED | unavailable |
| Recovery path | UNKNOWN | no board-specific evidence |
| Actual HG630 V2 boot | BLOCKED | no hardware access permitted |

**Decision: BLOCKED.** No artifact is labeled `FLASHABLE`.
