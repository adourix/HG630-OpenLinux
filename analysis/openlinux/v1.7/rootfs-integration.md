# V1.7 additive OEM RootFS integration

## Pipeline and result

`tools/integrate_v17_rootfs.py` starts with the immutable extracted `/home/ayad/build-output/rootfs`, builds the versioned runtime package, extracts it under `/opt/openlinux`, and calls the existing allowlisted `tools/build_rootfs.py`. It emits `before-manifest.json`, `after-manifest.json`, `integration-report.json`, `build-report.json`, the sorted file-priority list, and a host-extractable SquashFS. Outputs are created only in a new directory; an existing output is refused.

Build command used:

```sh
python3 tools/integrate_v17_rootfs.py \
  --rootfs /home/ayad/build-output/rootfs \
  --source-squashfs /home/ayad/build-output/carved/rootfs.squashfs \
  --runtime build/runtime \
  --output /home/ayad/build-output/openlinux-v1.7/rootfs-integration-final
```

Result: `/home/ayad/build-output/openlinux-v1.7/rootfs-integration-final/rootfs-build/rootfs.squashfs`, SquashFS 4.0/XZ, block size 1 MiB, `bytes_used=5,919,263`, reserved RootFS span `5,931,008`, margin `11,745` bytes. SHA-256: `0aa4ef57bafae5bd5b5b8804a30765a348e6acf00eaf64c0dcc2f22f2df22ca3`.

Before/after metadata manifests show **zero changed and zero missing original paths**. The archive extracts and matches the staged RootFS path/content/mode/uid/gid/mtime inventory exactly. OEM timestamps are preserved: the builder now normalizes only the SquashFS superblock timestamp and does not use `-all-time` to rewrite every original inode time. Fourteen package files are added under `/opt/openlinux`; no OEM daemon, library, driver, account file, device table, init script, kernel, or calibration data is replaced.

SSH remains disabled. No boot hook is added. `openlinuxctl ssh-start` is operator-invoked and refuses to run unless a dedicated non-root account, matching home/shell, protected key material, local bind address, devpts, and OEM daemon are evidenced. The supplied RootFS currently lacks the dedicated account and `dropbearkey`, and does not show a devpts mount. Therefore this candidate does not make SSH operational on the stock image.

## Full-container reconstruction

After RootFS structural, fit, and exact extraction checks passed, the existing firmware rebuilder created a separate full-size research artifact at `/home/ayad/build-output/openlinux-v1.7/HG630V2-openlinux-v1.7-final-EXPERIMENTAL_NON_FLASHABLE.bin` (7,563,600 bytes; SHA-256 `f93e40742d503c1d24a45616471c836321077fdba4689a313c2b5dd50f156ae4`). It retains the original package prefix, component table, kernel and suffix byte-for-byte; uImage CRCs validate. Candidate RootFS has 11,745 bytes internal margin. The builder's explicit `--allow-unpinned-experimental-rootfs` option was needed because this candidate differs from the previously pinned V1.5 image; it does not sign or bypass OEM authentication. The result is explicitly `EXPERIMENTAL_NON_FLASHABLE`; do not upload or flash it.

The generic firmware inspector reports known metadata extent/overlap warnings for both the original and rebuilt package; the same warnings occur on the unchanged original image. Their address-space semantics remain unresolved. Package, RootFS, and uImage structural checks pass, but those warnings and OEM authentication remain unresolved.

No claim is made for updater acceptance, signature validity, boot, DSL/Ethernet/Wi-Fi, recovery, or physical compatibility.
