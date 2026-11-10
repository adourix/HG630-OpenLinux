#!/usr/bin/env python3
"""Inventory an already-extracted rootfs for DSL/WLAN/kernel dependencies."""
import argparse, hashlib, json, re
from pathlib import Path
KEYWORDS = re.compile(r'(dsl|adsl|vdsl|bcm|broadcom|6316|6362|atm|ptm|xdsl|wan|wlan|wifi|wireless|d11|b43|brcm|kmod|kernel|modem)', re.I)
ELF = b'\\x7fELF'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def scan(root: Path):
    out={'root':str(root),'files':0,'elf_files':[],'kernel_modules':[],'keyword_paths':[],'firmware_candidates':[]}
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        out['files']+=1; rel=str(p.relative_to(root))
        try:
            with p.open('rb') as f: head=f.read(64)
        except OSError: continue
        if head.startswith(ELF):
            cls={1:'ELF32',2:'ELF64'}.get(head[4],'unknown'); endian={1:'little',2:'big'}.get(head[5],'unknown')
            machine=int.from_bytes(head[18:20],endian) if len(head)>=20 and endian!='unknown' else None
            out['elf_files'].append({'path':rel,'class':cls,'endian':endian,'machine_id':machine,'size':p.stat().st_size,'sha256':sha(p)})
        low=rel.lower()
        if low.endswith('.ko') or '/modules/' in '/'+low: out['kernel_modules'].append(rel)
        if KEYWORDS.search(rel): out['keyword_paths'].append(rel)
        if '/firmware/' in '/'+low or low.endswith(('.bin','.fw','.dat')): out['firmware_candidates'].append(rel)
    return out
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('rootfs',type=Path); ap.add_argument('-o','--output',type=Path,default=Path('artifacts/rootfs-inventory.json')); a=ap.parse_args()
    if not a.rootfs.is_dir(): ap.error('rootfs directory does not exist')
    result=scan(a.rootfs); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\\n'); print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in result.items()},indent=2))
if __name__=='__main__': main()
