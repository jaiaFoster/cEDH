"""Batch2 price adapter. Reads dated organizer documents; does not alter earlier artifacts."""
import collections,json,pathlib,re,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from pricing import load as load_batch1
VERSION='season0-proposed-batch2-2026-10-21'
SOURCE_COMMIT='02c84d47759691f63711caf67a25b33050de720b'
def load(documents=None):
 b,old17=load_batch1()
 documents=documents or json.loads((HERE/'batch2/research/calibration_documents.json').read_text())
 history=[];effective={(r['oracle_id'],r['zone']):r for r in b.precedence}
 def apply(name,value,authority,source,zone='main',bounds=None,reason=''):
  oid=b.index.resolve(name);field='main_deck_points' if zone=='main' else 'command_zone_points'
  previous=b.card_price(oid,zone)
  row={'oracle_id':oid,'card_name':b.index.cards[oid]['name'],'zone':zone,'previous_price':previous,'working_price':int(value),'authority':authority,'approved_range':bounds,'source':source,'reason':reason,'activated':False}
  history.append(row);b.config['overrides'].setdefault(oid,{})[field]=int(value)
  if not(effective.get((oid,zone),{}).get('authority') in ('explicit_organizer_price','qualitative_zero_anchor') and previous==value and authority!='explicit_organizer_price'):effective[oid,zone]=row
 exact={"Orim's Chant":1,'Abeyance':1,'Badgermole Cub':5,'Basalt Monolith':2,'Bloom Tender':1,'Command Tower':1,'Devoted Druid':1,'Enduring Vitality':4,'Formidable Speaker':1,'Kutzil, Malamet Exemplar':8,'Walking Ballista':2,'Vizier of Remedies':1,'Wargate':2}
 for n,v in exact.items():apply(n,v,'explicit_organizer_price','team_A_organizer_calibration_2026-10-21.md')
 picks={'Beseech the Mirror':(6,[5,7]),'Lavinia, Azorius Renegade':(2,[1,2]),'Scheming Symmetry':(5,[5,6]),'Tidal Barracuda':(2,[1,2]),'Chord of Calling':(8,[7,8]),'Eldritch Evolution':(9,[8,10]),'Finale of Devastation':(9,[8,10]),"Green Sun's Zenith":(6,[6,None]),'Imperial Recruiter':(4,[3,5]),'Neoform':(6,None),'Recruiter of the Guard':(4,[3,4]),'Seedborn Muse':(2,[1,2]),'Teferi, Time Raveler':(7,[7,None])}
 for n,(v,rg) in picks.items():apply(n,v,'working_selection_within_organizer_guidance','team_A_organizer_calibration_2026-10-21.md',bounds=rg)
 # Preserve illustration status and the one explicitly provisional CZ assignment.
 preview=next(v['content'] for k,v in documents.items() if k.endswith('team_B_repricing_preview_2026-10-21.md'))
 for ln in preview.splitlines():
  cells=[v.strip() for v in ln.strip('|').split('|')]
  if ln.startswith('|') and len(cells)==3 and cells[1].isdigit() and cells[2].isdigit():
   apply(cells[0],int(cells[2]),'provisional_working_price','batch1/team_B_repricing_preview_2026-10-21.md')
 apply('Derevi, Empyrial Tactician',2,'provisional_working_price','batch1/team_B_repricing_preview_2026-10-21.md',zone='commanders',reason='Preview explicitly selected2 in both zones; not exact approval.')
 fetches='Arid Mesa|Bloodstained Mire|Flooded Strand|Marsh Flats|Misty Rainforest|Polluted Delta|Scalding Tarn|Verdant Catacombs|Windswept Heath|Wooded Foothills'.split('|')
 duals='Tundra|Underground Sea|Badlands|Taiga|Savannah|Scrubland|Volcanic Island|Bayou|Plateau|Tropical Island'.split('|')
 shocks='Hallowed Fountain|Watery Grave|Blood Crypt|Stomping Ground|Temple Garden|Godless Shrine|Steam Vents|Overgrown Tomb|Sacred Foundry|Breeding Pool'.split('|')
 surveils='Meticulous Archive|Undercity Sewers|Raucous Theater|Commercial District|Lush Portico|Shadowy Backstreet|Thundering Falls|Underground Mortuary|Elegant Parlor|Hedge Maze'.split('|')
 for fam,ns,v in [('original fetch',fetches,5),('original dual',duals,5),('shock',shocks,2),('surveil',surveils,2)]:
  for n in ns:apply(n,v,'working_land_family_selection','organizer_batch1_price_lock_2026-10-21.md',reason=fam+' family retained at current working values, not exact individual approvals.')
 rainbow={'City of Brass':2,'Mana Confluence':2,'Forbidden Orchard':2,'Exotic Orchard':1,'Reflecting Pool':2,'Gemstone Mine':1,'Spire of Industry':1,'Glimmervoid':1,'Morphic Pool':2,'Sea of Clouds':2,'Luxury Suite':2,'Bountiful Promenade':2,'Spire Garden':2,'Spectator Seating':2,'Rejuvenating Springs':2,'Training Center':2,'Vault of Champions':2,'Undergrowth Stadium':2}
 for n,v in rainbow.items():apply(n,v,'working_land_family_selection','organizer_batch1_price_lock_2026-10-21.md',bounds=[1,2],reason='Explicitly identified rainbow/multiplayer family working pick. Conditional lands may cost less; no blanket nonbasic tax.')
 for n,v in {"Sensei's Divining Top":3,'Roaming Throne':2,'Sink into Stupor // Soporific Springs':1}.items():apply(n,v,'explicit_organizer_price','batch1/team_C_organizer_calibration_2026-10-21.md')
 for n,v in {"Orim's Chant":1,'Abeyance':1,"Gaea's Cradle":15,'Birthing Pod':5,'Scheming Symmetry':5}.items():apply(n,v,'explicit_organizer_price','organizer_batch1_price_lock_2026-10-21.md')
 for n in ['Boseiju, Who Endures','Otawara, Soaring City']:apply(n,6,'working_selection_within_approved_range','organizer_batch1_price_lock_2026-10-21.md',bounds=[5,6],reason='Latest organizer requested5–6; six is working choice, not exact approval.')
 b.precedence=list(effective.values());b.config['version']=VERSION;b.audit_config['version']=VERSION
 b.audit_config['overrides']=b.config['overrides'];b.audit_config['team_cap']=120;b.audit_config['individual_cap']=72;b.audit_config['individual_reference']=60;b.audit_config['transfer_fraction']=.2
 return b,history
def parse_inputs(raw):
 out={}
 for did,d in raw.items():
  roles={};main=collections.Counter()
  for role,text in d['roles'].items():
   for line in text.splitlines():
    if not line.strip():continue
    m=re.match(r'^(\d+) (.+)$',line.strip());q,n=(int(m[1]),m[2]) if m else (1,line.strip())
    main[n]+=q;roles[n]=role
  out[did]={'main':dict(main),'commanders':{n:1 for n in d['commanders']}}
 return out
