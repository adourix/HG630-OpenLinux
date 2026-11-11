# OEM MTD selection and flash-write path

## VERIFIED

- `ATP_MTD_Getfd` at `0x3ce8` is 480 bytes and compares the logical index against `15` before an ARM jump-table dispatch.
- Static paths include `/dev/mtd1`, `/dev/mtd0`, `/dev/mtd2`, `/dev/mtd3`, `/dev/mtd4`, `/dev/mtd5`, `/dev/mtd6`, `/dev/mtd7`, `/dev/mtd8`, `/dev/mtd9`, `/dev/mtd10`, `/dev/mtd11`, `/dev/mtd12`, `/dev/mtd13`, `/dev/mtd14`, `/dev/mtd15`.
- The library contains separate MTD get-fd, erase, read, write, area-write, generic-upgrade, configuration-upgrade, bootloader-upgrade, and partition-write functions.
- `upg` directly calls the recorded MTD/flash APIs at the addresses in the JSON report.

## Call-path evidence

- `ATP_MTD_WriteBufToOffset_Upg` (`0x3b8c`, `348` bytes): `0x3bc0`, `0x3bd0`, `0x3bf4`, `0x3c04`, `0x3c18`, `0x3c4c`, `0x3c58`, `0x3c68`, `0x3c74`, `0x3c90`.
- `ATP_MTD_Getfd` (`0x3ce8`, `480` bytes): `0x3e20`, `0x3e40`, `0x3e50`.
- `ATP_MTD_ReadBuffromOffset` (`0x3a70`, `284` bytes): `0x3aa4`, `0x3ab4`, `0x3ad8`, `0x3ae8`, `0x3afc`, `0x3b10`, `0x3b1c`, `0x3b38`.
- `ATP_MTD_WriteBufToOffset` (`0x4360`, `24` bytes): `0x436c`.
- `ATP_MTD_Erase` (`0x4378`, `136` bytes): `0x4394`, `0x43dc`.
- `FomWriteFlashAreaByHead` (`0x37d0`, `220` bytes): `0x383c`, `0x386c`.
- `UPG_FlashPartWrite` (`0x9d38`, `316` bytes): `0x9d50`, `0x9d58`, `0x9d7c`, `0x9d8c`, `0x9d9c`, `0x9dac`, `0x9db8`, `0x9dd0`, `0x9de4`, `0x9dec`, `0x9e00`, `0x9e18`, `0x9e2c`, `0x9e3c`, `0x9e44`, `0x9e4c`.
- `ATP_FLASH_UpgradeBootloader` (`0x6a34`, `256` bytes): `0x6a64`, `0x6a88`, `0x6a98`, `0x6ab8`, `0x6ac4`, `0x6ad8`, `0x6adc`, `0x6af4`, `0x6b08`.
- `ATP_FLASH_WriteArea` (`0x7958`, `436` bytes): `0x7984`, `0x7988`, `0x79ac`, `0x79bc`, `0x79c4`, `0x79d8`, `0x79ec`, `0x7a00`, `0x7a14`, `0x7a38`, `0x7a4c`, `0x7a68`, `0x7a70`, `0x7a7c`, `0x7a9c`, `0x7ab4`, `0x7ac4`, `0x7ad4`.
- `ATP_FLASH_UpgradeCfg` (`0x6968`, `204` bytes): `0x6998`, `0x69bc`, `0x69dc`, `0x69e8`, `0x69fc`, `0x6a10`.
- `ATP_FLASH_Upgrade` (`0x6b34`, `880` bytes): `0x6b68`, `0x6b8c`, `0x6ba0`, `0x6bb0`, `0x6bbc`, `0x6bd4`, `0x6bf4`, `0x6c08`, `0x6c2c`, `0x6c34`, `0x6c58`, `0x6c64`, `0x6c74`, `0x6cb0`, `0x6cc4`, `0x6cd0`, `0x6cec`, `0x6d00`, `0x6d0c`, `0x6d40`, `0x6d50`, `0x6d70`, `0x6d84`, `0x6da4`, `0x6dd8`, `0x6dec`, `0x6df8`, `0x6dfc`, `0x6e20`, `0x6e38`, `0x6e44`.

## INFERRED

- INFERRED: callers pass a logical MTD index to ATP_MTD_Getfd; this library resolves it to a static /dev/mtdN table.
- INFERRED: erase and write are separate operations, with error returns checked by callers; higher-level ATP_FLASH_Upgrade selects among paths using arguments and runtime state.

## UNKNOWN / BLOCKED

- UNKNOWN: no exact section-ID-to-MTD mapping.
- UNKNOWN: /dev/caldata -> /dev/mtd9 is known, but no traced upgrade branch proves it is excluded.
- UNKNOWN: a distinct ATP_FLASH_UpgradeBootloader path exists; its eligibility and target are unresolved.
- UNKNOWN: both full upgrade and area/partition write helpers exist; package selection logic is unresolved.
- UNKNOWN: MEMERASE is used, but exact erase-size source for each update path is not resolved.

No host MTD device was accessed and no flash operation was executed.
