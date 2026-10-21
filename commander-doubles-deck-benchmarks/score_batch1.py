#!/usr/bin/env python3
"""Offline Batch1 scorer: frozen effective prices; imports text or Oracle-keyed JSON."""
import argparse,csv,hashlib,json,pathlib,sys
from pricing import HERE,BASE,load
from audit_backend import load_deck

def frozen_backend():
 b,_=load();path=HERE/'batch1/price_snapshot.csv';p=json.loads((HERE/'batch1/provenance.json').read_text())
 if hashlib.sha256((BASE/'data/oracle_current.jsonl.gz').read_bytes()).hexdigest()!=p['pinned_oracle_sha256']:raise ValueError('Oracle dependency differs from frozen source; explicit update required')
 if hashlib.sha256(path.read_bytes()).hexdigest()!=p['price_snapshot_sha256']:raise ValueError('Frozen snapshot checksum mismatch; explicit regeneration/review required')
 for r in csv.DictReader(path.read_text().splitlines()):
  if b.card_price(r['oracle_id'],'main')!=int(r['main_deck_points']):raise ValueError('Dependency price differs from frozen main price')
  if r['command_zone_points'] and b.card_price(r['oracle_id'],'commanders')!=int(r['command_zone_points']):raise ValueError('Dependency price differs from frozen CZ price')
 return b,p

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('deck_a');p.add_argument('--deck-b');p.add_argument('--export');p.add_argument('--team-cap',type=int,default=120);p.add_argument('--individual-cap',type=int,default=72);p.add_argument('--reference',type=int,default=60);p.add_argument('--transfer-fraction',type=float,default=.2);p.add_argument('--summary',action='store_true');a=p.parse_args()
 try:
  b,meta=frozen_backend();d=load_deck(a.deck_a)
  if a.deck_b:r=b.team(d,load_deck(a.deck_b),a.team_cap,a.individual_cap,a.reference,a.transfer_fraction)
  else:
   if a.individual_cap<0:raise ValueError('Negative individual cap')
   b.config['individual_cap']=a.individual_cap;r=b.score(d)
  r['price_snapshot_sha256']=meta['price_snapshot_sha256'];r['source_commit']=meta['source_commit']
  if a.export:pathlib.Path(a.export).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
  if a.summary:
   keys=['total','command_zone_total','officially_legal','legality_issues','budget_compliant','both_decks_legal','within_individual_cap','points_transferred','gameplay_legality_approved','price_snapshot_sha256'];print(json.dumps({k:r[k] for k in keys if k in r},indent=2))
  else:print(json.dumps(r,indent=2,sort_keys=True))
  legal=r.get('both_decks_legal',r.get('officially_legal',False));budget=r.get('budget_compliant',r.get('within_individual_cap',False));return 0 if legal and budget else 1
 except (ValueError,KeyError) as e:print('ERROR: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
