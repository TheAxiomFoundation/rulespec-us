#!/usr/bin/env python3
"""Independent B1.6 extractor: regex over a concatenated page stream."""
import argparse,json,re,sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"us/policies/usitc/us-tariff-incidence/generated"
TOKEN=re.compile(r"(?<![\d.])(\d{4}\.\d{2}\.\d{2}(?:\d{2})?)(?![\d.])")
# Independently restated boundaries; no generator imports or shared functions.
BOUNDS={
"china_301_list1_membership":("(b) Heading 9903.88.01 applies","(c) For the purposes of heading 9903.88.02"),
"china_301_list2_membership":("(d) Heading 9903.88.02 applies","(e) For the purposes of heading 9903.88.03"),
"china_301_list3_membership":("(f) Heading 9903.88.03 applies","(g) For the purposes of heading 9903.88.04"),
"china_301_list4a_membership":("(s) Heading 9903.88.15 applies","(t) For the purposes of heading 9903.88.16"),
"s201_cspv_membership":("(c) (i) For the purposes of subheadings 9903.45.21","(ii) Subheadings 9903.45.21"),
"s122_aa_i_ch98_membership":("(aa) [Compiler’s note: Subdivisions (aa)(i)","(ii) As provided in heading 9903.03.03"),
"s122_aa_ii_membership":("(ii) As provided in heading 9903.03.03","(iii) As provided in heading 9903.03.04"),
"s122_aa_iii_membership":("(iii) As provided in heading 9903.03.04","(iv) As provided in heading 9903.03.05"),
"s122_gn6_conditional_membership":("(iv) As provided in heading 9903.03.05","(v) As provided in heading 9903.03.06"),
"s232_steel_primary_membership":("(iii) Articles of steel:","(iv) Derivative steel articles:"),
"s232_steel_derivative_legacy_membership":("(iv) Derivative steel articles:","(v) Articles of copper:"),
"s232_steel_derivative_april_membership":("(vii) Derivative steel articles:","(viii) Articles of copper:"),
"s232_steel_derivative_equipment_membership":("(x) Derivative steel articles:","(xi) Derivative steel articles:"),
"s232_steel_derivative_mobile_membership":("(xi) Derivative steel articles:","(d) Headings 9903.82.04"),
"s232_aluminum_primary_membership":("(b) The rates of duty set forth in heading 9903.85.01","(c) The Secretary of Commerce"),
"s232_aluminum_derivative_membership":("(j) The rates of duty set forth in heading 9903.85.07","(k) The rates of duty in heading 9903.85.08"),
}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("corpus",type=Path); ap.add_argument("--output",type=Path); a=ap.parse_args()
 rec=[]
 for raw in a.corpus.read_text().splitlines():
  d=json.loads(raw)
  if d.get('parent_citation_path')=='us/statute/hts/chapter-99': rec.append((int(d['metadata']['page_number']),d.get('body','')))
 stream='\n'.join(x[1] for x in sorted(rec)); report={}; failed=False
 generated={}
 for f in OUT.glob('*.yaml'):
  if f.name.endswith('.test.yaml'): continue
  for r in yaml.safe_load(f.read_text()).get('rules',[]):
   if r.get('kind')=='parameter' and 'membership' in r['name']: generated[r['name']]={str(k) for k in r['versions'][0]['values']}
 for name,(start,stop) in BOUNDS.items():
  lo=stream.find(start); hi=stream.find(stop,lo+len(start))
  if lo<0 or hi<0: report[name]={'error':'anchor absent'}; failed=True; continue
  codes={m.group(1).replace('.','') for m in TOKEN.finditer(stream,lo,hi) if not m.group(1).startswith('99')}
  if name=='s122_aa_i_ch98_membership': codes={c for c in codes if c.startswith('9818')}
  for width in (8,10):
   table=name+('_hts10' if width==10 else '')
   expected={str(int(c)) for c in codes if len(c)==width}; got=generated.get(table,set())
   if expected or got:
    report[table]={'expected':len(expected),'generated':len(got),'only_expected':sorted(expected-got),'only_generated':sorted(got-expected)}
    failed |= expected!=got
 text=json.dumps(report,indent=2)+"\n"; (a.output.write_text(text) if a.output else sys.stdout.write(text)); return int(failed)
if __name__=='__main__': raise SystemExit(main())
