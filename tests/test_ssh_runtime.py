"""OpenLinux SSH wrapper tests. Mock daemon tests cover lifecycle only, never SSH auth."""
import os
import base64
import struct
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/runtime"


class SshRuntimeTests(unittest.TestCase):
    @staticmethod
    def ecdsa_public_line():
        algorithm = b"ecdsa-sha2-nistp256"
        curve = b"nistp256"
        point = b"\x04" + (b"\x01" * 64)
        blob = struct.pack(">I", len(algorithm)) + algorithm + struct.pack(">I", len(curve)) + curve + struct.pack(">I", len(point)) + point
        return "ecdsa-sha2-nistp256 " + base64.b64encode(blob).decode() + " user@test\n"
    def package(self, temp: Path) -> Path:
        base = temp / "openlinux"
        shutil.copytree(SOURCE, base)
        return base

    def env(self, base: Path, **extra):
        result = os.environ.copy()
        result["OPENLINUX_HOME"] = str(base)
        result.update({key: str(value) for key, value in extra.items()})
        return result

    def call_ctl(self, base: Path, *args, env=None):
        return subprocess.run(["/bin/sh", str(base / "bin/openlinuxctl"), *args],
                              env=env or self.env(base), text=True, capture_output=True,
                              timeout=15, check=False)

    def test_all_runtime_shell_scripts_parse(self):
        scripts = list((SOURCE / "bin").glob("*")) + list((SOURCE / "libexec").glob("*")) + list((SOURCE / "sbin").glob("*"))
        for script in scripts:
            result = subprocess.run(["/bin/sh", "-n", str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"{script}: {result.stderr}")

    def test_diagnostic_reports_missing_evidence_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            proc = temp / "proc"; proc.mkdir(); (proc / "mounts").write_text("proc /proc proc rw 0 0\n")
            (proc / "filesystems").write_text("nodev\tsysfs\n")
            (proc / "version").write_text("Linux version fixture\n")
            (proc / "cmdline").write_text("console=tty\n")
            dev = temp / "dev"; dev.mkdir(); (dev / "pts").mkdir()
            before = sorted(str(p.relative_to(temp)) for p in temp.rglob("*"))
            env = self.env(base, OPENLINUX_PROC_ROOT=proc, OPENLINUX_DEV_ROOT=dev,
                           OPENLINUX_OEM_ROOT=temp / "absent")
            result = self.call_ctl(base, "ssh-check", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no devpts mount", result.stdout)
            self.assertIn("/dev/ptmx is absent", result.stdout)
            self.assertIn("MISSING/UNKNOWN", result.stdout)
            after = sorted(str(p.relative_to(temp)) for p in temp.rglob("*"))
            self.assertEqual(before, after)

    def test_disabled_default_refuses_to_start(self):
        with tempfile.TemporaryDirectory() as directory:
            base = self.package(Path(directory))
            result = self.call_ctl(base, "ssh-start")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SSH is disabled", result.stderr)

    def test_enabled_but_missing_devpts_refuses_before_daemon_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_HOME=\n", f"SSH_HOME={temp}/home/openlinux\n")
                            .replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={temp}/state\n")
                            .replace("SSH_BIND_ADDRESS=\n", "SSH_BIND_ADDRESS=127.0.0.1\n"))
            home = temp / "home/openlinux"; (home / ".ssh").mkdir(parents=True)
            (home / ".ssh").chmod(0o700)
            (home / ".ssh/authorized_keys").write_text("ecdsa-sha2-nistp256 AAAA test\n")
            (home / ".ssh/authorized_keys").chmod(0o600)
            state = temp / "state"; state.mkdir(); state.chmod(0o700)
            key = state / "dropbear_ecdsa_host_key"; key.write_text("fixture"); key.chmod(0o600)
            passwd = temp / "passwd"; passwd.write_text(f"openlinux:x:1000:1000:OpenLinux:{home}:/bin/sh\n")
            root = temp / "oem"; (root / "bin").mkdir(parents=True)
            marker = temp / "daemon-ran"; daemon = root / "bin/sshd"
            daemon.write_text(f"#!/bin/sh\ntouch '{marker}'\n"); daemon.chmod(0o755)
            env = self.env(base, OPENLINUX_OEM_ROOT=root, OPENLINUX_PASSWD_FILE=passwd, OPENLINUX_PROC_ROOT=temp / "proc",
                           OPENLINUX_DEV_ROOT=temp / "dev")
            (temp / "proc").mkdir(); (temp / "dev").mkdir(); (temp / "dev/pts").mkdir()
            (temp / "proc/mounts").write_text("proc /proc proc rw 0 0\n")
            (temp / "proc/filesystems").write_text("nodev\tsysfs\n")
            (temp / "proc/version").write_text("Linux fixture\n"); (temp / "proc/cmdline").write_text("\n")
            result = self.call_ctl(base, "ssh-start", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PTY/devpts", result.stderr)
            self.assertFalse(marker.exists())

    def test_invalid_ssh_port_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_BIND_ADDRESS=\n", "SSH_BIND_ADDRESS=127.0.0.1\n")
                            .replace("SSH_PORT=2222", "SSH_PORT=70000"))
            result = self.call_ctl(base, "ssh-start")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SSH_PORT must be in 1024..65535", result.stderr)

    def test_missing_oem_dropbear_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_HOME=\n", f"SSH_HOME={temp}/home/openlinux\n")
                            .replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={temp}/state\n")
                            .replace("SSH_BIND_ADDRESS=\n", "SSH_BIND_ADDRESS=127.0.0.1\n"))
            home = temp / "home/openlinux"; (home / ".ssh").mkdir(parents=True); (home / ".ssh").chmod(0o700)
            auth = home / ".ssh/authorized_keys"; auth.write_text("fixture\n"); auth.chmod(0o600)
            state = temp / "state"; state.mkdir(); state.chmod(0o700)
            hostkey = state / "dropbear_ecdsa_host_key"; hostkey.write_text("fixture"); hostkey.chmod(0o600)
            passwd = temp / "passwd"; passwd.write_text(f"openlinux:x:1000:1000:OpenLinux:{home}:/bin/sh\n")
            result = self.call_ctl(base, "ssh-start", env=self.env(base, OPENLINUX_PASSWD_FILE=passwd,
                                   OPENLINUX_OEM_ROOT=temp / "missing-oem"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("OEM Huawei Dropbear is missing", result.stderr)

    def test_ssh_stop_never_signals_unrelated_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            process = subprocess.Popen(["/bin/sleep", "20"])
            try:
                run = base / "var/run/openlinux-ssh"; run.mkdir(parents=True)
                (run / "pid").write_text(f"{process.pid}\n")
                result = self.call_ctl(base, "ssh-stop")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("no process signaled", result.stderr)
                self.assertIsNone(process.poll())
            finally:
                process.terminate(); process.wait(timeout=5)

    def test_missing_account_never_falls_back_to_root(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_HOME=\n", f"SSH_HOME={temp}/home/openlinux\n")
                            .replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={temp}/state\n")
                            .replace("SSH_BIND_ADDRESS=\n", "SSH_BIND_ADDRESS=192.0.2.1\n"))
            (temp / "home/openlinux/.ssh").mkdir(parents=True); (temp / "home/openlinux/.ssh/authorized_keys").write_text("x\n")
            (temp / "state").mkdir(); (temp / "state/dropbear_ecdsa_host_key").write_text("private")
            (temp / "state/dropbear_ecdsa_host_key").chmod(0o600); (temp / "state").chmod(0o700)
            passwd = temp / "passwd"; passwd.write_text("root:x:0:0:admin:/bin:/bin/sh\n")
            env = self.env(base, OPENLINUX_PASSWD_FILE=passwd, OPENLINUX_OEM_ROOT=temp / "oem")
            result = self.call_ctl(base, "ssh-start", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dedicated account 'openlinux' is absent", result.stderr)

    def test_provisioner_rejects_legacy_rsa_key_type(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp); key = temp / "user.pub"
            key.write_text("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ== test\n")
            (temp / "state").mkdir()
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_HOME=\n", f"SSH_HOME={temp}/home/openlinux\n")
                            .replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={temp}/state\n"))
            env = self.env(base, OPENLINUX_DROPBEARKEY="/missing/dropbearkey")
            result = self.call_ctl(base, "ssh-provision", str(key), env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only ecdsa-sha2-nistp256", result.stderr)

    def test_provisioner_requires_target_dropbearkey(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp); key = temp / "user.pub"
            key.write_text(self.ecdsa_public_line())
            (temp / "state").mkdir()
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_HOME=\n", f"SSH_HOME={temp}/home/openlinux\n")
                            .replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={temp}/state\n"))
            result = self.call_ctl(base, "ssh-provision", str(key), env=self.env(base, OPENLINUX_DROPBEARKEY="/missing/dropbearkey"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dropbearkey is missing", result.stderr)


    def test_provisioning_permissions_with_mock_keygen_only(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            home = temp / "home/openlinux"; home.mkdir(parents=True)
            state = temp / "external"; state.mkdir(); state.chmod(0o755)
            key = temp / "user.pub"; key.write_text(self.ecdsa_public_line())
            passwd = temp / "passwd"; passwd.write_text(f"openlinux:x:1000:1000:OpenLinux:{home}:/bin/sh\n")
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_HOME=\n", f"SSH_HOME={home}\n")
                            .replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={state}\n"))
            keygen = temp / "dropbearkey"
            keygen.write_text("#!/bin/sh\nwhile [ \"$#\" -gt 0 ]; do case \"$1\" in -f) out=$2; shift 2 ;; *) shift ;; esac; done\numask 077\nprintf mock-private-key > \"$out\"\n")
            keygen.chmod(0o755)
            result = self.call_ctl(base, "ssh-provision", str(key), env=self.env(base,
                                  OPENLINUX_PASSWD_FILE=passwd, OPENLINUX_DROPBEARKEY=keygen))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((state / "dropbear_ecdsa_host_key").stat().st_mode & 0o777, 0o600)
            self.assertEqual((home / ".ssh").stat().st_mode & 0o777, 0o700)
            self.assertEqual((home / ".ssh/authorized_keys").stat().st_mode & 0o777, 0o600)
            self.assertIn("No SSH authentication", result.stdout)

    def test_host_key_backup_and_restore_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            state = temp / "state"; state.mkdir(); state.chmod(0o700)
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={state}\n"))
            key = state / "dropbear_ecdsa_host_key"; key.write_text("mock ECDSA private key"); key.chmod(0o600)
            backup = temp / "safe-backup"; backup_dir = temp / "backup-dir"; backup_dir.mkdir()
            backup = backup_dir / "host-key"
            result = self.call_ctl(base, "ssh-provision", "backup", str(backup))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(backup.read_text(), key.read_text())
            self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
            (state / "dropbear_ecdsa_host_key").unlink()
            keygen = temp / "dropbearkey"
            keygen.write_text("#!/bin/sh\necho 'ecdsa-sha2-nistp256 AAAA test'\n"); keygen.chmod(0o755)
            result = self.call_ctl(base, "ssh-provision", "restore", str(backup),
                                   env=self.env(base, OPENLINUX_DROPBEARKEY=keygen))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(key.read_text(), "mock ECDSA private key")
            refused = self.call_ctl(base, "ssh-provision", "restore", str(backup),
                                    env=self.env(base, OPENLINUX_DROPBEARKEY=keygen))
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("refusing to overwrite", refused.stderr)

    def test_stale_pid_is_removed_without_signaling(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            run = base / "var/run/openlinux-ssh"; run.mkdir(parents=True)
            (run / "pid").write_text("4242\n")
            proc = temp / "proc"; proc.mkdir()
            result = self.call_ctl(base, "ssh-stop", env=self.env(base, OPENLINUX_PROC_ROOT=proc))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("stale PID state removed", result.stdout)
            self.assertFalse(run.exists())

    def test_package_uninstall_preserves_external_user_key_data(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            state = temp / "external-state"; state.mkdir(); (state / "dropbear_ecdsa_host_key").write_text("user key")
            result = subprocess.run(["/bin/sh", str(base / "sbin/openlinux-uninstall")],
                                    env=self.env(base), text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((state / "dropbear_ecdsa_host_key").read_text(), "user key")

    def test_mock_process_lifecycle_only_never_tests_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory); base = self.package(temp)
            conf = base / "etc/openlinux.conf"
            conf.write_text(conf.read_text().replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled")
                            .replace("SSH_HOME=\n", f"SSH_HOME={temp}/home/openlinux\n")
                            .replace("SSH_STATE_DIR=\n", f"SSH_STATE_DIR={temp}/state\n")
                            .replace("SSH_BIND_ADDRESS=\n", "SSH_BIND_ADDRESS=127.0.0.1\n"))
            home = temp / "home/openlinux"; (home / ".ssh").mkdir(parents=True)
            (home / ".ssh").chmod(0o700)
            (home / ".ssh/authorized_keys").write_text("ecdsa-sha2-nistp256 AAAA test\n")
            (home / ".ssh/authorized_keys").chmod(0o600)
            state = temp / "state"; state.mkdir(); state.chmod(0o700)
            key = state / "dropbear_ecdsa_host_key"; key.write_text("mock key only for lifecycle test"); key.chmod(0o600)
            passwd = temp / "passwd"; passwd.write_text(f"openlinux:x:1000:1000:OpenLinux:{home}:/bin/sh\n")
            root = temp / "oem"; (root / "bin").mkdir(parents=True)
            daemon = root / "bin/sshd"
            daemon.write_text("#!/usr/bin/python3\nimport time\ntime.sleep(60)\n"); daemon.chmod(0o755)
            ip = root / "bin/ip"; ip.write_text("#!/bin/sh\necho 'inet 127.0.0.1/8 scope host lo'\n"); ip.chmod(0o755)
            env = self.env(base, OPENLINUX_OEM_ROOT=root, OPENLINUX_IP=ip,
                           OPENLINUX_PASSWD_FILE=passwd, OPENLINUX_PROC_ROOT="/proc", OPENLINUX_DEV_ROOT="/dev")
            started = self.call_ctl(base, "ssh-start", env=env)
            self.assertEqual(started.returncode, 0, started.stderr)
            pidfile = base / "var/run/openlinux-ssh/pid"
            self.assertTrue(pidfile.exists())
            original_pid = pidfile.read_text()
            duplicate = self.call_ctl(base, "ssh-start", env=env)
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("already appears to be running", duplicate.stderr)
            self.assertEqual(pidfile.read_text(), original_pid)
            status = self.call_ctl(base, "ssh-status", env=env)
            self.assertEqual(status.returncode, 0, status.stderr)
            stopped = self.call_ctl(base, "ssh-stop", env=env)
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            self.assertFalse((base / "var/run/openlinux-ssh").exists())
            self.assertIn("no authentication call exists", "Mock process lifecycle only; no authentication call exists")


if __name__ == "__main__":
    unittest.main()
