"""Offline Batch2 scorer using latest frozen working calibration, not Batch1 prices."""
import argparse,csv,hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from pricing_batch2 import load
from audit_backend import load_deck
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('deck_a');p.add_argument('--deck-b');p.add_argument('--export');p.add_argument('--summary',action='store_true');p.add_argument('--team-cap',type=int,default=120);p.add_argument('--individual-cap',type=int,default=72);p.add_argument('--reference',type=int,default=60);p.add_argument('--transfer-fraction',type=float,default=.2);a=p.parse_args()
 try:
  b,_=load();f=HERE/'batch2';meta=json.loads((f/'provenance.json').read_text());snapshot=(f/'price_snapshot.csv').read_bytes()
  if hashlib.sha256(snapshot).hexdigest()!=meta['price_snapshot_sha256']:raise ValueError('Frozen price snapshot checksum mismatch')
  from pricing import BASE
  if hashlib.sha256((BASE/'data/oracle_current.jsonl.gz').read_bytes()).hexdigest()!=meta['oracle_archive_sha256']:raise ValueError('Oracle dependency changed; explicit version review required')
  for r in csv.DictReader(snapshot.decode().splitlines()):
   if b.card_price(r['oracle_id'],'main')!=int(r['main_deck_points']):raise ValueError('Main prices differ from frozen snapshot')
   if r['command_zone_points'] and b.card_price(r['oracle_id'],'commanders')!=int(r['command_zone_points']):raise ValueError('Command prices differ from frozen snapshot')
  if a.deck_b:r=b.team(load_deck(a.deck_a),load_deck(a.deck_b),a.team_cap,a.individual_cap,a.reference,a.transfer_fraction)
  else:
   if a.individual_cap<0:raise ValueError('Invalid individual cap')
   b.config['individual_cap']=a.individual_cap;r=b.score(load_deck(a.deck_a))
  r['price_snapshot_sha256']=meta['price_snapshot_sha256'];r['gameplay_legality_approved']=False
  text=json.dumps(r,sort_keys=True,indent=2)
  if a.export:pathlib.Path(a.export).write_text(text+'\n')
  if a.summary:print(json.dumps({k:r[k] for k in ('version','total','command_zone_total','officially_legal','both_decks_legal','within_individual_cap','budget_compliant','points_transferred','gameplay_legality_approved') if k in r},indent=2))
  else:print(text)
  return 0 if r.get('both_decks_legal',r.get('officially_legal',False)) and r.get('budget_compliant',r.get('within_individual_cap',False)) else 1
 except (ValueError,KeyError) as e:print('ERROR: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
