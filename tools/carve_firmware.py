#!/usr/bin/env python3
"""Carve validated SquashFS and legacy uImage components from an OEM image.
Read-only with respect to the input. Outputs are research artifacts, not flash images.
"""
from __future__ import annotations
import argparse, hashlib, json, struct, zlib
from pathlib import Path

UIMAGE = b'\\x27\\x05\\x19\\x56'
SQUASH = b'hsqs'

def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xffffffff

def carve(src: Path, out: Path) -> dict:
    data = src.read_bytes()
    out.mkdir(parents=True, exist_ok=True)
    fs_off = data.find(SQUASH)
    if fs_off < 0 or fs_off + 96 > len(data):
        raise ValueError('SquashFS superblock not found or truncated')
    sb = struct.unpack_from('<5I6H2Q5Q', data, fs_off)
    magic, inode_count, mkfs_time, block_size, fragments, comp, block_log, flags, ids, major, minor, root_inode, used, *_ = sb
    if (major, minor) != (4, 0):
        raise ValueError(f'Expected SquashFS 4.0, got {major}.{minor}')
    if used < 96 or fs_off + used > len(data):
        raise ValueError('SquashFS bytes_used is outside input bounds')
    fs = data[fs_off:fs_off + used]
    fs_path = out / 'rootfs.squashfs'
    fs_path.write_bytes(fs)

    uoff = data.find(UIMAGE)
    if uoff < 0 or uoff + 64 > len(data):
        raise ValueError('uImage header not found or truncated')
    fields = struct.unpack('>7I4B32s', data[uoff:uoff+64])
    magic_i, hcrc, timestamp, size, load, entry, dcrc, osid, arch, typ, compression, name = fields
    header = bytearray(data[uoff:uoff+64]); header[4:8] = b'\\0'*4
    start, end = uoff+64, uoff+64+size
    if end > len(data):
        raise ValueError('uImage payload exceeds input bounds')
    payload = data[start:end]
    header_ok, data_ok = crc32(header) == hcrc, crc32(payload) == dcrc
    if not header_ok or not data_ok:
        raise ValueError(f'uImage CRC failure: header={header_ok}, data={data_ok}')
    kernel_path = out / 'kernel.uimage'
    kernel_path.write_bytes(data[uoff:end])
    payload_path = out / 'kernel.payload.lzma'
    payload_path.write_bytes(payload)
    report = {
      'source': src.name, 'source_size': len(data), 'source_sha256': hashlib.sha256(data).hexdigest(),
      'squashfs': {'offset': fs_off, 'size': used, 'end': fs_off+used, 'version': f'{major}.{minor}', 'inodes': inode_count, 'block_size': block_size, 'compression_id': comp, 'sha256': hashlib.sha256(fs).hexdigest(), 'output': fs_path.name},
      'uimage': {'offset': uoff, 'size': end-uoff, 'payload_size': size, 'load': f'0x{load:08x}', 'entry': f'0x{entry:08x}', 'arch_id': arch, 'type_id': typ, 'compression_id': compression, 'name': name.split(b'\\0',1)[0].decode('ascii','replace'), 'header_crc_valid': header_ok, 'data_crc_valid': data_ok, 'output': kernel_path.name, 'payload_output': payload_path.name},
      'gap_between_squashfs_and_kernel': uoff-(fs_off+used)
    }
    (out/'carve-report.json').write_text(json.dumps(report, indent=2)+'\\n')
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('firmware', type=Path); ap.add_argument('-o','--output',type=Path,default=Path('artifacts/carved'))
    a=ap.parse_args(); print(json.dumps(carve(a.firmware,a.output),indent=2))
if __name__=='__main__': main()
