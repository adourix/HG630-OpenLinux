import unittest
from tools.analyze_flash_layout import analyze

def region(section,start,size,kind='main'):
 return {'section':str(section),'kind':kind,'offset':start,'size':size,'end':start+size}

class FlashLayoutTests(unittest.TestCase):
 def run_regions(self,rs,caps=(0x10000,)):
  return analyze({'metadata':{'regions':rs}},caps)
 def test_contiguous(self):
  r=self.run_regions([region(1,0,0x1000),region(2,0x1000,0x1000)]);self.assertFalse(any(e.startswith('overlap') for e in r['errors']))
 def test_gap_allowed(self):
  r=self.run_regions([region(1,0,0x1000),region(2,0x2000,0x1000)]);self.assertFalse(r['errors'])
 def test_overlap_rejected(self):
  r=self.run_regions([region(1,0,0x2000),region(2,0x1000,0x1000)]);self.assertTrue(any(e.startswith('overlap') for e in r['errors']))
 def test_capacity_boundary(self):
  r=self.run_regions([region(1,0xf000,0x2000)],(0x10000,0x20000));self.assertFalse(r['capacity_candidates'][0]['covers_metadata_extent']);self.assertTrue(r['capacity_candidates'][1]['covers_metadata_extent'])
 def test_unknown_fields_semantics_remain_unknown(self):
  r=self.run_regions([region(1,0,0x1000)]);self.assertEqual(r['regions'][0]['status'],'INFERRED');self.assertFalse(r['regions'][0]['physical_flash_verified'])

if __name__=='__main__':unittest.main()
