# Report 3 — Root filesystem inventory

Rootfs extraction and inventory were not completed on this server because the input firmware is unavailable. The repository tools are ready to run in the isolated Debian 13 container:

```sh
tools/run_analysis.sh /input/HG630V2-12V100R001.bin
```

Expected outputs are `firmware-inspect.json`, `carved/`, `rootfs/`, `rootfs-inventory.json`, and `abi.json` under ignored generated output. No extracted proprietary files are committed.
