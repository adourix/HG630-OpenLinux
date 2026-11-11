# Huawei HG630 V2 OEM updater: static analysis

Date: 2026-11-10. Status: read-only static analysis; no router or flash validation.

## Executive conclusion

**BLOCKED for a legitimate custom OEM update on the evidence available.** The extracted updater contains package-security and flash-writing paths, but static analysis does not establish a supported RootFS-only update contract, the package/signature byte ranges, or a trusted signing credential. No authorized firmware-signing private key was identified. Do not submit the reconstructed image to the OEM updater or describe it as flashable; retain `EXPERIMENTAL_NON_FLASHABLE`.

The evidence supports preserving the vendor Linux 2.6.30 ARM kernel and its driver/userspace startup as the lower-risk research direction. It does not prove a safe runtime injection point or successful device behavior. The existing experimental package is a host-side artifact only.

## Evidence labels

- **VERIFIED**: directly observed in the supplied firmware, extracted files, ELF metadata/symbols/strings, or recorded static disassembly.
- **PARTIALLY VERIFIED**: a relevant mechanism is present, but end-to-end behavior is unresolved.
- **UNKNOWN**: current evidence cannot establish the claim.
- **BLOCKED**: the requested conclusion cannot be supported without unavailable evidence or authorization.

## Exact inputs and binary inventory

Original image: `/home/ayad/firmware-input/HG630V2-12V100R001.bin`, 7,563,600 bytes, SHA-256 `d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222`.

Extracted RootFS: `/home/ayad/build-output/rootfs`.

Experimental image: `/home/ayad/build-output/HG630V2-12V100R001-openlinux-final-experimental.bin`, 7,563,600 bytes, SHA-256 `222cc9cd1aa0406826dd81d5237e1634690564014fcafa4e072451193dce4e3e`. Its status remains `EXPERIMENTAL_NON_FLASHABLE`.

| Inspected file | SHA-256 | ELF / role |
|---|---|---|
| `/home/ayad/build-output/rootfs/bin/upg` | `73ea3d4711d481599e58e5737ab80ce08e032ddd7ca48803063df4dedb6ba385` | ELF32 ARM little-endian ET_EXEC, EABI5, entry `0x9780`, 27,648 bytes |
| `/home/ayad/build-output/rootfs/lib/libbhalapi.so` | `c65abdae2c89df3054b11b3f9465f7639e985f7759ecb327f8258b41541cbcd2` | ELF32 ARM little-endian ET_DYN, EABI5, 51,548 bytes |
| `/home/ayad/build-output/rootfs/lib/libmsgapi.so` | `94afcbb979b50e7737f89055ea930310fa48b6146a19d8a5d815c05be14eb4dc` | ELF32 ARM little-endian ET_DYN, EABI5, 154,868 bytes |
| `/home/ayad/build-output/rootfs/lib/libcyassl.so.5.0.5` | `0fcccd41bfb71eb72c4d84a354f7149e8c4e4937986c79688a25d88f3da83463` | ELF32 ARM vendor crypto library; SONAME `libcyassl.so.5` |
| `/home/ayad/build-output/rootfs/lib/libcfmapi.so` | `e1a5b6b9c7f34ece50a7bccf0e87b960929f1061790b4cf03e5600a36d1c23af` | ELF32 ARM shared library |
| `/home/ayad/build-output/rootfs/lib/liblgplutil.so` | `98d3f6cdc743f07acc02b267a941f74668a8dbe4134242c2df791a44916a7b6a` | ELF32 ARM shared library |
| `/home/ayad/build-output/rootfs/lib/libxmlapi.so` | `0bb2544c7e9f2ec915dded7415894055e6d7ed355c5bb1c40decd914e3405984` | ELF32 ARM shared library |
| `/home/ayad/build-output/rootfs/lib/libhttpapi.so` | `887504abf6f29f58187708a0d0246ff1f10155612c86d7bb3ec7bef0518fdce2` | ELF32 ARM shared library |
| `/home/ayad/build-output/rootfs/lib/libm.so.0` | `14c314d35005b50b7a56d409847e209acdf950570f930c5f5d4d9b2be6e9673d` | ELF32 ARM uClibc math runtime |
| `/home/ayad/build-output/rootfs/lib/libz.so.1` | `dec03433b70a5b899a945e6b62e454cccc1926e369ef7090c3179f79263d375` | ELF32 ARM zlib runtime |
| `/home/ayad/build-output/rootfs/lib/libc.so.0` | `064ea2ba84aef5f650453e9bdbc14d3fcc79c617ce7807f2ee36f05f1644510a` | ELF32 ARM uClibc runtime |

`upg` declares DT_NEEDED entries for `libcyassl.so.5`, `libmsgapi.so`, `libcfmapi.so`, `liblgplutil.so`, `libxmlapi.so`, `libhttpapi.so`, `libbhalapi.so`, `libm.so.0`, `libz.so.1`, and `libc.so.0`. `libbhalapi.so` declares `libc.so.0`; `libmsgapi.so` declares `libgcc_s.so.1`, `libc.so.0`, and `ld-uClibc.so.0`. Dependency names and files are observed; runtime load success is not tested. Relevant exports/imports and the complete recorded call-site data are preserved in the companion JSON and the pre-existing analysis under `analysis/generated/upg-static/`.

### Relevant symbols, imports, and strings

`upg` imports `ATP_SEC_KM_GetKey`, `ATP_SEC_CreateData`, `ATP_SEC_CreateSignatureContext`, `ATP_SEC_VerifyData`, and `ATP_SEC_DeleteContext`; its call sites are `0xc304`, `0xc318`, `0xc33c`, `0xc35c`, and `0xc370`. It also imports `ATP_FLASH_Upgrade`, `ATP_FLASH_UpgradeBootloader`, `ATP_FLASH_UpgradeCfg`, `ATP_FLASH_Write`, `ATP_FLASH_WriteArea`, `ATP_MTD_Getfd`, `ATP_MTD_Erase`, `ATP_MTD_WriteBufToOffset_Upg`, and `BSP_FLASH_UnProtect`.

`libbhalapi.so` exports `ATP_MTD_Getfd` (`0x3ce8`, 480 bytes), `ATP_MTD_WriteBufToOffset_Upg` (`0x3b8c`, 348 bytes), `ATP_MTD_Erase` (`0x4378`, 136 bytes), `FomWriteFlashAreaByHead` (`0x37d0`, 220 bytes), `UPG_FlashPartWrite` (`0x9d38`, 316 bytes), `ATP_FLASH_UpgradeCfg` (`0x6968`, 204 bytes), `ATP_FLASH_UpgradeBootloader` (`0x6a34`, 256 bytes), `ATP_FLASH_Upgrade` (`0x6b34`, 880 bytes), and `ATP_FLASH_WriteArea` (`0x7958`, 436 bytes). These names and function boundaries are static symbol evidence; a function's existence does not prove a caller can select it for an arbitrary package.

`upg` strings include `/var/upg.bin`, `-f` (upgrade from file), `-m` (upgrade image type), `-a` (multicast upgrade), `main_offset`, `main_size`, `slave_offset`, `slave_size`, `Verify head error`, `Verify head ok`, `upgrade big system`, and `ATP_UPG_UpgradeKernel/Image Find single System !`. Strings are not proof of a complete parser or accepted command contract.

## Package parsing and control flow

**VERIFIED:** the original container parser records board ID `1212`, version `HG630V2V100R001C298B010`, a SquashFS 4.0 component at file offset `0x305cf` with 5,930,917 used bytes, and a Linux-2.6.30 ARM uImage at `0x5d85cf` with a 1,434,088-byte payload. Embedded uImage header and data CRC32 validate. The known component IDs are RootFS `1` and kernel `2`; four component records were observed in the prior package analysis.

The metadata has section labels including `20011`, `20003`, `20002`, `20001`, `20100`, `20101`, `20005`, `20004`, and `30002`. Some main/slave ranges fit within the file and several extend past its 7,563,600-byte end. **UNKNOWN:** whether these numbers address package offsets, flash locations, a larger virtual map, or another structure. The metadata parser itself labels their semantics unknown.

**PARTIALLY VERIFIED:** `upg` has file-input, image-type, board/version, security, and flash API references. It calls a security check before/around package update behavior, and failure strings mention header verification and flash erase/write errors. The complete parser control-flow path, package-bound checks, section-ID dispatch, and all writes' ordering are not recovered. Direct ARM-call analysis misses indirect calls and does not constitute full decompilation.

```text
upg
 ├─ package/file and board/version checks [partial; parser branch unresolved]
 ├─ ATP_SEC_KM_GetKey / CreateData / CreateSignatureContext
 │    └─ ATP_SEC_VerifyData (libmsgapi.so: 0x14648, 204 bytes)
 │         └─ ATP_SEC_DigestDataEx -> indirect verifier callback [target unresolved]
 └─ ATP_FLASH_Upgrade / UpgradeCfg / UpgradeBootloader / WriteArea
      └─ libbhalapi.so erase/read/write helpers
           └─ ATP_MTD_Getfd (0x3ce8) -> logical index dispatch 0..15
                └─ static /dev/mtd0 ... /dev/mtd15 paths
```

### RootFS-only and full-package behavior

**UNKNOWN:** no verified RootFS-only supported update path is established. A RootFS component ID and area/partition writing helpers exist, but neither proves that the OEM updater accepts a package containing only component 1 or permits that selection. The evidence does not establish whether a complete firmware package is mandatory. Do not interpret an exported `ATP_FLASH_WriteArea` function or `-m` option as authorization to write RootFS by itself.

## Authentication and integrity

**PARTIALLY VERIFIED:** `upg` directly imports/calls `ATP_SEC_*` wrappers. In `libmsgapi.so`, `ATP_SEC_VerifyData` is at `0x14648` (204 bytes), `ATP_SEC_VerifyDataEx` at `0x14d2c` (172 bytes), and `ATP_SEC_CreateSignatureContext` at `0x14be8` (324 bytes). The verify function has a checked-length path, invokes `ATP_SEC_DigestDataEx`, then makes an indirect context/function-pointer dispatch that static analysis has not resolved.

The crypto import set includes CyaSSL RSA routines (`CyaSSL_RSA_size`, `CyaSSL_RSA_new`, `CyaSSL_RSA_free`) and SHA-256 and MD5 primitives. This supports RSA and SHA-256 as candidates, but does not prove which primitive is used for firmware authentication. RSA padding, digest choice, modulus/signature size, signature encoding, signed byte range, and excluded fields remain **UNKNOWN**. The independently verified uImage CRC32 values are integrity checks for the embedded uImage; they are not an OEM package signature.

The extracted RootFS contains `/etc/root.pem`, `/etc/servercert.pem`, and `/etc/serverkey.pem`, which are also strings in `libmsgapi.so`. Certificate inspection identifies `root.pem` as a self-issued `root.home` certificate and `servercert.pem` as a `mediarouter.home` server certificate issued by that root. `/etc/serverkey.pem` is the paired HTTPS server private-key file; its content is not reproduced. No call-site evidence establishes that this certificate chain is the firmware updater's trust anchor. No OEM update signing private key or documented authorized signing process was found. Therefore legitimate authentication of a custom image is **BLOCKED** on current evidence.

No package-level checksum algorithm or coverage was identified. The outer container signature/checksum and the exact bytes covered by authentication remain **UNKNOWN**.

## Flash mapping and update behavior

**VERIFIED:** `ATP_MTD_Getfd` has a bound check against 15 followed by a jump-table dispatch for logical indices 0–15 and static `/dev/mtd0` through `/dev/mtd15` strings. The library has separate MTD selection, erase, read, write, area-write, generic upgrade, configuration upgrade, bootloader upgrade, and partition-write functions. `upg` imports several of these flash APIs.

**UNKNOWN:** no evidence maps section/component IDs to logical MTD indices; nor does it label the partitions, establish the metadata offsets' address space, or show how the active main/slave side is chosen. The existence of a bootloader-upgrade helper does not establish that bootloader updating is mandatory or optional. The existence of RootFS and kernel component IDs does not establish independent update eligibility. Exact erase geometry, recovery/rollback behavior, and protected-region exclusions are also unresolved.

No `/dev/mtd*` device was opened and no erase or write operation was performed.

## OEM startup and compatibility

Files inspected:

- `/home/ayad/build-output/rootfs/etc/inittab`, SHA-256 `e36c598c6c364f8e83de3fe40b1bf4f50d16ba031023e06a1934bbd91bc7b64a`
- `/home/ayad/build-output/rootfs/etc/init.d/rcS`, SHA-256 `7c31a33578ddd71ebbaa8f9c79453d00d9762f020a7c035dd8bd09e9ae64e116`
- `/home/ayad/build-output/rootfs/etc/profile`, SHA-256 `ebce1e5930054326095b6df72101d1c5690854b5750dad225064ccec4695cca2`

`inittab` configures `::sysinit:/etc/init.d/rcS` and `::respawn:-/bin/sh`. `rcS` only prints `RCS DONE`. `/etc/profile` contains the substantial vendor initialization: temporary filesystems, device-node creation, `startbsp`, optional config JFFS2 mounts, `hi_xpon`, background `hsanportinit` and `insmod_all.sh`, `/dev/caldata` linked to `/dev/mtd9`, then `mic`.

These service and module initialization paths must remain intact for a vendor-kernel compatibility experiment. A respawned shell makes an operator-controlled manual command conceivable, but console access, privilege state, environment, service interactions, and safe runtime coexistence are not proven. No dedicated unattended OpenLinux service hook is established. Do not modify OEM startup files as part of this static investigation.

## Explicit answers and recommendation

| Question | Finding |
|---|---|
| Does a legitimate RootFS-only OEM update path exist? | **UNKNOWN / not demonstrated.** Treat it as unavailable for planning; no package/component eligibility branch was proved. |
| Can OEM authentication be satisfied legitimately from available material? | **BLOCKED.** Signature contract and authorized updater signing key/process are unavailable. Server HTTPS key material is not evidence of firmware signing authority. |
| Are main/slave records proof of dual-bank update behavior? | **No. UNKNOWN.** Their metadata labels exist, but address space and selection semantics are unresolved. |
| Must the package include every component? | **UNKNOWN.** Neither partial-package acceptance nor a complete-package requirement is proved. |
| Are bootloader or kernel updates mandatory? | **UNKNOWN.** Helpers and component records exist; eligibility and requiredness are unresolved. |
| Is the reconstructed firmware flashable? | **No claim.** Keep `EXPERIMENTAL_NON_FLASHABLE`; neither OEM acceptance nor a verified recovery path is established. |

**Recommended next technical step:** seek vendor-signed documentation or an authorized Huawei update service/key-custody path that explicitly states RootFS component-only eligibility and the signature contract. Until that exists, do not generate or submit an OEM package. Continue only a separate, non-flashing userspace compatibility prototype using the original kernel, with an independently established recovery path and operator-controlled launch; preserve vendor startup and driver services.

## Reproducible evidence and safety

Machine-readable inventory, hashes, symbol call sites, package metadata, classifications, unresolved questions, and safety record are in [`updater-static-analysis.json`](updater-static-analysis.json). Supporting static-analysis outputs are in `analysis/generated/upg-static/`, `analysis/generated/upgrade-re/`, and `analysis/oem-firmware/`.

No OEM ARM executable was run. No MTD device was opened. No flash was written. The original firmware and extracted artifacts were left unchanged. No private key contents are included.
