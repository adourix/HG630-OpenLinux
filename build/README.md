# Isolated analysis/build environment

`Dockerfile` defines a Debian 13 (trixie) environment with the read-only firmware tools, SquashFS utilities, and both ARM EABI toolchain families. Build it from the repository root:

```sh
docker build -f build/Dockerfile -t hg630-openlinux-analysis .
docker run --rm -it \
  -v "$PWD:/workspace" \
  -v /path/to/local-input:/input:ro \
  hg630-openlinux-analysis
```

Run `tools/run_analysis.sh /input/HG630V2-12V100R001.bin` inside the container. Keep `/input` read-only and write generated output under the ignored `analysis/generated/` or `build-output/` directories.

The image deliberately installs both `arm-linux-gnueabi` and `arm-linux-gnueabihf`. The correct one cannot be selected from the uImage architecture byte alone; `tools/detect_abi.py` selects based on actual extracted ELF AEABI attributes. No firmware image is produced by this environment.
