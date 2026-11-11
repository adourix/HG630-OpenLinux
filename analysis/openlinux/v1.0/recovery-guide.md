# V1.0 recovery and installation status

## Status: BLOCKED

No installation instructions are provided because the OEM acceptance contract
is not established. In particular, there is no verified signature, outer
checksum, section-to-MTD mapping, RootFS-only update branch, or exact-board
recovery procedure.

The only safe current action is offline inspection. Preserve the original
firmware and use a passive UART discovery session only after identifying a
safe ground and voltage-compatible adapter. Do not interrupt boot, transmit
commands, write MTD, alter bootloader environment, or deploy the experimental
candidate.

A future recovery guide requires direct evidence for the board revision,
bootloader prompt, signed OEM restore image acceptance, and a known-good
recovery procedure. TFTP, reset-button recovery, dual-bank behavior, and web
recovery are all UNKNOWN rather than assumed.
