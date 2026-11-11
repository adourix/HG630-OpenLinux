# Tests

The firmware inspector is designed to be testable without physical hardware.

The suite covers uImage parsing and CRC validation, bounded signature scanning,
malformed/truncated image rejection, ARM ABI evidence, and RootFS build safety.

RootFS tests specifically exercise hardlink, symlink, FIFO, device-safe copying,
ownership/mode preservation, unsupported socket rejection, source-tree protection,
and a real extractable SquashFS build.
