import tempfile
import unittest
from pathlib import Path

from tools.build_qemu_image import validate_inputs


class QemuImageTests(unittest.TestCase):
    def test_input_validation_requires_elf_and_shell(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            kernel = root / "zImage"
            busybox = root / "busybox"
            ctl = root / "openlinuxctl"
            kernel.write_bytes(b"kernel")
            busybox.write_bytes(b"not-elf")
            ctl.write_text("#!/bin/sh\n")
            with self.assertRaisesRegex(ValueError, "not ELF"):
                validate_inputs(kernel, busybox, ctl)

    def test_input_validation_accepts_static_elf_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = [root / name for name in ("zImage", "busybox", "openlinuxctl")]
            paths[0].write_bytes(b"kernel")
            paths[1].write_bytes(b"\x7fELFfixture")
            paths[2].write_text("#!/bin/sh\n")
            validate_inputs(*paths)


if __name__ == "__main__":
    unittest.main()
