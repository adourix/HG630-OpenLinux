# Experimental builds

This directory contains small, reproducible build inputs only. Large SquashFS,
firmware, and extracted RootFS artifacts stay outside Git under
`/home/ayad/build-output/`.

The `openlinux-overlay/rootfs` tree is applied after copying the complete OEM
RootFS. It adds an opt-in userspace supervisor and configuration validator; it
does not replace the vendor kernel, libraries, drivers, DSL stack, or original
boot scripts.

Example build (use a new output directory for every run):

```sh
pgrep -af 'tools/build_rootfs.py' || true
python3 tools/build_rootfs.py \
  /home/ayad/build-output/custom-build/run-007/stage-rootfs \
  --overlay build/experimental/openlinux-overlay/rootfs \
  --output /home/ayad/build-output/custom-build/run-V03 \
  --source-squashfs /home/ayad/build-output/custom-build/run-007/rootfs.squashfs \
  --bcj arm --pad-to 5931008
python3 tools/build_firmware.py \
  /home/ayad/firmware-input/HG630V2-12V100R001.bin \
  /home/ayad/build-output/custom-build/run-V03/rootfs.squashfs \
  --output /home/ayad/build-output/custom-build/firmware-run-003/HG630V2-v0.3-experimental.bin
```

The firmware result remains experimental and non-flashable while OEM signature
and outer-container requirements are unresolved. `--bcj arm` is an explicit
experimental XZ filter choice; the kernel's acceptance of this filter has not
been proven by actual HG630 V2 boot.
