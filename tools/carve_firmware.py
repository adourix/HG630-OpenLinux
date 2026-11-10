#!/usr/bin/env python3
"""Carve validated SquashFS and legacy uImage components from an OEM image."""
import argparse, hashlib, json, struct, zlib
from pathlib import Path
UIMAGE=bytes.fromhex("27051956"); SQUASH=b"hsqs"
def crc32(data): return zlib.crc32(data)&0xffffffff
def carve(src,out):
 data=src.read_bytes(); out.mkdir(parents=True,exist_ok=True); fs_off=data.find(SQUASH)
 if fs_off<0 or fs_off+96>len(data): raise ValueError("SquashFS superblock missing/truncated")
 sb=struct.unpack_from("<5I6H2Q5Q",data,fs_off); magic,inodes,mtime,block,frags,comp,blog,flags,ids,major,minor,root,used,*_=sb
 if (major,minor)!=(4,0) or used<96 or fs_off+used>len(data): raise ValueError("Invalid/unsupported SquashFS superblock bounds/version")
 fs=data[fs_off:fs_off+used]; (out/"rootfs.squashfs").write_bytes(fs)
 uoff=data.find(UIMAGE)
 if uoff<0 or uoff+64>len(data): raise ValueError("uImage header missing/truncated")
 fields=struct.unpack(">7I4B32s",data[uoff:uoff+64]); magic,hcrc,ts,size,load,entry,dcrc,osid,arch,typ,compression,name=fields
 header=bytearray(data[uoff:uoff+64]); header[4:8]=bytes(4); end=uoff+64+size
 if end>len(data): raise ValueError("uImage payload out of bounds")
 payload=data[uoff+64:end]; hok=crc32(header)==hcrc; dok=crc32(payload)==dcrc
 if not hok or not dok: raise ValueError(f"uImage CRC invalid: header={hok}, data={dok}")
 (out/"kernel.uimage").write_bytes(data[uoff:end]); (out/"kernel.payload.lzma").write_bytes(payload)
 report={"source":src.name,"source_size":len(data),"source_sha256":hashlib.sha256(data).hexdigest(),"squashfs":{"offset":fs_off,"size":used,"end":fs_off+used,"version":f"{major}.{minor}","inodes":inodes,"block_size":block,"compression_id":comp,"sha256":hashlib.sha256(fs).hexdigest()},"uimage":{"offset":uoff,"size":end-uoff,"payload_size":size,"load":f"0x{load:08x}","entry":f"0x{entry:08x}","arch_id":arch,"type_id":typ,"compression_id":compression,"name":name.split(bytes(1),1)[0].decode("ascii","replace"),"header_crc_valid":hok,"data_crc_valid":dok},"gap_between_squashfs_and_kernel":uoff-(fs_off+used)}
 (out/"carve-report.json").write_text(json.dumps(report,indent=2)+"\n"); return report
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("firmware",type=Path); p.add_argument("-o","--output",type=Path,default=Path("artifacts/carved")); a=p.parse_args(); print(json.dumps(carve(a.firmware,a.output),indent=2))
if __name__=="__main__": main()
