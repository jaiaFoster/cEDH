"""Offline season0-proposed calculator; location prices, no synergy surcharge."""
import argparse,gzip,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'commander-doubles-final-audit'))
from audit_backend import AuditBackend,load_deck
from ranking import OracleIndex,eligibility
import pandas as pd
class RecalibratedBackend(AuditBackend):
 def __init__(self,index,frame,config,combos=None,anchors=None,precedence=None):
  # Earlier hardcoded tier intervals were assistant policy, not human instructions.
  super().__init__(index,frame,config,combos,anchors=[])
  self.anchors=list(anchors or []);self.precedence=precedence or []
  for a in self.anchors:
   if a['tier']==0 and self.card_price(index.resolve(a['card_name']),a['zone'])!=0:raise ValueError('Organizer free qualitative anchor conflict: '+a['card_name'])
  for r in self.precedence:
   value=self.card_price(r['oracle_id'],r['zone']);authority=r['authority']
   if authority=='explicit_organizer_price' and value!=r['working_price']:raise ValueError('Explicit organizer price conflict: '+r['card_name'])
   bounds=r.get('approved_range')
   if bounds and ((bounds[0] is not None and value<bounds[0]) or (bounds[1] is not None and value>bounds[1])):raise ValueError('Organizer range conflict: '+r['card_name'])
 def score(self,deck):
  r=super().score(deck)
  for row in r['rows']:
   rec=self.ratings.get(row['oracle_id'],{})
   if not rec or not rec.get('manually_assessed',False):
    row['rating_evidence']='unreviewed_or_explicit_exception_see_precedence'
   row['price_authority']='global_curve_proposal'
   for p in self.precedence:
    if p['oracle_id']==row['oracle_id'] and p['zone']==row['zone']:row['price_authority']=p['authority']
   if not rec:r['rules_risk_flags'].append('known_identity_unrated_zero_pending_review:'+row['card_name'])
  r['schedule_status']='season0-proposed_not_activated';return r

def load_backend(config_path=None,overrides_path=None):
 config=json.loads(pathlib.Path(config_path or HERE/'scoring_config.json').read_text())
 if overrides_path:
  incoming=json.loads(pathlib.Path(overrides_path).read_text())
  for oid,fields in incoming.items():config.setdefault('overrides',{}).setdefault(oid,{}).update(fields)
 cards=[json.loads(l) for l in gzip.open(HERE/'data/oracle_current.jsonl.gz','rt')];index=OracleIndex(cards)
 frame=pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv')
 prior=json.loads((ROOT/'commander-doubles-final-audit/audit_inputs.json').read_text())
 ledger=json.loads((HERE/'calibration_precedence.json').read_text())
 combos=json.loads((HERE/'pairing_review_rules.json').read_text())
 return RecalibratedBackend(index,frame,config,combos,prior['anchors'],ledger['effective_location_decisions'])
def cli():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('deck_a');p.add_argument('--deck-b');p.add_argument('--config');p.add_argument('--overrides');p.add_argument('--export-overrides');p.add_argument('--export');p.add_argument('--team-cap',type=int);p.add_argument('--individual-cap',type=int);p.add_argument('--individual-reference',type=int);p.add_argument('--transfer-fraction',type=float)
 args=p.parse_args();b=load_backend(args.config,args.overrides);a=load_deck(args.deck_a)
 imported=json.loads(pathlib.Path(args.deck_a).read_text()) if args.deck_a.endswith('.json') else {}
 bb=load_deck(args.deck_b) if args.deck_b else load_deck(args.deck_a,'b') if 'submitted_decks' in imported else None
 if bb is not None:r=b.team(a,bb,args.team_cap,args.individual_cap,args.individual_reference,args.transfer_fraction)
 else:
  if any(v is not None for v in (args.team_cap,args.individual_reference,args.transfer_fraction)):p.error('Team options require two decks')
  if args.individual_cap is not None:
   if args.individual_cap<0:p.error('Negative cap')
   b.config['individual_cap']=args.individual_cap
  r=b.score(a)
 if args.export_overrides:pathlib.Path(args.export_overrides).write_text(json.dumps(b.audit_config['overrides'],indent=2,sort_keys=True)+'\n')
 out=json.dumps(r,indent=2,sort_keys=True)+'\n'
 if args.export:pathlib.Path(args.export).write_text(out)
 print(out)
if __name__=='__main__':cli()
