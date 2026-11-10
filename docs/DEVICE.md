# Device profile

## Owner-reported identification

| Field | Value |
|---|---|
| Product | Huawei HG630 V2 |
| Hardware revision | VER.B |
| Firmware version | V100R001C298B010 |
| Update package | HG630V2-12V100R001.bin |
| Package string | `board_id=1212` |

## Caveats

- A model name does not uniquely identify PCB layout.
- VER.B is the router UI hardware revision, not necessarily a PCB silkscreen revision.
- The firmware package `board_id=1212` is not necessarily the CFE board ID.
- Do not assume components from HG630b, HG630-52 or related Huawei models are interchangeable.

## Candidate platform information

Publicly documented HG630 variants are associated with Broadcom BCM63168-family hardware and BCM6362-family wireless. These are research leads, not verified specifications for this exact VER.B unit. Confirm chip markings or trusted boot logs before generating any device-specific image.

## Unconfirmed for this unit

- SoC and stepping
- RAM size/layout
- Flash part, capacity and erase geometry
- Bootloader version
- CFE board ID
- DSL PHY/AFE
- Wi-Fi chip and calibration location
