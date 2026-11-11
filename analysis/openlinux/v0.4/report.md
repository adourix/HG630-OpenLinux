# OpenLinux V0.4 integration and boot readiness

Date: 2026-11-10

## Result

V0.4 improves integration safety and compatibility validation without changing
the OEM startup path. The OEM init sequence is documented from actual file
calls. The OpenLinux hook is hardened but remains outside `rcS` and `/etc/profile`
because no safe one-shot insertion point is proven.

The V0.4 RootFS and experimental container were rebuilt because the hook and
runtime command dependencies changed. Both remain non-hardware artifacts.

## OEM init findings

**VERIFIED:** BusyBox init runs `/etc/init.d/rcS` as `sysinit`, then respawns
`-/bin/sh`. `rcS` only sets `PATH` and prints `RCS DONE`. The shell environment
then sources `/etc/profile`, which performs mounts, device creation, `startbsp`,
`hi_xpon`, background `hsanportinit`, background `/etc/insmod_all.sh`, the
calibration-device link, and `mic` startup. `insmod_eth.sh` is present but not
called by this observed path.

**INFERRED:** `mic` is the vendor dynamic application manager for services such
as SSH, DHCP, DNS, firewall, DDNS, and other management processes. Its strings
prove process/exec/restart and service references, but not exact launch order.

The detailed inventory is in [init-inventory.json](init-inventory.json), with
[init-order.md](init-order.md) and [vendor-dependencies.md](vendor-dependencies.md).

## Safe integration

The OpenLinux hook now:

- exits successfully when the binary or configuration is absent;
- validates configuration before starting anything;
- runs with a bounded shell timeout;
- logs invalid configuration, timeout, and supervisor failure to an
  OpenLinux-owned path;
- always exits without propagating OpenLinux failure to OEM startup.

The hook is not called by OEM `rcS` or `/etc/profile`. Injecting it would either
replace the verified sysinit script or risk repeated execution on shell respawn.
Automatic boot integration is therefore **UNKNOWN/BLOCKED**, and no startup
path was modified.

## SquashFS compatibility

Original and V0.3/V0.4 filesystems are SquashFS 4.0, little-endian, XZ, with
1 MiB blocks. The original kernel contains SquashFS XZ and `xz_dec_*` evidence.
V0.3/V0.4 add an ARM XZ BCJ filter to fit the fixed RootFS span. The kernel
configuration is unavailable and filter support is not proven; BCJ compatibility
is **UNKNOWN/BLOCKED**. The build option remains explicit and non-default.

See [squashfs-comparison.json](squashfs-comparison.json) and
[squashfs-compatibility.md](squashfs-compatibility.md).

## Compatibility audit

The original ARM EABI5/uClibc interpreter, Linux 2.6.30 ARMv7 module vermagic,
vendor libraries, and module dependencies are preserved. V0.4 scripts use only
verified runtime facilities after removing V0.3's unavailable `sed`, `wc`, `mv`,
and `tr` dependencies. Static kernel support for proc/sysfs/tmpfs/modules/MTD
and network facilities is evidenced, but runtime kernel behavior is not.

See [compatibility-audit.json](compatibility-audit.json) and
[compatibility-audit.md](compatibility-audit.md).

## Boot simulation

The host simulator executes the actual OEM `rcS` sysinit and then the isolated
OpenLinux hook. It covers OEM-only, disabled, missing/invalid configuration,
supervisor failure, timeout, missing binary, and logging failure. The V0.4
staged RootFS result was:

```text
OEM stdout: RCS DONE
OEM returncode: 0
OpenLinux returncode: 0
oem_failure_isolated: true
```

ARM user-mode QEMU also executed V0.4 `status`, network validation, DHCP
validation, firewall status, SSH status, monitoring, and dry-run commands with
RootFS-only `PATH` and `QEMU_LD_PREFIX`. The dynamic-loader cache warning is
from the preserved legacy RootFS; commands still returned expected results.
This is userspace validation, not kernel boot.

## V0.4 artifacts

- RootFS: `/home/ayad/build-output/custom-build/run-013/rootfs.squashfs`
- RootFS SHA256: `db620f72a514c62cccc9cd3ae6cb7d27151abec59cb4cb58b4c1aee393777785`
- Firmware: `/home/ayad/build-output/custom-build/firmware-run-004/HG630V2-v0.4-experimental.bin`
- Firmware SHA256: `9ec2d00ffa546c7b0d3be228c0867fba7ffac2a5e354c6b22d249d1035ab5cb1`
- Complete builder manifest: `/home/ayad/build-output/custom-build/firmware-run-004/HG630V2-v0.4-experimental.bin.manifest.json`
- Summary manifest: [manifest.json](manifest.json)
- Label: `EXPERIMENTAL_NON_FLASHABLE`

No original firmware, previous artifact, bootloader, MTD device, or router was
modified or accessed.
