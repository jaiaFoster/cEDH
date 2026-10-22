"""Frozen Batch3 overlay on the preserved Batch2 adapter; no historical files are modified."""
import csv,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from pricing_batch2 import load as prior_load,parse_inputs
VERSION='season0-proposed-batch3-2026-10-21'
SOURCE_COMMIT='0b1d2ddfc1e08908c79b406babd6c2e0dc864dfc'
def load(overrides=None):
 b,history=prior_load()
 if overrides is None:
  overrides=list(csv.DictReader((HERE/'batch3/research/accepted_working_price_overrides_2026-10-21.csv').read_text().splitlines()))
 effective={(r['oracle_id'],r['zone']):r for r in b.precedence}
 for a in overrides:
  oid=b.index.resolve(a['card_name']);zone=a['zone'];v=int(a['points'])
  assert zone in ('main','commanders') and v>=0
  row={'oracle_id':oid,'card_name':b.index.cards[oid]['name'],'zone':zone,'previous_price':b.card_price(oid,zone),'working_price':v,'authority':a['authority'],'source':'accepted_working_price_overrides_2026-10-21.csv','activated':False}
  history.append(row);effective[oid,zone]=row
  b.config['overrides'].setdefault(oid,{})['main_deck_points' if zone=='main' else 'command_zone_points']=v
 b.precedence=list(effective.values())
 b.config['version']=VERSION;b.audit_config['version']=VERSION
 b.audit_config['overrides']=b.config['overrides']
 return b,history
