import gzip
import hashlib
import json
import os
import selectors
import shutil
import subprocess
import tempfile
import tarfile
import time
import unittest
from pathlib import Path

from tools.package_runtime import build


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/runtime"
CTL = SOURCE / "bin/openlinuxctl"
UNINSTALL = SOURCE / "sbin/openlinux-uninstall"


class RuntimePackageTests(unittest.TestCase):
    def test_package_is_reproducible_and_manifest_hashes_files(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.tar.gz"
            second = Path(directory) / "second.tar.gz"
            result = build(SOURCE, first)
            build(SOURCE, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(result["sha256"], hashlib.sha256(first.read_bytes()).hexdigest())
            with tarfile.open(first, "r:gz") as package:
                manifest = json.load(package.extractfile("openlinux/manifest.json"))
                for record in manifest["files"]:
                    if record["sha256"] is None:
                        continue
                    data = package.extractfile("openlinux/" + record["path"]).read()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
                    member = package.getmember("openlinux/" + record["path"])
                    self.assertEqual(f"{member.mode:04o}", record["mode"])
            self.assertEqual(manifest["network"]["default"], "disabled")
            self.assertFalse(manifest["network"]["network_actions_implemented"])
            self.assertFalse(manifest["network"]["bind_address_used"])

    def make_runtime(self, parent: Path) -> tuple[Path, Path, Path]:
        base = parent / "runtime"
        shutil.copytree(SOURCE, base)
        (base / "var/run").mkdir(parents=True)
        (base / "var/log").mkdir(parents=True)
        proc = parent / "proc"
        (proc / "123").mkdir(parents=True)
        (proc / "123/comm").write_text("mic\n")
        (proc / "uptime").write_text("42.00 10.00\n")
        dev = parent / "dev"
        dev.mkdir()
        (dev / "caldata").symlink_to("mtd-not-opened")
        return base, proc, dev

    def run_ctl(self, base: Path, proc: Path, dev: Path, action: str,
                ctl: Path = CTL) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env.update({
            "OPENLINUX_HOME": str(base),
            "OPENLINUX_VENDOR_PROC_ROOT": str(proc),
            "OPENLINUX_DEV_ROOT": str(dev),
            "OPENLINUX_INTERVAL": "1",
            "PATH": "/usr/bin:/bin",
        })
        return subprocess.run(["/bin/sh", str(ctl), action], env=env, text=True,
                              capture_output=True, check=False, timeout=10)

    def test_extracted_archive_launcher_start_status_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            archive = temp / "runtime.tar.gz"
            build(SOURCE, archive)
            with tarfile.open(archive, "r:gz") as package:
                package.extractall(temp, filter="data")
            base = temp / "openlinux"
            (base / "var/run").mkdir(parents=True)
            (base / "var/log").mkdir(parents=True)
            proc = temp / "vendor-proc"
            (proc / "22").mkdir(parents=True)
            (proc / "22/comm").write_text("mic\n")
            dev = temp / "vendor-dev"
            dev.mkdir()
            (dev / "caldata").symlink_to("mtd-not-opened")
            ctl = base / "bin/openlinuxctl"
            for action in ("start", "status", "stop", "stop"):
                result = self.run_ctl(base, proc, dev, action, ctl)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_duplicate_start_is_refused_and_shutdown_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            base, proc, dev = self.make_runtime(Path(directory))
            started = self.run_ctl(base, proc, dev, "start")
            self.assertEqual(started.returncode, 0, started.stderr)
            pidfile = base / "var/run/openlinux.lock/pid"
            self.assertTrue(pidfile.exists())
            pid = int(pidfile.read_text())
            repeated = self.run_ctl(base, proc, dev, "start")
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertIn("already running", repeated.stdout)
            self.assertEqual(int(pidfile.read_text()), pid)
            stopped = self.run_ctl(base, proc, dev, "stop")
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            self.assertFalse((base / "var/run/openlinux.lock").exists())
            again = self.run_ctl(base, proc, dev, "stop")
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertIn("not running", again.stdout)

    def test_missing_vendor_readiness_does_not_create_runtime_state(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "runtime"
            shutil.copytree(SOURCE, base)
            proc = Path(directory) / "proc"
            proc.mkdir()
            dev = Path(directory) / "dev"
            dev.mkdir()
            result = self.run_ctl(base, proc, dev, "start")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("vendor readiness not established", result.stderr)
            self.assertFalse((base / "var/run/openlinux.lock").exists())

    def test_missing_dependency_fails_before_lock_or_oem_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            base, proc, dev = self.make_runtime(Path(directory))
            marker = Path(directory) / "oem-state.txt"
            marker.write_text("untouched\n")
            env = os.environ.copy()
            env.update({
                "OPENLINUX_HOME": str(base),
                "OPENLINUX_VENDOR_PROC_ROOT": str(proc),
                "OPENLINUX_DEV_ROOT": str(dev),
                "PATH": "/no-such-runtime-path",
            })
            result = subprocess.run(["/bin/sh", str(CTL), "start"], env=env, text=True,
                                    capture_output=True, check=False, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required command is missing", result.stderr)
            self.assertFalse((base / "var/run/openlinux.lock").exists())
            self.assertEqual(marker.read_text(), "untouched\n")

    def test_shutdown_never_signals_unrelated_process(self):
        with tempfile.TemporaryDirectory() as directory:
            base, proc, dev = self.make_runtime(Path(directory))
            process = subprocess.Popen(["/bin/sleep", "20"])
            try:
                run = base / "var/run/openlinux.lock"
                run.mkdir(parents=True)
                (run / "pid").write_text(f"{process.pid}\n")
                result = self.run_ctl(base, proc, dev, "stop")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("no process signaled", result.stderr)
                self.assertIsNone(process.poll())
            finally:
                process.terminate()
                process.wait(timeout=5)

    def test_uninstall_removes_only_openlinux_owned_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            base, proc, dev = self.make_runtime(Path(directory))
            (base / "operator-note.txt").write_text("preserve me\n")
            env = os.environ.copy()
            env.update({"OPENLINUX_HOME": str(base), "OPENLINUX_VENDOR_PROC_ROOT": str(proc), "OPENLINUX_DEV_ROOT": str(dev)})
            result = subprocess.run(["/bin/sh", str(UNINSTALL)], env=env, text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((base / "operator-note.txt").exists())
            self.assertFalse((base / "bin/openlinuxctl").exists())

    def test_uninstall_removes_clean_openlinux_owned_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            base, proc, dev = self.make_runtime(Path(directory))
            env = os.environ.copy()
            env.update({"OPENLINUX_HOME": str(base), "OPENLINUX_VENDOR_PROC_ROOT": str(proc), "OPENLINUX_DEV_ROOT": str(dev)})
            result = subprocess.run(["/bin/sh", str(UNINSTALL)], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(base.exists())

    @unittest.skipUnless(
        all(os.environ.get(name) for name in (
            "OPENLINUX_QEMU_KERNEL", "OPENLINUX_QEMU_DTB", "OPENLINUX_QEMU_BUSYBOX"))
        and shutil.which("qemu-system-arm") and shutil.which("cpio"),
        "set VExpress QEMU kernel, DTB, BusyBox, and install qemu-system-arm/cpio",
    )
    def test_optional_qemu_vexpress_runtime_controls(self):
        kernel = Path(os.environ["OPENLINUX_QEMU_KERNEL"])
        dtb = Path(os.environ["OPENLINUX_QEMU_DTB"])
        busybox = Path(os.environ["OPENLINUX_QEMU_BUSYBOX"])
        for path in (kernel, dtb, busybox):
            self.assertTrue(path.is_file(), f"missing QEMU input: {path}")
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            archive = temp / "runtime.tar.gz"
            build(SOURCE, archive)
            package_dir = temp / "package"
            package_dir.mkdir()
            with tarfile.open(archive, "r:gz") as package:
                package.extractall(package_dir, filter="data")

            stage = temp / "initramfs"
            for name in ("bin", "dev", "etc", "proc", "run", "sys", "tmp", "opt"):
                (stage / name).mkdir(parents=True, exist_ok=True)
            shutil.copy2(busybox, stage / "bin/busybox")
            for applet in ("sh", "date", "mkdir", "rm", "sleep", "mount", "ln"):
                (stage / "bin" / applet).symlink_to("busybox")
            shutil.copytree(package_dir / "openlinux", stage / "opt/openlinux")
            init = stage / "init"
            init.write_text("""#!/bin/sh
PATH=/bin:/sbin
export PATH
mount -t proc proc /proc 2>/dev/null || :
mount -t sysfs sysfs /sys 2>/dev/null || :
mount -t devtmpfs devtmpfs /dev 2>/dev/null || :
mkdir -p /run/vendor-proc/123 /run/vendor-dev
echo mic > /run/vendor-proc/123/comm
ln -s mtd-not-opened /run/vendor-dev/caldata
export OPENLINUX_HOME=/opt/openlinux
export OPENLINUX_VENDOR_PROC_ROOT=/run/vendor-proc
export OPENLINUX_DEV_ROOT=/run/vendor-dev
export OPENLINUX_INTERVAL=1
/opt/openlinux/bin/openlinuxctl start || { echo QEMU_RUNTIME_START_FAILED; exec /bin/sh; }
/opt/openlinux/bin/openlinuxctl status || { echo QEMU_RUNTIME_STATUS_FAILED; exec /bin/sh; }
/opt/openlinux/bin/openlinuxctl start || { echo QEMU_RUNTIME_DUPLICATE_FAILED; exec /bin/sh; }
/opt/openlinux/bin/openlinuxctl stop || { echo QEMU_RUNTIME_STOP_FAILED; exec /bin/sh; }
/opt/openlinux/bin/openlinuxctl stop || { echo QEMU_RUNTIME_STOP_IDEMPOTENCE_FAILED; exec /bin/sh; }
echo OPENLINUX_RUNTIME_QEMU_PASS
exec /bin/sh
""")
            init.chmod(0o755)
            listing = ".\n" + "\n".join("./" + path.relative_to(stage).as_posix() for path in sorted(stage.rglob("*"))) + "\n"
            cpio = subprocess.run(["cpio", "-o", "-H", "newc"], cwd=stage,
                                  input=listing.encode(), capture_output=True, check=True, timeout=10)
            initramfs = temp / "runtime.cpio.gz"
            import gzip
            with initramfs.open("wb") as raw:
                with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as output:
                    output.write(cpio.stdout)
            command = [
                "qemu-system-arm", "-M", "vexpress-a9", "-m", "256M",
                "-kernel", str(kernel), "-dtb", str(dtb), "-initrd", str(initramfs),
                "-append", "console=ttyAMA0,115200 rdinit=/init", "-serial", "stdio",
                "-monitor", "none", "-display", "none", "-audio", "driver=none",
                "-nic", "none", "-no-reboot",
            ]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=False, bufsize=0)
            output = bytearray()
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            try:
                deadline = time.monotonic() + 25
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        break
                    for _, _ in selector.select(timeout=0.25):
                        chunk = os.read(process.stdout.fileno(), 65536)
                        if not chunk:
                            break
                        output.extend(chunk)
                        if b"OPENLINUX_RUNTIME_QEMU_PASS" in output:
                            break
                    if b"OPENLINUX_RUNTIME_QEMU_PASS" in output:
                        break
                self.assertIn(b"OPENLINUX_RUNTIME_QEMU_PASS", output,
                              output.decode("utf-8", "replace")[-4000:])
                self.assertIn(b"already running", output)
                self.assertIn(b"OpenLinux runtime stopped", output)
            finally:
                selector.close()
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
                process.stdout.close()


if __name__ == "__main__":
    unittest.main()
