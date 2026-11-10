import importlib.util
import struct
import zlib
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "firmware_inspect", Path(__file__).parents[1] / "tools" / "firmware_inspect.py"
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def make_uimage(payload: bytes, name: bytes = b"test-kernel") -> bytes:
    fields = [
        0x27051956, 0, 0, len(payload), 0x81208000, 0x81208000,
        zlib.crc32(payload) & 0xFFFFFFFF, 5, 2, 2, 3,
        name.ljust(32, b"\0")[:32],
    ]
    header = bytearray(struct.pack(">7I4B32s", *fields))
    fields[1] = zlib.crc32(header) & 0xFFFFFFFF
    return struct.pack(">7I4B32s", *fields) + payload


def test_uimage_crc_and_metadata():
    result = module.parse_uimage(make_uimage(b"HG630 test payload"), 0)
    assert result["header_crc_valid"]
    assert result["data_crc_valid"]
    assert result["payload_size"] == len(b"HG630 test payload")
    assert result["name"] == "test-kernel"


def test_truncated_uimage_rejected():
    try:
        module.parse_uimage(make_uimage(b"0123456789")[:-3], 0)
    except ValueError as exc:
        assert "extends beyond" in str(exc)
    else:
        raise AssertionError("truncated payload was accepted")


def test_signature_scan():
    data = b"abc" + module.SQUASHFS_MAGIC + b"xyz" + module.SQUASHFS_MAGIC
    assert module.find_all(data, module.SQUASHFS_MAGIC) == [3, 10]
