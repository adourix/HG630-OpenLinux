# Engineering work plan

## Milestone 1 — Static analysis
- [x] Record firmware SHA-256 and embedded structure offsets.
- [x] Add read-only uImage/SquashFS inspector.
- [x] Add parser unit tests.
- [ ] Extract SquashFS in an isolated host environment.
- [ ] Inventory ELF files, libraries, kernel modules and init scripts.
- [ ] Identify DSL module, firmware image and control daemons.

## Milestone 2 — Board identification
- [ ] Match exact OEM GPL source release.
- [ ] Confirm SoC, Wi-Fi and DSL chipsets for VER.B.
- [ ] Confirm CFE board ID, RAM and flash geometry.
- [ ] Map calibration/NVRAM/bootloader protected regions.

## Milestone 3 — Architecture decision
- [ ] Compare OpenWrt bmips support with OEM BSP.
- [ ] Establish DSL driver kernel ABI and licensing.
- [ ] Decide upstream kernel port vs vendor-derived Linux.
- [ ] Build reproducible host tools and non-flashable artifacts.

## Milestone 4 — Device validation
No flash operation until recovery is independently verified and every gate in RECOVERY.md is satisfied. DSL synchronization and WAN stability are mandatory acceptance criteria.
