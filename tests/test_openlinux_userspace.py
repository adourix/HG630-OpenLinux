import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTL = ROOT / "build/experimental/openlinux-overlay/rootfs/usr/sbin/openlinuxctl"
BASE_CONFIG = """SERVICE_NETWORK=disabled
SERVICE_DNS=disabled
SERVICE_SSH=disabled
SERVICE_FIREWALL=disabled
SERVICE_WEB=disabled
NETWORK_LAN_IFACE=br0
NETWORK_LAN_MODE=static
NETWORK_LAN_ADDRESS=192.168.1.1
NETWORK_LAN_NETMASK=255.255.255.0
NETWORK_WAN_IFACE=eth0
NETWORK_WAN_MODE=dhcp
DHCP_ENABLE=enabled
DHCP_START=192.168.1.100
DHCP_END=192.168.1.200
DHCP_LEASE_SECONDS=86400
DNS_DOMAIN=lan
FIREWALL_BACKEND=auto
SSH_ENABLE=disabled
SSH_BIND=192.168.1.1
LOG_LEVEL=info
LOG_MAX_BYTES=128
"""


class OpenLinuxUserspaceTests(unittest.TestCase):
    def run_ctl(self, root: Path, *args: str):
        env = os.environ.copy()
        env["OPENLINUX_ROOT"] = str(root)
        env["OPENLINUX_LOG"] = str(root / "var/log/test.log")
        return subprocess.run(["sh", str(CTL), *args], env=env, text=True, capture_output=True, check=False)

    def write_config(self, root: Path, text: str = BASE_CONFIG):
        config = root / "etc/openlinux/openlinux.conf"
        config.parent.mkdir(parents=True)
        config.write_text(text)

    def test_valid_config_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root)
            result = self.run_ctl(root, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("network=disabled", result.stdout)
            self.assertIn("ssh=disabled", result.stdout)

    def test_invalid_config_and_interface_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root, BASE_CONFIG.replace("NETWORK_LAN_IFACE=br0", "NETWORK_LAN_IFACE=bad iface"))
            result = self.run_ctl(root, "network", "validate")
            self.assertNotEqual(result.returncode, 0)

    def test_dhcp_generation_is_openlinux_owned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root)
            result = self.run_ctl(root, "dhcp", "validate")
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = root / "etc/openlinux/generated/dnsmasq.conf"
            self.assertTrue(generated.exists())
            self.assertIn("dhcp-range=192.168.1.100,192.168.1.200,86400s", generated.read_text())

    def test_dhcp_static_leases_and_local_hosts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root)
            (root / "etc/openlinux/dhcp.leases").write_text("aa:bb:cc:dd:ee:ff,192.168.1.20,printer\n")
            (root / "etc/openlinux/hosts").write_text("192.168.1.21 camera\n")
            result = self.run_ctl(root, "dhcp", "validate")
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = (root / "etc/openlinux/generated/dnsmasq.conf").read_text()
            self.assertIn("dhcp-host=aa:bb:cc:dd:ee:ff 192.168.1.20 printer", generated)
            self.assertIn("address=/camera/192.168.1.21", generated)

    def test_firewall_rules_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root)
            rules = root / "etc/openlinux/firewall.rules"
            rules.parent.mkdir(parents=True, exist_ok=True)
            rules.write_text("allow tcp 22\n")
            result = self.run_ctl(root, "firewall", "validate")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("dry-run", result.stdout)

    def test_ssh_validation_does_not_enable_service(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root, BASE_CONFIG.replace("SSH_ENABLE=disabled", "SSH_ENABLE=enabled"))
            binary = root / "bin/sshd"
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            result = self.run_ctl(root, "ssh", "validate")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("remains disabled", result.stdout)

    def test_monitor_reads_fake_proc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root)
            proc = root / "proc"
            proc.mkdir()
            (proc / "uptime").write_text("12.00 4.00\n")
            (proc / "loadavg").write_text("0.01 0.02 0.03 1/2 3\n")
            (proc / "meminfo").write_text("MemTotal: 100 kB\n")
            (proc / "mounts").write_text("rootfs / rootfs rw 0 0\n")
            result = self.run_ctl(root, "monitor")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("12.00", result.stdout)
            self.assertIn("MemTotal", result.stdout)

    def test_dry_run_never_executes_network_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root)
            result = self.run_ctl(root, "network", "apply", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN", result.stdout)

    def test_boot_logs_disabled_services(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_config(root)
            result = self.run_ctl(root, "boot")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("network disabled", (root / "var/log/test.log").read_text())


if __name__ == "__main__":
    unittest.main()
