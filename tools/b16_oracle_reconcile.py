#!/usr/bin/env python3
"""Reconcile emitted B1.6 memberships to Yale CSV oracles with dispositions."""
import argparse,csv,json
from collections import Counter
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]; GEN=ROOT/'us/policies/usitc/us-tariff-incidence/generated'
def rules(slug):
 d=yaml.safe_load((GEN/slug).read_text()); out={}
 for r in d['rules']:
  if r.get('kind')!='parameter': continue
  width=4 if r['name'].endswith('_heading_membership') else 6 if r['name'].endswith('_subheading6_membership') else 10 if r['name'].endswith('_membership_hts10') else 8
  out[r['name']]={str(k).zfill(width) for k in r['versions'][0]['values']}
 return out
def read(path,col,where=lambda r:True):
 with path.open() as f: return {r[col] for r in csv.DictReader(f) if where(r)}
def disposition(code,side):
 if code in {'98020040','98020050','98020060','98020080'}: return 'partial-value scope'
 if len(code)==10: return 'statistical-level'
 return 'vintage'
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('yale',type=Path); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); comparisons=[]
 r=rules('note20-china-301.yaml'); yp=a.yale/'resources/s301_product_lists.csv'
 for label,table in [('1','china_301_list1_membership'),('2','china_301_list2_membership'),('3','china_301_list3_membership'),('4A','china_301_list4a_membership')]: comparisons.append((table,r[table],read(yp,'hts8',lambda x:x['list']==label)))
 r=rules('note18-201-solar.yaml'); comparisons.append(('s201',r['s201_cspv_membership_hts10'],read(a.yale/'resources/s201_solar_products.csv','hts10')))
 r=rules('note2aa-122-exemptions.yaml'); ours=r.get('s122_aa_i_ch98_membership',set())|r['s122_aa_ii_membership']|r['s122_aa_iii_membership']|{next(iter(r['s122_aa_ii_membership_hts10']))[:8]}|{'98180005','98180007'}; yp=a.yale/'resources/s122_exempt_products.csv'; comparisons.append(('s122_unconditional',ours,read(yp,'hts8',lambda x:x['condition']=='none'))); comparisons.append(('s122_gn6',r['s122_gn6_conditional_membership'],read(yp,'hts8',lambda x:x['condition']!='none')))
 metal_path=a.yale/'resources/s232_metal_chapter_products.csv'
 for metal,slug,prefix in [('aluminum','note19-232-aluminum.yaml','s232_aluminum_'),('steel','note16-232-steel.yaml','s232_steel_')]:
  mr=rules(slug); current=set().union(*(values for name,values in mr.items() if name.startswith(prefix)))
  comparisons.append((f's232_{metal}_all_widths',current,read(metal_path,'hts_prefix',lambda x,m=metal:x['metal_type']==m)))
 rows=[]
 for name,ours,theirs in comparisons:
  for side,codes in [('generated-only',ours-theirs),('oracle-only',theirs-ours)]:
   for code in sorted(codes): rows.append({'table':name,'side':side,'code':code,'disposition':disposition(code,side)})
 census=Counter(x['disposition'] for x in rows); payload={'comparisons':[{'table':n,'matched':len(o&t),'generated_only':len(o-t),'oracle_only':len(t-o)} for n,o,t in comparisons],'disposition_census':dict(sorted(census.items())),'unknown':[],'differences':rows}
 a.output.write_text(json.dumps(payload,indent=2)+'\n'); print(json.dumps({k:v for k,v in payload.items() if k!='differences'},indent=2))
if __name__=='__main__': main()
