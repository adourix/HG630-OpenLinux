# V1.2 OEM-preserving OpenLinux runtime scaffold

Date: 2026-11-10. Status: **host-validated runtime scaffold; hardware compatibility UNKNOWN**.

## Summary

This implementation adds an operator-controlled, relocatable shell runtime package. It can be extracted under a writable operator-selected location (including `/opt/openlinux` only if that location is verified writable). It does not assume USB, a specific mount point, writable OEM rootfs, or nonvolatile flash. The inspected extracted RootFS has no `/opt` directory; the original RootFS is SquashFS and treated as immutable.

The package contains a minimal monitor daemon, launcher, shutdown command, configuration, ownership marker, and generated manifest. It is **scaffolding**, not the OpenLinux network/service payload. No network action is implemented; `NETWORK_MODE` must remain `disabled`. A configurable bind address is recorded for future work but is unused. Existing experimental network, DHCP, firewall, and SSH scripts are not activated or copied into this runtime package because interface ownership, routing, DNS/DHCP integration, firewall backend, and service coexistence are unverified.

The monitor writes a timestamp and `/proc/uptime` value to its own log. It does not open sockets, alter routes/firewall/resolver state, mount filesystems, read/write MTD devices, or manage Huawei processes. The launcher checks dependencies and vendor readiness, creates state only inside the package directory, uses an atomic directory lock, refuses a second instance, and verifies `/proc/<pid>/cmdline` before signalling a recorded daemon. Shutdown is idempotent. Uninstall checks the package marker and removes only the fixed package file list and its private state; symlinked package directories are rejected. Additional user files prevent removal of the containing directory and are preserved.

## OEM ABI and runtime requirements

### VERIFIED from extracted OEM files

- `/home/ayad/build-output/rootfs/bin/busybox` is ELF32 little-endian ARM EABI5 (`e_flags=0x05000002`). Its program interpreter is `/lib/ld-uClibc.so.0`; that name links to `ld-uClibc-0.9.32.1-git.so`. The corresponding OEM libc is uClibc 0.9.32.1-git.
- `/bin/sh` and the required `cat`, `date`, `kill`, `mkdir`, `rm`, and `sleep` commands are symlinks to the OEM BusyBox. `rmdir` is present in the BusyBox embedded applet strings but has no standalone symlink, so the runtime uses `/bin/busybox rmdir` when no `rmdir` command is on `PATH`.
- The runtime package contains only POSIX shell scripts and text configuration. It has no ELF executable, no shared-library dependency, and no ARM calling-convention requirement of its own. It invokes OEM `/bin/sh` and verified BusyBox command paths at runtime; this is not a host-side execution of those OEM binaries.
- Launcher readiness requires `/dev/caldata` to be a symlink (created in the inspected OEM startup profile after its mounts and board initialization) and at least one `/proc/<pid>/comm` entry equal to `mic` (the vendor service started at the end of the inspected profile). These checks establish that startup reached those observed markers; they do not prove DSL/Wi-Fi readiness or every vendor daemon's health.
- Runtime process monitoring reads `/proc/<pid>/cmdline` for its own child and `/proc/uptime` for a log entry, and uses standard process signaling/wait/sleep behavior. Procfs availability is consistent with the OEM startup script mounting `/proc`. Actual 2.6.30 kernel behavior with this script is untested.

### UNKNOWN / BLOCKED

- There is no compiled OpenLinux ARM service binary or matching shared-library payload in the current source tree. Existing service code is experimental shell code and does not establish deployable target behavior.
- A host `arm-linux-gnueabi-gcc` is not evidence of an ABI-matched uClibc toolchain. A compatible ARM EABI5 cross compiler plus the matching uClibc 0.9.32.1-git headers/sysroot, along with the intended compiled service source and audited dependency set, is the missing build dependency for a native OpenLinux payload.
- Exact syscall needs and ABI requirements of any future native service remain UNKNOWN. No OpenLinux application binary was linked or run.
- QEMU executables and preserved VExpress A9 inputs are available. An optional test boots a fresh initramfs with the packaged runtime and a separately built static BusyBox, then exercises start/status/duplicate-start/stop. The emulator is not the HG630 HiSilicon SD5610x platform. The OEM kernel and OEM ARM binaries were not executed; QEMU success does not establish router compatibility.
- No writable router storage or transport mount has been verified. The package is relocatable and the operator must select an available writable path. A RAM-backed destination is volatile; an external path is not assumed.

## Package and commands

Source: `build/runtime/`. Builder: `tools/package_runtime.py`. Tests: `tests/test_runtime.py`.

Exact package build command used:

```bash
python3 tools/package_runtime.py \
  --source build/runtime \
  --output /home/ayad/build-output/openlinux-runtime-v1.2.tar.gz
```

Output: `/home/ayad/build-output/openlinux-runtime-v1.2.tar.gz`  
Size: 4,417 bytes  
SHA-256: `727c1ad23a7b729f7b0a2ad1b7dd8f7ce7cf4d98332d7333f840fdee88015409`

The archive contains the top-level directory `openlinux/`. `openlinux/manifest.json` records each payload path, SHA-256, size, mode, dependencies, ownership, network posture, and package-owned state rules. Its own hash is null by design to avoid recursive self-hashing. Tar entries are normalized to root ownership and timestamp zero; extracted ownership follows the permissions of the operator's tar invocation/filesystem.

On a router, an operator would first confirm a writable destination after OEM initialization, unpack the archive there, then call `openlinux/bin/openlinuxctl start` by absolute path. `status` reports state; `stop` or `bin/openlinux-shutdown` stops only the verified OpenLinux monitor process. `sbin/openlinux-uninstall` removes only the marked package's known files and private state. No OEM startup file is touched. No fixed destination is prescribed.

## Validation

- Full suite with the optional QEMU test enabled: `OPENLINUX_QEMU_KERNEL=/home/ayad/build-output/openlinux-v09/image-v09/openlinux-v0.9-vexpress-a9.zImage OPENLINUX_QEMU_DTB=/home/ayad/build-output/openlinux-v09/image-v09/openlinux-v0.9-vexpress-a9.dtb OPENLINUX_QEMU_BUSYBOX=/home/ayad/build-output/openlinux-v09/busybox-build/busybox python3 -m unittest discover -s tests -v` — **93 tests passed**.
- Runtime tests use host shell processes and temporary fake `/proc` and `/dev` trees. They cover package repeatability and manifest hashes/modes, duplicate-start refusal, idempotent stop, missing vendor readiness, missing dependency failure before lock creation, refusal to signal an unrelated PID, and conservative uninstall behavior.
- `python3 tools/package_runtime.py` produced the archive above. The package test independently builds two archives and compares bytes. QEMU test uses copied files in a temporary directory and leaves preserved V0.9 inputs unchanged.
- No OEM ARM executable was run by tests. No MTD node was accessed. No OEM RootFS, startup file, kernel, firmware, interface, route, firewall, or service was modified.
- **Physical router validation required:** verify a user-selected writable runtime location, confirm the two readiness markers on device, inspect logs while Huawei services remain healthy, then exercise start/status/stop/uninstall. Do not perform that validation until a recovery path is established. VExpress QEMU and host tests do not establish HG630 V2 compatibility.

## Next technical step

Obtain or build an ARM EABI5/uClibc 0.9.32.1-git toolchain/sysroot and identify the intended OpenLinux service source/dependency set. Build and inspect that payload without integrating it into OEM startup; only then extend the runtime manifest and add target-ABI tests. Keep network services disabled until interface, routing, firewall, DHCP/DNS, and vendor-service coexistence are established.
