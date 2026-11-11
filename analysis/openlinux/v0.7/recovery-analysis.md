# V0.7 recovery and safety analysis

## Artifact evidence

**VERIFIED:** The RootFS contains the web upgrade UI and the `upg` executable.
Static strings mention firmware upgrade, reset controls, and a bootloader
version field.

**UNKNOWN:** A documented TFTP recovery procedure, reset-button recovery mode,
dual-bank fallback, bootloader prompt, or bootloader environment interface.
No bootloader binary, board-specific recovery documentation, or exact-board
serial capture is present in the available artifacts. A `tftp` service entry or
UI string is not sufficient evidence of recovery support.

**UNKNOWN:** Whether the `main`/`slave` metadata records represent active and
backup images. The names do not establish a boot-selection or rollback policy.

## Safe recovery prerequisite

Before any experimental boot attempt, obtain a passive UART boot log and exact
board identification. Record the bootloader name/version, prompt behavior,
RAM/flash detection, kernel command line, MTD table, root mount, and any signed
OEM recovery procedure. Do not interrupt boot or transmit commands during the
first observation session.

Without that evidence, there is no verified no-UART recovery path for this
project. No flash write, MTD access, bootloader modification, or firmware
deployment is authorized.
