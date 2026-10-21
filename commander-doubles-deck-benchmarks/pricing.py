"""Frozen recalibration schedule plus seventeen latest organizer location overrides."""
import copy,csv,gzip,hashlib,json,pathlib,re,sys
import pandas as pd
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'commander-doubles-cutoff-recalibration'))
from recalibrated_backend import RecalibratedBackend
from ranking import OracleIndex,eligibility,oracle_text
SOURCE_COMMIT='db3b8e8ce97e789ee967398cfe6f024e677d2a60'
BASE=ROOT/'commander-doubles-cutoff-recalibration'
def overlay_entries(index):
 text=(BASE/'organizer_premium_boundary_decisions_2026-10-20.md').read_text();rows=[]
 for line in text.splitlines():
  if not line.startswith('|') or '**' not in line:continue
  cells=[v.strip() for v in line.strip('|').split('|')]
  if len(cells)!=5 or cells[1] not in ('main','commanders'):continue
  name,zone,old,new,delta=cells;v=int(new.replace('*',''))
  rows.append({'card_name':name,'oracle_id':index.resolve(name),'zone':zone,'organizer_table_previous_price':int(old),'working_price':v,'authority':'explicit_organizer_price','reason':'Latest seventeen numerical decisions; supersedes prior integer proposal by exact location.','approved_range':None,'source':'organizer_premium_boundary_decisions_2026-10-20.md','activated':False})
 assert len(rows)==17,len(rows)
 return rows

def load():
 cards=[json.loads(l) for l in gzip.open(BASE/'data/oracle_current.jsonl.gz','rt')];index=OracleIndex(cards)
 frame=pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv')
 config=json.loads((BASE/'scoring_config.json').read_text());prior=json.loads((ROOT/'commander-doubles-final-audit/audit_inputs.json').read_text());precedence=json.loads((BASE/'calibration_precedence.json').read_text())['effective_location_decisions'];latest=overlay_entries(index)
 for r in latest:config['overrides'].setdefault(r['oracle_id'],{})['main_deck_points' if r['zone']=='main' else 'command_zone_points']=r['working_price']
 replacements={(r['oracle_id'],r['zone']) for r in latest};precedence=[r for r in precedence if (r['oracle_id'],r['zone']) not in replacements]+latest
 config.update(version='season0-proposed-batch1-price-snapshot',status='season0-proposed_not_activated')
 backend=RecalibratedBackend(index,frame,config,json.loads((BASE/'pairing_review_rules.json').read_text()),prior['anchors'],precedence)
 return backend,latest
