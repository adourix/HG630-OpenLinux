#!/usr/bin/env python3
"""Classify OEM metadata extents without asserting a physical flash map."""
import argparse, json
from pathlib import Path

def analyze(report: dict, capacities=(0x1000000,)) -> dict:
    regs=report.get('metadata',{}).get('regions',[])
    proposed=[]; errors=[]
    for r in regs:
        start=r.get('offset'); size=r.get('size'); end=r.get('end')
        if start is None or size is None: errors.append(f"unparsed region {r.get('section')} {r.get('kind')}"); continue
        proposed.append({'section':r['section'],'kind':r['kind'],'start':start,'end':end,'size':size,'evidence_source':'OEM metadata text in firmware header','confidence':'LOW','status':'INFERRED','physical_flash_verified':False,'semantics':'UNKNOWN'})
    ordered=sorted((x for x in proposed if x['size']>0),key=lambda x:x['start'])
    for a,b in zip(ordered,ordered[1:]):
        if b['start'] < a['end'] and not (a['start']==b['start'] and a['end']==b['end']):
            errors.append(f"overlap {a['section']}:{a['kind']} with {b['section']}:{b['kind']}")
    max_end=max((x['end'] for x in proposed if x['end'] is not None),default=0)
    for cap in capacities:
        if max_end>cap: errors.append(f"metadata end {max_end:#x} exceeds candidate capacity {cap:#x}")
    return {'capacity_candidates':[{'bytes':c,'hex':hex(c),'covers_metadata_extent':max_end<=c} for c in capacities], 'metadata_extent_end':max_end,'regions':proposed,'errors':errors,'layout_verified':False,'interpretation':'Metadata extents are not proven physical flash partitions.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('metadata_json',type=Path);p.add_argument('--capacity',action='append',type=lambda s:int(s,0),default=[]);p.add_argument('--output',type=Path);a=p.parse_args()
 report=analyze(json.loads(a.metadata_json.read_text()),a.capacity or (0x1000000,)); out=json.dumps(report,indent=2)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(out)
 else:print(out,end='')
 return 1 if any(e.startswith('overlap') for e in report['errors']) else 0
if __name__=='__main__':raise SystemExit(main())
