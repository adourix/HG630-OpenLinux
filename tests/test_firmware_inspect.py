import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "firmware_inspect", Path(__file__).parents[1] / "tools" / "firmware_inspect.py"
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def make_uimage(payload: bytes, name: bytes = b"test-kernel") -> bytes:
    import struct
    import zlib

    fields = [
        0x27051956, 0, 0, len(payload), 0x81208000, 0x81208000,
        zlib.crc32(payload) & 0xFFFFFFFF, 5, 2, 2, 3,
        name.ljust(32, b"\0")[:32],
    ]
    header = bytearray(struct.pack(">7I4B32s", *fields))
    fields[1] = zlib.crc32(header) & 0xFFFFFFFF
    return struct.pack(">7I4B32s", *fields) + payload


def test_uimage_crc_and_metadata():
    payload = b"HG630 test payload"
    image = make_uimage(payload)
    result = module.parse_uimage(image, 0)
    assert result["header_crc_valid"] is True
    assert result["data_crc_valid"] is True
    assert result["image_size"] == len(payload)
    assert result["name"] == "test-kernel"


def test_truncated_payload_is_rejected():
    image = make_uimage(b"0123456789")[:-3]
    result = module.parse_uimage(image, 0)
    assert result["payload_bounds_valid"] is False
    assert result["data_crc_valid"] is False


def test_signature_scan_finds_all_offsets():
    data = b"abc" + module.SQUASHFS_LE_MAGIC + b"xyz" + module.SQUASHFS_LE_MAGIC
    assert module.find_all(data, module.SQUASHFS_LE_MAGIC) == [3, 10]
