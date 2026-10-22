"""Issue #5: offline, versioned research schedule and unchanged-deck rescoring.

This is an explicit price overlay, never a change to the historical cutoff model.
All research prices remain proposals. No cards, construction rules or bans change.
"""
from __future__ import annotations
import argparse, collections, copy, csv, gzip, hashlib, io, json, pathlib, re, statistics, sys

HERE = pathlib.Path(__file__).resolve().parent
BENCH = HERE.parent
ROOT = BENCH.parent
sys.path.insert(0, str(BENCH))
from pricing_batch3 import load as load_historical
from pricing import BASE, eligibility, oracle_text
from ranking import name_key
from audit_backend import load_deck
from recalibration_reports_v3 import render_reports
from recalibration_rules_v3 import generate_rules

VERSION = 'season0-proposed-global-v3-2026-10-22'
SOURCE_COMMIT = 'a8b91b934120d412d514c0529cb36c34df6901b0'
OVERLAY = HERE / 'organizer_effective_price_overlay_v2_2026-10-22.csv'
PRIOR = ROOT / 'commander-doubles-cutoff-recalibration/recalibrated_point_schedule.csv'
HANDOFF = HERE / 'agent_handoff_v1_2026-10-22.md'
CR_URL = 'https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt'
NOTES = [
 'team_A_organizer_calibration_2026-10-21.md',
 'batch1/team_B_repricing_preview_2026-10-21.md',
 'batch1/team_C_organizer_calibration_2026-10-21.md',
 'organizer_batch1_price_lock_2026-10-21.md',
 'batch2/team_D_organizer_calibration_2026-10-21.md',
 'batch2/team_E_organizer_calibration_2026-10-21.md',
 'batch2/team_F_organizer_calibration_2026-10-21.md',
 'batch3/team_G_organizer_calibration_2026-10-21.md',
 'batch3/team_G_followup_prices_2026-10-21.md',
 'batch3/team_H_organizer_calibration_2026-10-21.md',
 'batch3/team_I_organizer_calibration_2026-10-21.md',
]

# These are deliberate nonchanges in the supplied handoff/review, not new taxes.
ZERO_MAIN = [
 'Pox','Smallpox','Death Cloud','Contamination',"Geth's Grimoire",
 'Life from the Loam','Exploration','Burgeoning','Dakmor Salvage',
 "Thespian's Stage",'Dark Depths','Expedition Map','Dramatic Reversal',
 'The Reality Chip','Scroll Rack','Viscera Seer','Putrid Imp','Wild Mongrel',
 'Noose Constrictor','Oblivion Crown','Acererak the Archlich',
 'Solitary Confinement',
]
EXACT_A = {"Orim's Chant",'Abeyance','Badgermole Cub','Basalt Monolith',
 'Bloom Tender','Command Tower','Devoted Druid','Enduring Vitality',
 'Formidable Speaker','Kutzil, Malamet Exemplar','Walking Ballista',
 'Vizier of Remedies','Wargate',"Gaea's Cradle",'Scheming Symmetry',
 "Sensei's Divining Top",'Roaming Throne','Sink into Stupor // Soporific Springs'}
EXACT_DF = {'Aetherflux Reservoir','Phyrexian Altar',"Ashnod's Altar",'Krark-Clan Ironworks',
 'Felidar Sovereign','Ranger of Eos','Triskelion','Harmonic Prodigy','Clock of Omens',
 'Goblin Welder','Goblin Engineer','Lotho, Corrupt Shirriff','Mystic Forge',
 'Rings of Brighthearth','Urza, Lord High Artificer','Unwinding Clock','Merchant Scroll',
 'Transmute Artifact'}

# Named follow-ups are not automatic price recommendations. Generic query hits
# otherwise put slow fetch lands ahead of genuinely uncertain specialized engines.
FOLLOWUP = {
 'Eye of Ugin':'Colorless search/discount in a land slot; no ordinary mana production and costly activation. Assess specialized ceiling before any tax.',
 'Helm of the Host':'Deliberately plausible free payoff for Godo engine proposal; high equipment cost is counterexample to pricing every combo component.',
 'Primal Surge':'Ten-mana all-permanent build can win, but severe deck restriction/initial investment; candidate for remaining free.',
 'Mystic Reflection':'Cheap global creature-entry replacement can amplify token plans, with exact target/control windows; no automatic engine designation.',
 'Ob Nixilis, Captive Kingpin':'Unpointed command access with exactly-one-life-loss condition; review two-opponent triggers and All Will Be One mechanism together without pair surcharge.',
 'All Will Be One':'Five-mana counter-to-damage converter; investigate reusable rather than interchangeable-payoff role, not every possible counter combo.',
 'Ob Nixilis, Unshackled':'Six-mana opponent-search punishment may scale as shared-life losses; target searches and actual trigger controller need state analysis.',
 'Energy Field':'Own-player damage protection does not shield teammate. Likely low despite global graveyard replacement support.',
 'Primal Amulet // Primal Wellspring':'Conditional own-spell reduction then spell copying from a transformed land; real four-spell/setup requirements, not generic MDFC pricing.',
}

FAMILIES = {
 'tutors': ('Demonic Tutor 15; Enlightened 9; Call4; artifact tutors8–9; specialist Mages1',
  'Expedition Map0 and Sylvan Scrying0 are intentional; not every search is charged.',
  'Access breadth, destination, timing and repeatability, not the word search alone.'),
 'acceleration': ('Dark Ritual9; Basalt4; Bloom Tender1; Lake6; Cradle15',
  'One-mana ordinary dorks and ordinary ramp remain0; accepted Bloom Tender1 is not silently raised.',
  'Count net mana after real costs, setup, symmetry and ownership; no shared mana pools.'),
 'lands': ('Crop Rotation6; Boseiju/Otawara6; Shifting Woodland3; fetch/dual5 working',
  'Stage, Depths, Loam, Exploration, Burgeoning and Map intentionally0; conditional/basic fixing mostly free.',
  'Land-slot opportunity cost and repeatable access matter, but not all nonbasics are premium.'),
 'reusable_engines': ('Aluren4; KCI10; Clock5; Mystic Forge6; Curio3',
  'Acererak0, ordinary tokens and narrow borrowed abilities can be free; engine premium is not a pair surcharge.',
  'Concentrate cost on portable repeated conversion; explicitly identify prerequisite ownership.'),
 'reanimation': ('Reanimate/Animate/Dance/Necromancy4 working; Replenish9 working',
  'Ordinary expensive one-shot resurrection and narrow targets need no universal4-point family tax.',
  'Graveyard scope, mana cheated, reusable permissions and destination separate engine from payload.'),
 'interaction': ('Force14; Fierce13; Silence14; Chant1; Abeyance1; Swan2; Shoal/Misdirection2',
  'Counterspell, ordinary removal and intentionally free Cyclonic Rift are not mechanically taxed.',
  'Free protection and timing can defend a teammate, but targets and controller wording remain exact.'),
 'commanders': ('Sheoldred main7/CZ13 working; Chulane CZ2; Tymna CZ9',
  'Kenrith/Najeela/Inalla/Yuriko/Oloro deliberate free CZ exceptions preserved; no blanket doubling.',
  'Guaranteed access and recast role are independent location judgments; Partner costs add independently.'),
 'card_advantage': ('Rhystic9; Remora6; One Ring10; Wheel5 working; Lotho7',
  'Faerie Mastermind and Snapcaster deliberate0; ordinary draw/cantrips free.',
  'Separate cards actually received by one head from two enemy streams and shared-turn opportunities.'),
 'extra_turns': ('Time Sieve8 retained; Expropriate8 organizer; cheap one-card turn proposed12',
  'Savor skips both friendly untaps; defensive protection is not automatically an offensive turn engine.',
  'Extra turn is an extra TEAM turn under805.8; pay own costs and model real deployment.'),
 'shared_life': ('Sorin5; Bloodletter~5; Test7; Exsanguinate1',
  'Symmetric Pox variants0 and weak payloads free; shared value does not merge gain/loss events.',
  'Calculate each-head events applied to shared60 and distinguish loss from damage or life-setting.'),
 'mdfc': ('Sink into Stupor1',
  'Beyeen Veil, Zof Consumption and other weak/tapped options do not receive a blanket land-face tax.',
  'Exactly one Oracle identity charged once; actual spell utility plus land flexibility evaluated individually.'),
 'narrow_payoffs': ('Acererak0; Ballista2; Bloodthirsty3; Tenacity4',
  'No automatic combo-membership or teammate premium; ordinary interchangeable payoffs may remain0.',
  'Independent efficient utility may justify a small price; dead-outside-engine role alone does not.'),
 'ordinary_or_prior': ('Prior individual assessment retained pending specific contrary evidence',
  'Most of the legal card pool stays free; a screen nomination is not a human approval.',
  'Document what was screened and inherited rather than pretending all prior tail ranks are independently measured.'),
}

def sha(data):
    return hashlib.sha256(data.encode() if isinstance(data,str) else data).hexdigest()
def jt(data): return json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
def rows(path):
    with pathlib.Path(path).open(newline='') as f: return list(csv.DictReader(f))
def ct(data, fields=None):
    data=list(data); fields=fields or list(data[0]); out=io.StringIO(newline='')
    w=csv.DictWriter(out,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(data);return out.getvalue()
def table(data,fields):
    return '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'' )).replace('|','/') for k in fields)+' |\n' for r in data)
def legal(c):
    # Oracle bulk picks a representative PRINTING. Intuition/Pox can be digital
    # representatives of physically printed cards; the format legality is identity-level.
    return c.get('legalities',{}).get('commander')=='legal'
def zone_field(zone):
    if zone not in ('main','commanders'):raise ValueError('Unknown pricing zone: '+str(zone))
    return 'main_deck_points' if zone=='main' else 'command_zone_points'
def checked_points(value):
    if isinstance(value,bool) or not isinstance(value,int) or value<0:raise ValueError('Nonnegative integer price required')
    return value
def assign(b,oid,zone,value):
    if oid not in b.index.cards:raise KeyError('Unknown Oracle ID: '+str(oid))
    field=zone_field(zone);checked_points(value)
    if zone=='commanders' and not eligibility(b.index.cards[oid]):raise ValueError('Ineligible command-zone identity')
    b.config['overrides'].setdefault(oid,{})[field]=value
    b.audit_config['overrides']=b.config['overrides']

def sources():
    return [(BENCH/p) for p in NOTES]+[OVERLAY,HANDOFF,PRIOR,
     BENCH/'accepted_working_price_overrides_2026-10-21.csv',
     BENCH/'accepted_working_price_summary_2026-10-21.md',
     BENCH/'retotal_12_decks_2026-10-21.csv',BENCH/'retotal_full_card_ledger_2026-10-21.csv',
     ROOT/'commander-doubles-cutoff-recalibration/organizer_premium_boundary_decisions_2026-10-20.md',
     ROOT/'commander-doubles-final-audit/human_calibration_anchors.json',
     ROOT/'commander-doubles-final-audit/organizer_calibration_2026-10-20.md',
     BASE/'data/oracle_current.jsonl.gz',BASE/'data/comprehensive_rules.gz',
     HERE/'proposals_v3.tsv',HERE/'v3_inputs/research_evidence.json',HERE/'recalibration_v3.py',
     HERE/'recalibration_reports_v3.py',HERE/'recalibration_rules_v3.py',
     HERE/'score_recalibration_v3.py',HERE/'test_recalibration_v3.py',HERE/'validate_recalibration_v3.py',
     HERE/'v3_inputs/identity_paper_examples.json',HERE/'v3_inputs/current_rules_verification.json',
     BENCH/'pricing.py',BENCH/'pricing_batch2.py',BENCH/'pricing_batch3.py',
     BENCH/'batch2/research/calibration_documents.json',BENCH/'batch3/research/accepted_working_price_overrides_2026-10-21.csv',
     BASE/'scoring_config.json',BASE/'calibration_precedence.json',BASE/'pairing_review_rules.json',BASE/'recalibrated_backend.py',
     ROOT/'commander-doubles-final-audit/audit_backend.py',ROOT/'commander-doubles-final-audit/audit_inputs.json',
     ROOT/'commander-top1000-power-ranking/candidate_inventory.csv',ROOT/'commander-top1000-power-ranking/backend.py',ROOT/'commander-top1000-power-ranking/ranking.py',
     ROOT/'commander-top1000-power-ranking/data/name_aliases.json',
     ROOT/'commander-card-power-research-v1/spellbook_integration.py']

def original_decks():
    result={}
    for batch in range(1,4):
        for path in sorted((BENCH/f'batch{batch}/decks').glob('*.json')):
            result[path.stem]={'path':path,'deck':load_deck(path),'batch':batch}
    if len(result)!=18:raise ValueError('Exactly18 original decks required')
    return result

def normalize_authority(row):
    name=row['card_name'];raw=row['authority']
    if name=='Cabal Coffers':return 'accepted_assistant_placeholder_8_to_10'
    if raw in ('working_selection','range_working','CZ_working'):return raw
    if raw=='organizer_approximate':return 'organizer_approximate'
    if row['source'].startswith('batch3/'):return 'organizer_explicit_numeric'
    if name in ('Boseiju, Who Endures','Otawara, Soaring City'):return 'working_within_organizer_5_to_6'
    if name in ('Reshape','Whir of Invention'):return 'organizer_approximate_around_8'
    if name in ('Pyroblast','Red Elemental Blast','Wishclaw Talisman'):return 'working_at_organizer_lower_bound'
    if name in EXACT_A|EXACT_DF:return 'organizer_explicit_numeric'
    return 'accepted_legacy_working_not_proved_exact'

def approved_bounds(row):
    """Only named documented human intervals; do not bless assistant placeholders."""
    known={'Academy Rector':[8,10],'Birthing Pod':[5,6],'Buried Alive':[3,None],
      'Cloud, Midgar Mercenary':[1,2],'Force of Despair':[1,2],'Icetill Explorer':[1,2],
      'Open the Armory':[2,3],'Ramunap Excavator':[1,2],'Replenish':[9,10],
      'Stoneforge Mystic':[1,2],'Boseiju, Who Endures':[5,6],'Otawara, Soaring City':[5,6],
      'Pyroblast':[1,None],'Red Elemental Blast':[1,None],'Wishclaw Talisman':[4,None]}
    return known.get(row['card_name'])

def family(c,zone='main'):
    text=oracle_text(c).lower();name=c['name'];typ=c.get('type_line','')
    if zone=='commanders':return 'commanders'
    if c.get('layout')=='modal_dfc' and 'Land' in typ:return 'mdfc'
    if 'extra turn' in text:return 'extra_turns'
    if 'Land' in typ:return 'lands'
    if ('search' in text and 'library' in text):return 'tutors'
    if re.search(r'(graveyard|graveyards).*(battlefield|cast|play)|return.*graveyard',text,re.S):return 'reanimation'
    if re.search(r'life total|half.*life|each opponent loses|you gain.*life|loses.*life',text):return 'shared_life'
    if re.search(r'add \{|add.*mana|untap.*land|mana ability',text):return 'acceleration'
    if re.search(r'counter target|protection|can.t cast|can.t activate|spells.*can.t|hexproof',text):return 'interaction'
    if re.search(r'draw (a|two|three|x|cards)|draws a card',text):return 'card_advantage'
    if re.search(r'without paying|untap|whenever.*cast|copy.*ability|sacrifice.*creature',text):return 'reusable_engines'
    return 'ordinary_or_prior'

def matching_note_evidence(name, source):
    selected=[]
    ordered=[ROOT/'commander-doubles-final-audit/organizer_calibration_2026-10-20.md',BASE/'organizer_premium_boundary_decisions_2026-10-20.md']+[BENCH/p for p in NOTES]
    for path in ordered:
        for no,line in enumerate(path.read_text().splitlines(),1):
            if name.casefold() in line.casefold():selected.append({'source':str(path.relative_to(ROOT)), 'line':no,'text':line.strip()})
    # Family-level land assignments may not repeat each card's individual name.
    return selected

def source_path(raw):
    """Resolve inherited shorthand without changing its raw provenance label."""
    aliases={
      'organizer_calibration_2026-10-20.md':ROOT/'commander-doubles-final-audit/organizer_calibration_2026-10-20.md',
      'human_calibration_anchors.json':ROOT/'commander-doubles-final-audit/human_calibration_anchors.json',
      '../../commander-doubles-final-audit/human_calibration_anchors.json':ROOT/'commander-doubles-final-audit/human_calibration_anchors.json',
      'organizer_premium_boundary_decisions_2026-10-20.md':BASE/'organizer_premium_boundary_decisions_2026-10-20.md',
      'batch1_batch2_accepted_working_price_overrides':BENCH/'accepted_working_price_overrides_2026-10-21.csv',
      'accepted_working_price_overrides_2026-10-21.csv':BENCH/'batch3/research/accepted_working_price_overrides_2026-10-21.csv',
    }
    if raw in aliases:return str(aliases[raw].relative_to(ROOT))
    for p in ((BENCH/raw).resolve(),(ROOT/raw).resolve()):
        if p.is_file() and p.is_relative_to(ROOT):return str(p.relative_to(ROOT))
    return raw

def build_backends():
    historical,history=load_historical();v2=copy.deepcopy(historical)
    # New adapters accept back-face names too, but resolve them to one identity.
    # Alias sets preserve ambiguity errors rather than guessing between identities.
    for oid,c in v2.index.cards.items():
        for face in c.get('card_faces',[]):
            if face.get('name'):v2.index.aliases[name_key(face['name'])].add(oid)
    prior_protected={(x['oracle_id'],x['zone']):x for x in historical.precedence
                     if x['authority'] in ('explicit_organizer_price','qualitative_zero_anchor','organizer_approved_range','organizer_minimum_working_price') or x.get('approved_range')}
    authoritative={};overlay=rows(OVERLAY)
    for row in overlay:
        oid=v2.index.resolve(row['card_name']);zone=row['zone'];value=int(row['points']);key=(oid,zone)
        if key in authoritative:raise ValueError('Duplicate organizer row')
        r=dict(row,oracle_id=oid,working_price=value,raw_authority=row['authority'],authority=normalize_authority(row),approved_range=approved_bounds(row),activated=False)
        authoritative[key]=r;assign(v2,oid,zone,value)
    for name in ZERO_MAIN:
        oid=v2.index.resolve(name);key=(oid,'main')
        if key in authoritative and authoritative[key]['working_price']!=0:raise ValueError('Conflicting explicit zero')
        generalized=name in ('Putrid Imp','Wild Mongrel','Noose Constrictor','Oblivion Crown')
        authority='working_zero_under_discard_outlet_guidance' if generalized else 'working_zero_pending_observation' if name=='Solitary Confinement' else 'organizer_explicit_zero_nonchange'
        note='Named implementation of organizer discard-outlets-free guidance, not an individually dictated exact0.' if generalized else 'Deliberate exception/nonchange; Solitary remains under observation.' if name=='Solitary Confinement' else 'Deliberate exception/nonchange, not an inferred family tax.'
        authoritative[key]={'oracle_id':oid,'card_name':name,'zone':'main','working_price':0,'authority':authority,'raw_authority':'handoff_and_review_zero','source':str(HANDOFF.relative_to(BENCH)),'note':note,'activated':False}
        assign(v2,oid,'main',0)
    # Preserve historical free qualitative anchors until a later location-specific numeric decision exists.
    for a in v2.anchors:
        key=(v2.index.resolve(a['card_name']),a['zone'])
        if a['tier']==0 and key not in authoritative:
            authoritative[key]=dict(oracle_id=key[0],card_name=a['card_name'],zone=a['zone'],working_price=0,authority='organizer_historical_free_not_superseded',raw_authority='qualitative_zero_anchor',source='../../commander-doubles-final-audit/human_calibration_anchors.json',note='Historical zero preserved in absence of later numeric override.',activated=False)
            assign(v2,key[0],key[1],0)
    oloro=v2.index.resolve('Oloro, Ageless Ascetic');key=(oloro,'commanders')
    authoritative[key]=dict(oracle_id=oloro,card_name='Oloro, Ageless Ascetic',zone='commanders',working_price=0,authority='organizer_explicit_zero_nonchange',raw_authority='G_review_nonchange',source=NOTES[7],note='Oloro explicitly stays CZ0; do not infer automatic premium.',activated=False)
    assign(v2,oloro,'commanders',0)
    for key,r in prior_protected.items():
        if key not in authoritative:authoritative[key]=dict(r,raw_authority=r['authority'],note=r.get('reason','Prior explicit decision retained.'))
    v2.precedence=list(authoritative.values());v2.config['version']='season0-proposed-organizer-v2-2026-10-22';v2.audit_config['version']=v2.config['version']
    proposals=list(csv.DictReader((HERE/'proposals_v3.tsv').read_text().splitlines(),delimiter='\t'))
    v3=copy.deepcopy(v2);prop={}
    for row in proposals:
        oid=v3.index.resolve(row['card_name']);key=(oid,row['zone']);val=int(row['points'])
        if key in prop:raise ValueError('Duplicate research proposal')
        if key in authoritative:raise ValueError('Research proposal would overwrite organizer price: '+row['card_name'])
        if not legal(v3.index.cards[oid]):raise ValueError('Research proposal is not a legal paper Commander identity: '+row['card_name'])
        prop[key]=dict(row,oracle_id=oid,points=val,priority=int(row['priority']));assign(v3,oid,row['zone'],val)
    v3.precedence=list(authoritative.values())+[dict(oracle_id=o,card_name=v3.index.cards[o]['name'],zone=z,authority='agent_proposal_awaiting_approval',working_price=r['points'],activated=False) for (o,z),r in prop.items()]
    v3.config['version']=VERSION;v3.audit_config['version']=VERSION
    return historical,v2,v3,authoritative,prop,history

def discover(index):
    """Named, deterministic Oracle screens nominate; they NEVER set a price."""
    out=[]
    for oid,c in sorted(index.cards.items()):
        if not legal(c):continue
        text=oracle_text(c).lower();mv=c.get('cmc',99);typ=c.get('type_line','');tags=[]
        if mv<=3 and 'search' in text and 'library' in text and not 'basic land card' in text:tags.append('cheap_nonbasic_search')
        if 'extra turn' in text:tags.append('extra_team_turn')
        if re.search(r'life total (becomes|with)|exchange.*life total|half.*life',text):tags.append('shared_life_transform')
        if re.search(r'(opponent|players?).*can.t draw|draw.*instead',text) and mv<=5:tags.append('draw_replacement_or_denial')
        if re.search(r'rather than pay|without paying (this|its|their)',text) and 'Land' not in typ:tags.append('alternative_cost_or_free_cast')
        if re.search(r'add.*for each|untap (another|all|target)',text) and (mv<=4 or 'Land' in typ):tags.append('repeat_resource_conversion')
        if c.get('layout')=='modal_dfc' and 'Land' in typ:tags.append('mdfc_individual_review')
        if re.search(r'command zone|eminence',text) and eligibility(c):tags.append('command_zone_text')
        if 'Land' in typ and re.search(r'channel|untap|search|copy|destroy|return.*graveyard',text):tags.append('utility_land_slot')
        if c['name'] in FOLLOWUP:tags.append('curated_followup_not_approved_price')
        if tags:out.append({'oracle_id':oid,'card_name':c['name'],'signals':';'.join(tags),'mana_value':mv,'family':family(c),'screen_status':'nomination_not_power_rating','oracle_sha256':sha(oracle_text(c))})
    return out

def budget(a,b,team_cap=120,individual_cap=72,reference=60,transfer_limit=12):
    for n in (a,b,team_cap,individual_cap,reference,transfer_limit):checked_points(n)
    required=max(0,a-reference,b-reference);unused=max(0,reference-min(a,b));possible=min(required,transfer_limit,unused)
    return dict(total=a+b,team_overage=max(0,a+b-team_cap),team_headroom=team_cap-a-b,
      head_a_overage=max(0,a-individual_cap),head_b_overage=max(0,b-individual_cap),
      transfer_required=required,teammate_unused=unused,transferrable_points=possible,
      transfer_shortfall=required-possible,within_transfer_policy=required<=possible,
      within_team_cap=a+b<=team_cap,within_individual_cap=max(a,b)<=individual_cap,
      budget_compliant=a+b<=team_cap and max(a,b)<=individual_cap and required<=possible)

def generate():
    old,v2,v3,authoritative,prop,history=build_backends();index=v3.index
    original=original_decks();prior={r['oracle_id']:r for r in rows(PRIOR)};discovery=discover(index)
    deck_ids={index.resolve(n) for r in original.values() for z in r['deck'].values() for n in z}
    discovery_ids={r['oracle_id'] for r in discovery}
    # Mandatory full union is individually recorded; discoveries get their own screening table.
    # Include inherited positive prices outside the old export: the CSV must not
    # silently differ from the executable global backend (e.g. off-roster duals).
    inherited_positive={o for o,c in index.cards.items() if legal(c) and
        any(v3.card_price(o,z)>0 for z in ['main']+(['commanders'] if eligibility(c) else []))}
    audited=set(prior)|deck_ids|{o for o,z in authoritative}|{o for o,z in prop}|inherited_positive
    pool=audited  # Do not pretend every low-specificity screen hit has had an individual assessment.
    source_manifest={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources()}
    for r in original.values():source_manifest[str(r['path'].relative_to(ROOT))]=sha(r['path'].read_bytes())
    for n in (1,2,3):
        for p in sorted((BENCH/f'batch{n}/decks').glob('*.txt')):source_manifest[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    evidence=json.loads((HERE/'v3_inputs/research_evidence.json').read_text())
    files={};audit=[];schedule=[];lineage=[]
    for (oid,zone),r in sorted(authoritative.items()):
        p=prior.get(oid,{})
        initial=int(p[zone_field(zone)]) if p and p.get(zone_field(zone)) not in ('',None) else ''
        events=[dict(x) for x in history if x['oracle_id']==oid and x['zone']==zone]
        refs=matching_note_evidence(index.cards[oid]['name'],r.get('source',''))
        lineage.append(dict(oracle_id=oid,card_name=index.cards[oid]['name'],zone=zone,initial_points=initial,initial_export_present=bool(p),
          pre_batch3_effective_points=old.card_price(oid,zone),organizer_v2_points=v2.card_price(oid,zone),
          raw_authority=r.get('raw_authority',r['authority']),precision=r['authority'],latest_source=source_path(r.get('source','')),raw_source=r.get('source',''),
          note=r.get('note',r.get('reason','')),approved_range=json.dumps(r.get('approved_range')),family=family(index.cards[oid],zone),
          reasons=FAMILIES[family(index.cards[oid],zone)][2],two_hg_modifier=two_hg_note(index.cards[oid],zone),
          previous_events=json.dumps(events,ensure_ascii=False,sort_keys=True),source_mentions=json.dumps(refs,ensure_ascii=False,sort_keys=True),
          status='season0-proposed',activated=False))
    for oid in sorted(pool,key=lambda o:index.cards[o]['name'].casefold()):
        c=index.cards[oid];text=oracle_text(c)
        for zone in ['main']+(['commanders'] if eligibility(c) else []):
            key=(oid,zone);p=prop.get(key);a=authoritative.get(key);f=p['family'] if p else family(c,zone)
            o=v2.card_price(oid,zone);n=v3.card_price(oid,zone)
            authority='agent_proposal_awaiting_approval' if p else a['authority'] if a else 'inherited_proposal_not_new_approval'
            priority=p['priority'] if p else 1 if n>=8 and not a else 2 if oid in discovery_ids and not a else 3
            prior_reason=prior.get(oid,{}).get('main_reason' if zone=='main' else 'command_zone_reason','')
            if p:reason=p['reason']
            elif a:reason=a.get('note') or a.get('reason') or FAMILIES[f][2]
            else:reason=prior_reason or 'Inherited judgment retained; no individual repricing established in this pass.'
            row=dict(oracle_id=oid,card_name=c['name'],zone=zone,old_effective_points=o,proposed_points=n,delta=n-o,
              authority=authority,exact_vs_working=(a['authority'] if a else 'research_judgment' if p else 'inherited_unvalidated'),
              source=(str((HERE/'proposals_v3.tsv').relative_to(ROOT)) if p else source_path(a.get('source','')) if a else str(PRIOR.relative_to(ROOT))),
              family=f,anchor_comparison=(p['anchor'] if p else FAMILIES[f][0]),reason=reason,two_hg_notes=two_hg_note(c,zone),
              evidence='pinned Oracle; supplied organizer comparisons; '+(family_evidence(f)),
              confidence='moderate_policy_judgment' if p else 'organizer_decision_not_empirical_strength' if a else 'inherited_low_or_unvalidated',
              manual_review_priority=priority,oracle_text_sha256=sha(text),commander_eligible=bool(eligibility(c)),
              commander_legality=c['legalities'].get('commander'),commander_legal_identity=legal(c),point_bearing=legal(c) and n>0,
              status='season0-proposed',activated=False)
            schedule.append(row)
            audit.append(dict(row,in_old_schedule=oid in prior,in_benchmark_decks=oid in deck_ids,newly_discovered=oid not in (set(prior)|deck_ids),
              audit_method='explicit_individual_agent_review' if p else 'organizer_lineage_review' if a else 'Oracle_family_screen_and_prior_rationale_retained',
              oracle_text=text,counterexample=FAMILIES[f][1]))
    files['decision_lineage.csv']=ct(lineage)
    reversals=[]
    for name,trajectory,source,clarification in [
      ("Orim's Chant",'12 prior proposal -> 3 premium decision -> 1 Batch1 decision',NOTES[0],'Later numeric decision supersedes earlier tier5 without editing the tier observation.'),
      ('Basalt Monolith','2 earlier -> 4 final',NOTES[10],'Latest TeamI exact4 applies across batches.'),
      ('Swan Song','3 earlier -> 2 final',NOTES[9],'Latest TeamH exact2 also lowers historical G2 by1.'),
      ('Opposition Agent','8 earlier -> 6 final',NOTES[7],'Direct reduction, not an assistant optimization.'),
      ('Krark-Clan Ironworks','12 TeamD -> 10 TeamF',NOTES[6],'Latest TeamF supersedes earlier12.'),
      ('Unwinding Clock','3 considered -> 2 selected',NOTES[6],'Within-note self-correction; intermediate consideration was not a lasting exact assignment.'),
      ('Land Tax','3 considered -> 2 considered -> 1 selected',NOTES[7],'Preserve final1; considered values are not approved ranges.'),
      ('Crop Rotation','7 considered -> 6 selected',NOTES[10],'Final6 takes precedence.'),
      ('Tireless Provisioner','1 TeamH -> 0 considered -> 1 reaffirmed',NOTES[10],'Zero consideration did not become the effective price.'),
      ('Contamination','1 tentative -> 0 retained',NOTES[7],'Explicit leave-unchanged exception, not a new tax.'),
      ('Bloodthirsty Conqueror','0 pending -> 3 selected',NOTES[8],'Follow-up resolves the original pending substitute loophole.'),
      ('Enduring Tenacity','0 pending -> 4 selected',NOTES[8],'Follow-up resolves the original pending substitute loophole.'),
    ]:
        oid=index.resolve(name);reversals.append(dict(card_name=name,oracle_id=oid,zone='main',ordered_trajectory=trajectory,effective_points=v2.card_price(oid,'main'),latest_source=source_path(source),clarification=clarification,status='season0-proposed',activated=False))
    files['decision_reversals.csv']=ct(reversals)
    files['candidate_point_schedule_v3.csv']=ct(schedule)
    files['agent_price_changes_v3.csv']=ct([x for x in schedule if x['authority']=='agent_proposal_awaiting_approval'])
    files['family_coverage_audit.csv']=ct(audit)
    files['targeted_oracle_discovery.csv']=ct(discovery)
    files['identity_printing_qc.csv']=ct([
      dict(oracle_id=o,card_name=c['name'],representative_digital=c.get('digital',False),representative_games=';'.join(c.get('games',[])),commander_legality='legal',interpretation='Representative printing medium does not establish Oracle identity illegality; retained under format legality.')
      for o,c in sorted(index.cards.items()) if legal(c) and (c.get('digital') or 'paper' not in c.get('games',[]))])
    queue=[]
    for r in discovery:
        o=r['oracle_id'];c=index.cards[o];n=v3.card_price(o,'main')
        if n==0 and (o not in pool or 'search' in oracle_text(c).lower() or len(r['signals'].split(';'))>=2 or c['name'] in FOLLOWUP):
            protected=(o,'main') in authoritative
            priority=3 if protected else 1 if c['name'] in FOLLOWUP else 3 if 'Land' in c.get('type_line','') else 2
            queue.append(dict(r,proposed_points=0,review_status='deliberate_zero_exception' if protected else 'unpriced_nomination_pending_individual_review',priority=priority,reason=FOLLOWUP.get(c['name'],'No automatic screen-based tax; real ceiling/controller/setup must be assessed.'),counterexample=FAMILIES[r['family']][1]))
    queue.sort(key=lambda r:(r['priority'],r['card_name'].casefold()))
    files['unpriced_high_risk_queue.csv']=ct(queue)
    # Reprice the original files only; construction noncompliance is never hidden by a rebuild.
    deck_rows=[];team_rows=[];card_rows=[];normalized={};original_total={}
    for did,r in sorted(original.items()):
        batch=r['batch'];d=r['deck'];normalized[did]={z:{index.resolve(n):q for n,q in d[z].items()} for z in ('main','commanders')}
        report=json.loads((BENCH/f'batch{batch}/reports/{did}.json').read_text());original_total[did]=report['total']
        submitted={(x['oracle_id'],x['zone']):x['points_each'] for x in report['rows']}
        ra=v2.score(d);rb=v3.score(d)
        if not ra['officially_legal'] or not rb['officially_legal']:raise ValueError((did,ra['legality_issues'],rb['legality_issues']))
        for zone,counts in normalized[did].items():
            for oid,q in counts.items():
                for no in range(1,q+1):
                    card_rows.append(dict(deck_id=did,team=did[0],oracle_id=oid,card_name=index.cards[oid]['name'],zone=zone,copy_index=no,quantity=1,
                      original_points=submitted[oid,zone],organizer_v2_points=v2.card_price(oid,zone),candidate_v3_points=v3.card_price(oid,zone),
                      delta_v2_from_original=v2.card_price(oid,zone)-submitted[oid,zone],delta_v3_from_v2=v3.card_price(oid,zone)-v2.card_price(oid,zone),
                      authority=next(x['authority'] for x in schedule if x['oracle_id']==oid and x['zone']==zone)))
        drivers=lambda rr:'; '.join(x['card_name']+' '+str(x['total']) for x in rr['rows'][:7])
        deck_rows.append(dict(deck_id=did,batch=batch,original_points=report['total'],organizer_v2_points=ra['total'],candidate_v3_points=rb['total'],
          v2_delta_from_original=ra['total']-report['total'],v3_delta_from_v2=rb['total']-ra['total'],v3_delta_from_original=rb['total']-report['total'],
          original_cz_points=report['command_zone_total'],v2_cz_points=ra['command_zone_total'],v3_cz_points=rb['command_zone_total'],
          v2_over_72=max(0,ra['total']-72),v3_over_72=max(0,rb['total']-72),v2_pointed_cards=sum(x['quantity'] for x in ra['rows'] if x['points_each']),
          v3_pointed_cards=sum(x['quantity'] for x in rb['rows'] if x['points_each']),officially_legal=True,cards=sum(sum(z.values()) for z in d.values()),
          original_deck_sha256=sha(r['path'].read_bytes()),v2_top_drivers=drivers(ra),v3_top_drivers=drivers(rb)))
    for t in 'ABCDEFGHI':
        a=next(x for x in deck_rows if x['deck_id']==t+'1');b=next(x for x in deck_rows if x['deck_id']==t+'2')
        for model,field in [('organizer_v2','organizer_v2_points'),('candidate_v3','candidate_v3_points')]:
            br=budget(a[field],b[field]);check=(v2 if model=='organizer_v2' else v3).team(original[t+'1']['deck'],original[t+'2']['deck'])
            if br['budget_compliant']!=check['budget_compliant']:raise ValueError('Budget policy drift')
            team_rows.append(dict(team=t,model=model,head_a=a[field],head_b=b[field],original_team=original_total[t+'1']+original_total[t+'2'],delta_from_original=br['total']-original_total[t+'1']-original_total[t+'2'],**br,status='season0-proposed',activated=False))
    for model in ('organizer_v2','candidate_v3'):
        ranked=sorted([r for r in team_rows if r['model']==model],key=lambda r:(-r['total'],r['team']))
        for r in ranked:r['rank_by_construction_cost']=1+sum(x['total']>r['total'] for x in ranked)
    files['deck_score_changes.csv']=ct(deck_rows)
    files['team_score_changes.csv']=ct(team_rows)
    files['full_card_rescoring_ledger.csv']=ct(card_rows)
    files['changed_card_copies.csv']=ct([r for r in card_rows if r['delta_v2_from_original'] or r['delta_v3_from_v2']])
    sensitivity=[];team_sensitivity=[]
    for shift in (-2,-1,0,1,2):
        totals={}
        for did,inv in normalized.items():
            total=0
            for zone,counts in inv.items():
                for oid,q in counts.items():
                    n=v3.card_price(oid,zone)
                    if (oid,zone) in prop and n>0:n=max(0,n+shift)
                    total+=q*n
            totals[did]=total
            central=next(r['candidate_v3_points'] for r in deck_rows if r['deck_id']==did)
            sensitivity.append(dict(deck_id=did,positive_agent_price_shift=shift,points=total,delta_from_central=total-central,over_72=max(0,total-72),organizer_values_unchanged=True,interpretation='deterministic scenario_not_confidence_interval'))
        for t in 'ABCDEFGHI':team_sensitivity.append(dict(team=t,positive_agent_price_shift=shift,**budget(totals[t+'1'],totals[t+'2'])))
    files['sensitivity_by_deck_v3.csv']=ct(sensitivity)
    files['sensitivity_by_team_v3.csv']=ct(team_sensitivity)
    distribution=[]
    for col in ('original_points','organizer_v2_points','candidate_v3_points'):
        v=[r[col] for r in deck_rows];quart=statistics.quantiles(v,n=4,method='inclusive')
        distribution.append(dict(schedule=col,n=len(v),mean=statistics.mean(v),median=statistics.median(v),sample_sd=statistics.stdev(v),q25=quart[0],q75=quart[2],iqr=quart[2]-quart[0],minimum=min(v),maximum=max(v),over72=sum(n>72 for n in v)))
    files['score_distribution_summary.csv']=ct(distribution)
    anchor_rows=[]
    for a in v3.anchors:
        oid=index.resolve(a['card_name']);zone=a['zone']
        anchor_rows.append(dict(card_name=a['card_name'],oracle_id=oid,zone=zone,historical_tier=a['tier'],organizer_v2_points=v2.card_price(oid,zone),candidate_v3_points=v3.card_price(oid,zone),interpretation='Historical0–5 qualitative observation preserved verbatim; later numeric location decisions control.'))
    files['historical_anchor_comparison.csv']=ct(anchor_rows)
    pointed=[r for r in schedule if r['point_bearing']]
    old_pointed=[r for r in schedule if r['commander_legal_identity'] and r['old_effective_points']>0]
    summary=dict(version=VERSION,status='season0-proposed',activated=False,source_commit=SOURCE_COMMIT,old_schedule_identities=len(prior),benchmark_unique_identities=len(deck_ids),mandatory_union=len(set(prior)|deck_ids),recorded_audit_union=len(pool),additional_individual_proposal_identities=len({o for o,z in prop}-(set(prior)|deck_ids)),additional_inherited_positive_identities=len(inherited_positive-(set(prior)|deck_ids|{o for o,z in prop}|{o for o,z in authoritative})),
      commander_legal_oracle_population=sum(legal(c) for c in index.cards.values()),oracle_screen_nominees=len(discovery),organizer_overlay_rows=len(rows(OVERLAY)),protected_location_decisions=len(authoritative),explicit_agent_proposals=len(prop),changed_agent_prices=sum(v2.card_price(o,z)!=v3.card_price(o,z) for o,z in prop),
      candidate_rows=len(schedule),legal_pointed_identities=len({r['oracle_id'] for r in pointed}),legal_pointed_main=sum(r['zone']=='main' for r in pointed),legal_pointed_commanders=sum(r['zone']=='commanders' for r in pointed),organizer_v2_legal_pointed_identities=len({r['oracle_id'] for r in old_pointed}),newly_pointed_locations=sum(r['old_effective_points']==0 and r['proposed_points']>0 for r in schedule),newly_unpointed_locations=sum(r['old_effective_points']>0 and r['proposed_points']==0 for r in schedule),known_unpointed_policy='verified identity zero; unknown error',
      decks=18,expanded_card_entries=len(card_rows),source_unchanged_deck_hashes={k:sha(r['path'].read_bytes()) for k,r in original.items()},rules='120 team / 72 head / 60 reference / 12 max transfer',no_gameplay_data=True,
      inherited_cutoff=77.5,cutoff_changed=False,prices_fitted_to_deck_totals=False,review_scope='All320 prior schedule identities and all751 benchmark identities screened; explicit judgment proposals separately enumerated. Oracle discovery hits are nominations, not claims of independent human review.')
    files['summary.json']=jt(summary)
    files['source_provenance.json']=jt(dict(source_commit=SOURCE_COMMIT,retrieval_date='2026-10-22',files_sha256=source_manifest,external_evidence=evidence,oracle_snapshot='2026-10-20 pinned; no full live bulk refresh claimed',rules_text_sha256=sha(gzip.open(BASE/'data/comprehensive_rules.gz','rb').read()),activated=False))
    generated_config=dict(version=VERSION,status='season0-proposed',activated=False,team_cap=120,individual_cap=72,individual_reference=60,transfer_limit=12,source_commit=SOURCE_COMMIT,point_schedule='candidate_point_schedule_v3.csv',default_for_known_unlisted='zero_or_unchanged_historical_backend_value',unknown_policy='error',synergy_surcharge=0,automatic_combo_legality=False)
    files['scoring_config_v3.json']=jt(generated_config)
    files.update(render_reports(summary,lineage,audit,schedule,deck_rows,team_rows,prop,source_manifest))
    files['global_recalibration_analysis.md']+='\n### Eighteen-deck descriptive distributions\n\n'+table(distribution,['schedule','n','mean','median','sample_sd','q25','q75','minimum','maximum','over72'])
    stress=[]
    for t in 'ABCDEFGHI':
        rr=[x for x in team_sensitivity if x['team']==t]
        stress.append(dict(team=t,minus_two=rr[0]['total'],central=rr[2]['total'],plus_two=rr[4]['total'],compliant_scenarios=sum(x['budget_compliant'] for x in rr),tested_scenarios=len(rr)))
    files['global_recalibration_analysis.md']+='\n### Joint price-judgment stress scenarios\n\nAll positive agent prices shift together by up to2, flooring at0. Human/working protected prices do not change. Joint shifts are deliberately broad scenarios rather than estimated statistical errors. No team fits120 in any of these five scenarios.\n\n'+table(stress,['team','minus_two','central','plus_two','compliant_scenarios','tested_scenarios'])
    files.update(generate_rules(index,sha,oracle_text,CR_URL,table))
    for path,text in list(files.items()):
        if path.endswith('.md'):files[path]=text.rstrip()+'\n'
    files['artifact_hashes_v3.json']=jt({p:sha(s) for p,s in sorted(files.items())})
    return files

def two_hg_note(c,zone):
    t=oracle_text(c).lower();notes=[]
    if zone=='commanders':notes.append('Guaranteed own access; no partner-pair surcharge; separate actual-zone price.')
    if 'extra turn' in t or 'skip your' in t:notes.append('805.8: added/skipped turn or step applies to whole team.')
    if 'each opponent' in t or 'whenever an opponent' in t:notes.append('Two opponents; actual trigger opportunities and head events remain distinct.')
    if 'life' in t:notes.append('810.9: shared60 value, individual gain/loss events; damage differs from loss.')
    if 'you control' in t or 'your graveyard' in t:notes.append('Only that controller owns/pays/uses stated resources; no merged permanents or graveyards.')
    if 'target player' in t:notes.append('Target may be teammate unless restricted; no implicit multihead targeting.')
    if 'target opponent' in t:notes.append('Teammate is not opponent; one enemy target does not affect both heads.')
    return ' '.join(notes) or 'No additional2HG price multiplier asserted; separate hands, mana and control.'

def family_evidence(f):
    if f in ('extra_turns','shared_life','interaction','lands','mdfc','commanders'):return CR_URL
    if f in ('reusable_engines','reanimation','tutors'):return 'Batches1–3 controller reviews; Commander Spellbook sources in research_evidence.json (component matches not proofs)'
    return 'existing candidate inventory and individual Oracle text; adoption is not power'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args();files=generate()
    if args.check:
        bad=[x for x,s in files.items() if not (HERE/x).exists() or (HERE/x).read_bytes()!=s.encode()]
        if bad:raise SystemExit('Different or missing: '+', '.join(bad))
        print('All global v3 outputs reproduce byte-for-byte; no writes.')
    else:
        for path,text in files.items(): (HERE/path).write_bytes(text.encode())
        print('Generated',len(files),'global recalibration outputs.')
if __name__=='__main__':main()
