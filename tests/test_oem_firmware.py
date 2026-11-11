import struct, unittest, zlib
from pathlib import Path
from tools.inspect_firmware import parse
from tools.validate_firmware import validate

def make_firmware(meta=None):
    meta=meta or b'[global]\nboard_id=1212\nmain_offset=0x0\nmain_size=0x1000\nslave_offset=0x1000\nslave_size=0x1000\n'
    fs=bytearray(96);struct.pack_into('<5I6H2Q5Q',fs,0,0x73717368,1,0,4096,0,4,12,0,1,4,0,0,96,0,0,0,0,0)
    payload=b'fixture'; f=[0x27051956,0,0,len(payload),0,0,zlib.crc32(payload)&0xffffffff,5,2,2,3,b'fixture']
    h=bytearray(struct.pack('>7I4B32s',*f)); f[1]=zlib.crc32(h)&0xffffffff
    u=struct.pack('>7I4B32s',*f)+payload
    return meta+bytes(fs)+u

class OEMParserTests(unittest.TestCase):
 def test_valid_metadata_and_embedded_structures(self):
  r=parse(make_firmware());self.assertEqual(r['metadata']['field_records'][0]['value'],1212);self.assertTrue(r['structurally_valid'])
 def test_missing_fields_reported(self):
  r=parse(make_firmware(b'board_id=12\n'));self.assertTrue(any('missing field' in x for x in r['issues']))
 def test_invalid_numeric_value(self):
  r=parse(make_firmware(b'[1]\nboard_id=12\nmain_offset=xx\nmain_size=3\nslave_offset=0\nslave_size=2\n'));self.assertTrue(any('invalid numeric' in x for x in r['issues']))
 def test_out_of_range(self):
  r=parse(make_firmware(b'[1]\nboard_id=12\nmain_offset=0xfffffff\nmain_size=3\nslave_offset=0\nslave_size=2\n'));self.assertTrue(any('out-of-range' in x for x in r['issues']))
 def test_overlap(self):
  r=parse(make_firmware(b'[1]\nboard_id=12\nmain_offset=0x0\nmain_size=0x200\nslave_offset=0x100\nslave_size=0x200\n'));self.assertTrue(any('overlap' in x for x in r['issues']))
 def test_truncation_and_corrupt_crc(self):
  b=bytearray(make_firmware());self.assertFalse(parse(bytes(b[:-1]))['signatures']['uimage'][0]['within_file']);b[-1]^=1;self.assertFalse(parse(bytes(b))['signatures']['uimage'][0]['data_crc_valid'])
 def test_corrupt_squashfs_magic_not_found(self):
  b=bytearray(make_firmware());i=b.find(b'hsqs');b[i]=0;self.assertFalse(parse(bytes(b))['signatures']['squashfs'])

if __name__=='__main__':unittest.main()
