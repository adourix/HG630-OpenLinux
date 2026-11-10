# Recovery and device safety

## Current status

No recovery method has been verified for the owner's HG630 V2 VER.B unit. No firmware writes are authorized at this stage.

## Do not

- Upload experimental images through Firmware Update.
- Use Factory Restore as recovery from a failed boot.
- Write CFE, bootloader, calibration, NVRAM or unknown partitions.
- Assume a vendor settings backup is a full flash dump.
- Use a firmware for a related model or different PCB revision.

## Required recovery evidence

- Exact CFE version and board identity.
- Verified serial console method and voltage levels, if accessible.
- Verified bootloader recovery procedure for this exact unit.
- Full flash backup procedure with read-back verification.
- Known-good original image and checksums.
- Partition boundaries and protected data regions.
- Tested restore procedure independent of the router's normal web UI.

## Configuration backup

The router's Backup or Restore Settings function produces a configuration backup, not a complete flash dump. Treat it as sensitive; it may contain ISP credentials, Wi-Fi credentials and local network details. Do not commit it.
