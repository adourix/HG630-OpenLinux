import struct, tempfile, unittest, zlib
from pathlib import Path
from tools.carve_firmware import carve

def make_image():
    payload=b'kernel-payload'
    vals=[0x27051956,0,0,len(payload),0x81208000,0x81208000,zlib.crc32(payload)&0xffffffff,5,2,2,3,b'Linux-test']
    h=bytearray(struct.pack('>7I4B32s',*vals)); vals[1]=zlib.crc32(h)&0xffffffff
    u=struct.pack('>7I4B32s',*vals)+payload
    # minimal 96-byte SquashFS superblock; bytes_used=96
    sb=struct.pack('<5I6H2Q5Q',0x73717368,1,0,4096,0,4,12,0,1,4,0,0,96,0,0,0,0,0)
    return b'PREFIX'+sb+b'GAP'+u

class CarveTests(unittest.TestCase):
    def test_carves_and_validates_uimage(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'in.bin'; out=Path(td)/'out'; src.write_bytes(make_image())
            report=carve(src,out)
            self.assertTrue(report['uimage']['header_crc_valid'])
            self.assertTrue(report['uimage']['data_crc_valid'])
            self.assertEqual((out/'rootfs.squashfs').stat().st_size,96)
            self.assertTrue((out/'kernel.uimage').exists())
if __name__=='__main__': unittest.main()
