#!/usr/bin/env python3
"""Read-only byte-level inventory of the HG630 V2 update image."""
from __future__ import annotations
import argparse, hashlib, json, re, struct, zlib
from pathlib import Path

FIELD_RE = re.compile(rb'(?m)^([a-zA-Z_]+)=([^\r\n\x00]+)')
KNOWN = {b'board_id', b'main_offset', b'main_size', b'slave_offset', b'slave_size'}
SQUASH = b'hsqs'; UIMAGE = b'\x27\x05\x19\x56'; HEADER_SIZE = 0x600

def number(raw: bytes):
    s = raw.decode('ascii')
    if re.fullmatch(r'0[xX][0-9a-fA-F]+', s): return int(s, 16), 'hexadecimal'
    if re.fullmatch(r'[0-9]+', s): return int(s, 10), 'decimal'
    return None, 'unknown/ambiguous'

def positions(data: bytes, needle: bytes):
    out=[]; i=0
    while (i:=data.find(needle,i))>=0: out.append(i); i+=1
    return out

def parse(data: bytes, name='<memory>') -> dict:
    fields=[]
    for m in FIELD_RE.finditer(data[:HEADER_SIZE]):
        key, value=m.group(1),m.group(2)
        if key not in KNOWN: continue
        value_num, radix=number(value)
        fields.append({'key':key.decode(),'value_raw':value.decode('ascii','replace'), 'value':value_num,
          'radix':radix,'key_offset':m.start(1),'value_offset':m.start(2),
          'raw_record_hex':data[max(0,m.start()-16):min(HEADER_SIZE,m.end()+16)].hex(),
          'raw_record_text':data[max(0,m.start()-16):min(HEADER_SIZE,m.end()+16)].decode('latin1')})
    bykey={}
    for f in fields: bykey.setdefault(f['key'],[]).append(f)
    issues=[]; regions=[]
    for group in re.finditer(rb'(?m)^\[(\d+)\]',data[:HEADER_SIZE]):
        nxt=re.search(rb'\n\[\d+\]',data[group.end():HEADER_SIZE]); stop=HEADER_SIZE if nxt is None else group.end()+nxt.start()+1
        block=data[group.start():stop]
        vals={m.group(1).decode():m.group(2) for m in FIELD_RE.finditer(block)}
        for prefix in ('main','slave'):
            ok=prefix+'_offset' in vals and prefix+'_size' in vals
            if not ok: continue
            off,orad=number(vals[prefix+'_offset']); size,srad=number(vals[prefix+'_size'])
            r={'section':group.group(1).decode(),'kind':prefix,'offset':off,'size':size,'offset_radix':orad,'size_radix':srad,'semantics':'UNKNOWN; metadata label only','valid':False}
            if off is None or size is None: issues.append(f"invalid numeric region in [{r['section']}] {prefix}")
            else:
                end=off+size; r.update(end=end,within_file=(off<=len(data) and end<=len(data)),valid=(off<=len(data) and end<=len(data)))
                if not r['valid']: issues.append(f"out-of-range region [{r['section']}] {prefix}: {off:#x}+{size:#x} exceeds file")
            r['raw_section_hex']=block.hex(); regions.append(r)
    for key in sorted(KNOWN):
        if key.decode() not in bykey: issues.append('missing field '+key.decode())
    ranges=[r for r in regions if r.get('end') is not None and r['size']]
    for i,a in enumerate(ranges):
        for b in ranges[i+1:]:
            if a['offset']<b['end'] and b['offset']<a['end']:
                issues.append(f"overlap: [{a['section']}] {a['kind']} and [{b['section']}] {b['kind']}")
    squash=[]
    for off in positions(data,SQUASH):
        item={'offset':off}
        if off+96>len(data): item['error']='truncated superblock'
        else:
            f=struct.unpack_from('<5I6H2Q5Q',data,off); used=f[12]
            item.update(version=f'{f[9]}.{f[10]}',inode_count=f[1],compression_id=f[5],block_size=f[3],bytes_used=used,end=off+used,within_file=off+used<=len(data),superblock_hex=data[off:off+96].hex())
            if off+used>len(data): item['error']='filesystem extends beyond file'; issues.append(f'SquashFS at {off:#x} extends beyond file')
        squash.append(item)
    uimages=[]
    for off in positions(data,UIMAGE):
        x={'offset':off}
        if off+64>len(data): x['error']='truncated uImage header'
        else:
            vals=struct.unpack_from('>7I4B32s',data,off); size=vals[3]; end=off+64+size
            hdr=bytearray(data[off:off+64]); hdr[4:8]=b'\0'*4
            x.update(header_size=64,payload_size=size,end=end,within_file=end<=len(data),header_crc_stored=f'{vals[1]:08x}',data_crc_stored=f'{vals[6]:08x}',header_crc_valid=(zlib.crc32(hdr)&0xffffffff)==vals[1],data_crc_valid=end<=len(data) and (zlib.crc32(data[off+64:end])&0xffffffff)==vals[6],load_address=vals[4],entry_address=vals[5],name=vals[11].split(b'\0')[0].decode('ascii','replace'),header_hex=data[off:off+64].hex())
            if not x['within_file']: x['error']='payload extends beyond file'
        uimages.append(x)
    return {'file':name,'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
      'header':{'range':[0,HEADER_SIZE],'hex':data[:HEADER_SIZE].hex(),'latin1':data[:HEADER_SIZE].decode('latin1')},
      'metadata':{'field_records':fields,'regions':regions,'region_semantics':'UNKNOWN; not established as physical flash addresses'},
      'signatures':{'squashfs':squash,'uimage':uimages},'issues':issues,'structurally_valid':not issues and all(x.get('within_file') and x.get('header_crc_valid') and x.get('data_crc_valid') for x in uimages) and all(x.get('within_file') for x in squash)}

def inspect(path: Path): return parse(path.read_bytes(),str(path))
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('firmware',type=Path); p.add_argument('--json',nargs='?',const='-',default='-'); a=p.parse_args()
    if not a.firmware.is_file(): p.error(f'firmware not found: {a.firmware}')
    report=inspect(a.firmware); encoded=json.dumps(report,indent=2)+'\n'
    if a.json=='-': print(encoded,end='')
    else: Path(a.json).parent.mkdir(parents=True,exist_ok=True); Path(a.json).write_text(encoded)
    return 0 if report['structurally_valid'] else 1
if __name__=='__main__': raise SystemExit(main())
