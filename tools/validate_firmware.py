#!/usr/bin/env python3
"""Independently validate known HG630 embedded image checks."""
import argparse, hashlib, json
from pathlib import Path
try:
    from tools.inspect_firmware import inspect
except ModuleNotFoundError:
    from inspect_firmware import inspect

EXPECTED_SHA256='d5fb45d7b8e8fd399bbbfd903a31a0d1026ee8375455d32028129bd04ff2b222'

def validate(path: Path, expected_hash: str|None=None):
    raw=path.read_bytes(); report=inspect(path); checks=[]
    checks.append({'name':'sha256','valid':expected_hash is None or hashlib.sha256(raw).hexdigest()==expected_hash,'expected':expected_hash,'actual':hashlib.sha256(raw).hexdigest()})
    for i,s in enumerate(report['signatures']['squashfs']):
        checks.append({'name':f'squashfs[{i}] superblock/bounds','valid':'error' not in s and s.get('within_file',False) and s.get('version')=='4.0'})
    for i,u in enumerate(report['signatures']['uimage']):
        checks.append({'name':f'uimage[{i}] bounds/header CRC/data CRC','valid':'error' not in u and u.get('within_file',False) and u.get('header_crc_valid',False) and u.get('data_crc_valid',False)})
    checks.append({'name':'metadata syntax and bounds','valid':not any('missing field' in e or 'invalid numeric' in e or 'out-of-range' in e for e in report['issues']),'issues':report['issues']})
    checks.append({'name':'known embedded signatures present','valid':bool(report['signatures']['squashfs']) and bool(report['signatures']['uimage'])})
    return {'file':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,'valid':all(c['valid'] for c in checks)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('firmware',type=Path);p.add_argument('--expected-sha256',default=EXPECTED_SHA256);a=p.parse_args()
 try:r=validate(a.firmware,a.expected_sha256)
 except (OSError,ValueError) as e: print(json.dumps({'valid':False,'error':str(e)}));return 2
 print(json.dumps(r,indent=2));return 0 if r['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
