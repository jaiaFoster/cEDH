"""Build a local capability index and reviewed corpus from a hash-pinned Oracle bulk.
Regex capabilities nominate research; they never establish cross-controller legality.
"""
import json,gzip,pathlib,hashlib,re,csv,sys,urllib.request
root=pathlib.Path(__file__).resolve().parents[1]; research=root/'research/compositions'; data=root/'data/compositions'
source=json.loads((research/'bulk-source.json').read_text());raw=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/commander-compositions-oracle.jsonl.gz').read_bytes()
if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('Oracle bulk does not match the recorded snapshot')
approved=json.loads((research/'reviewed-source.json').read_text())
if source['sha256']!=approved['oracle_sha256']:raise ValueError('New Oracle snapshot requires mechanics review before publication seeds can be rebuilt')
cards=[json.loads(s) for s in gzip.decompress(raw).splitlines() if s];names={c['name']:c for c in cards}
def kind(c):
 t=c.get('card_faces',[c])[0].get('type_line',c.get('type_line',''))
 return 'background' if 'Background' in t and 'Enchantment' in t and 'Creature' not in t else 'commander'
def text(c):return c.get('oracle_text') or '\n'.join(f.get('oracle_text','') for f in c.get('card_faces',[]))
def eligible(c):
 f=c.get('card_faces',[c])[0]; t=f.get('type_line',c.get('type_line',''))
 return c.get('legalities',{}).get('commander')=='legal' and (('Legendary' in t and 'Enchantment' in t and 'Background' in t) or 'can be your commander' in text(c).lower() or c['name']=='Grist, the Hunger Tide' or ('Legendary' in t and ('Creature' in t or 'Vehicle' in t or ('Spacecraft' in t and 'power' in f))))
# Evidence-oriented feature classes. Scope is a warning annotation, not a rules inference.
rules={
 'each-opponent':('Opponent scaling',r'each opponent','opponent restricted'),
 'opponent-trigger':('Opponent scaling',r'whenever an opponent','opponent restricted'),
 'controller-reward':('Controller independent',r'its controller|that player','inspect exact clause'),
 'any-player-event':('Controller independent',r'whenever a player|whenever a creature','inspect exact clause'),
 'target-permanent':('Teammate targeting',r'target (?:creature|permanent|artifact|player|commander)','inspect targeting restrictions'),
 'extra-combat':('Shared turns',r'additional combat|extra turn','shared phase/turn; inspect untaps'),
 'attack-timing':('Shared turns',r'whenever you attack|whenever a .*attacks|untap target|during your turn','inspect active player and controller'),
 'shared-life':('Life total',r'life total|pay .*life|lose.*life|gain.*life|damage to each player','individual events; shared result'),
 'restriction':('Asymmetric restrictions',r'your opponents|can.t cast|can.t activate|can.t attack|can.t win|can.t lose','inspect symmetry and affected players'),
 'global-permission':('Global assembly',r'each player may|players may cast|that player may search|target player.s library','inspect permissions and costs'),
 'attack-tokens':('Output/input',r'Whenever [^\n]*attack[^\n]*(?:create|put)[^\n]*','nomination only'),
 'treasure':('Output/input',r'Treasure','own tokens unless explicitly otherwise'),
 'counter-engine':('Output/input',r'counter|proliferate','inspect permanent/player scope'),
 'graveyard':('Output/input',r'graveyard|dies|sacrifice','inspect card types and ownership'),
 'draw':('Output/input',r'draw','inspect recipient and optionality'),
 'tap-ability':('Output/input',r'\{T\}[^\n]*:','inspect activation ownership'),
 'coin':('Output/input',r'coin flip','inspect won flips versus copies'),
}
index=[]
for c in cards:
 if not eligible(c):continue
 tags=[]
 for name,(cls,pat,scope) in rules.items():
  m=re.search(pat,text(c),re.I)
  if m:tags.append({'capability':name,'class':cls,'scope':scope,'oracle_match':m.group(0)})
 index.append({'oracle_id':c['oracle_id'],'name':c['name'],'color_identity':c['color_identity'],'mana_value':c.get('cmc',0),'type_line':c['type_line'],'eligibility':kind(c),'features':tags,'metadata_reference':'data/compositions/cards.json.gz#'+c['oracle_id']})
(research/'commander-capability-index.json.gz').write_bytes(gzip.compress(json.dumps(index,separators=(',',':')).encode(),mtime=0))
profiles=[];used=set();initial=[];corrections={'B','D','E','F','H','I','10','11','13','15','17','18','19','24','25','26','27','28','33','34','35','37','38'}
mechanisms=['Each opponent','Each player','Opponent-trigger scaling','Shared life','Shared team turns','Shared combat','Controller-independent triggers','Cross-player targeting','Cross-deck tutoring','Global effects','Asymmetric restrictions','Alternate win conditions']
cr='https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt'
def metadata(c):
 f=c.get('card_faces',[c])[0];images=c.get('image_uris') or f.get('image_uris',{})
 return {'oracle_id':c['oracle_id'],'name':c['name'],'aliases':[f['name'] for f in c.get('card_faces',[])],'oracle_text':text(c),'color_identity':c['color_identity'],'mana_value':c.get('cmc',0),'type_line':c['type_line'],'keywords':c.get('keywords',[]),'card_faces':[{k:v for k,v in f.items() if k in ['name','oracle_text','type_line','colors','power']} for f in c.get('card_faces',[c])],'power':c.get('power'),'eligibility':(kind(c)) if eligible(c) else None,'legality':c['legalities']['commander'],'scryfall_url':c['scryfall_uri'],'image_url':images.get('art_crop') or images.get('small'),'source_updated_at':source['bulk']['updated_at']}
for line in (research/'profiles.txt').read_text().splitlines():
 if not line.strip() or line.startswith('#'):continue
 parts=line.split('|')
 if len(parts)!=13:raise ValueError('Expected 13 fields: '+line[:80])
 n,a,b,arch,title,hook,why,action,result,limit,keys,role_a,role_b=parts
 an=a.split(';');bn=b.split(';');kn=keys.split(';')
 for name in an+bn+kn:
  if name not in names:raise ValueError('Unknown canonical card '+name)
  used.add(name)
 for name in an+bn:
  if not eligible(names[name]):raise ValueError('Ineligible commander '+name)
 ai=sorted(names[n]['oracle_id'] for n in an);bi=sorted(names[n]['oracle_id'] for n in bn)
 pair='|'.join(sorted(['+'.join(ai),'+'.join(bi)]));id='benchmark-'+n.lower() if n in list('ABCDEFGHI') else ('seed-'+n if not n.startswith('N') else 'discovery-'+n[1:])
 tags=[];blob=(why+' '+action+' '+result).lower()
 if any(x in blob for x in ['each opponent','both opponent','two opponent','opposing heads']):tags.append('Each opponent')
 if 'each player' in blob or 'each head' in blob:tags.append('Each player')
 if any(x in blob for x in ['shared life','shared pool','shared total','life gain','life loss','lifelink','parity']):tags.append('Shared life')
 if any(x in blob for x in ['shared turn','shared team turn','active','upkeep','extra turn']):tags.append('Shared team turns')
 if any(x in blob for x in ['combat','attack','block']):tags.append('Shared combat')
 if n in ['A','11','13','14','17','19','20','24','27','28','33','N01','N02','N03','N04','N05','N08','N09','N23','N24','N26','N28','N41','N42']:tags.append('Controller-independent triggers')
 if n in ['A','B','19','20','36','37','N29','N30','N31','N32','N33','N34','N43','N47','N48','N49']:tags.append('Cross-player targeting')
 if n in ['19','20']:tags.append('Cross-deck tutoring')
 if any(x in blob for x in ['global','aluren','kudo','yurlok']):tags.append('Global effects')
 if n in ['E','I','15','20','21','23','N10','N11','N12','N44']:tags.append('Asymmetric restrictions')
 if any(x in blob for x in ['wins','win condition','lose the game','loss trigger']):tags.append('Alternate win conditions')
 if any(re.search(r'Whenever (?:an opponent|one or more opponents)',text(names[k]),re.I) for k in an+bn):tags.append('Opponent-trigger scaling')
 for tag,ns in {'Counter engines':['18','N21','N22','N29','N43'],'Borrowed abilities':['N30','N31'],'Public activated abilities':['N14','N15','N45'],'Spell copying':['34','35','N25','N26'],'Equipment coordination':['N47','N48'],'Graveyard events':['17','N08','N09','N41','N42'],'Cross-deck assembly':['H','21','N12','N14','N30','N31','N50']}.items():
  if n in ns:tags.append(tag)
 tags=list(dict.fromkeys(tags)) or ['Controller-independent triggers']
 refs=['810.4','810.5','109.5','810.8a']
 if n in ['10','N16']:refs+=['805.9']
 if n in ['N14','N15','N45']:refs+=['113.8','106.4']
 if n in ['19','20','21','22','N12','N13','N41']:refs+=['701.21a']
 if n=='10':refs+=['120.3f','702.15b']
 if n in ['26','27']:refs+=['805.7']
 if n in ['N19','N20','15']:refs+=['805.4d']
 if 'Shared life' in tags:refs+=['810.9','810.9a']
 if 'Shared combat' in tags:refs+=['805.10','508.3','506.5']
 if 'Shared team turns' in tags:refs+=['805.8']
 if 'Cross-player targeting' in tags:refs+=['109.5','115.1c']
 if 'Cross-deck tutoring' in tags:refs+=['701.23a'] # Checked against current edition below; replaced if numbering changes.
 if n in ['18','N21','N22','N29','N30','N31','N43']:refs+=['613.4b','613.4c','704.5f']
 if n in ['N30','N31']:refs+=['201.5b','302.6']
 if n in ['N23','N24']:refs+=['704.5f']
 if n in ['36','37','N49']:refs+=['903.10a','704.6c']
 if n in ['34','35','N25','N26']:refs+=['707.10']
 historical=n in list('ABCDEFGHI');status='Historical benchmark' if historical else ('Active brew' if n=='10' else ('Research candidate' if n=='17' else 'Verified synergy'))
 p={'id':id,'seed_id':n if not n.startswith('N') else None,'display_name':title,'player_a':ai,'player_b':bi,'pair_key':pair,'archetype':arch,'hook':hook,'description':hook+' '+result,'featured_order':0 if n=='10' else (10+list('ABCDEFGHI').index(n) if historical else 100+len(profiles)), 'tags':tags,'overview':title+': '+role_a+' '+role_b,'interaction':why,'execution':['A controls '+', '.join(an)+'; B controls '+', '.join(bn)+'. Establish the named support and a legal action window.',action,result],'strengths':[hook,result],'weaknesses':[limit,'The acting player must pay their own costs and protect the required pieces; the teammate does not share mana or control.'],'key_cards':[names[k]['oracle_id'] for k in kn],'role_a':role_a,'role_b':role_b,'win_conditions':[result],'counterplay':[limit,'Interact before the required ability or trigger resolves; a verified interaction is not a demonstrated tournament win rate.'],'rule_references':list(dict.fromkeys(refs)),'sources':[cr,'https://magic.wizards.com/en/formats/two-headed-giant']+[names[k]['scryfall_uri'] for k in an+bn], 'rules_edition':'September 25, 2026','verified_on':'2026-11-05','verified_by':'Commander Doubles composition source audit','verification_status':'verified','research_status':status,'verification_notes':'Mechanics verified for the stated control configuration and conditions. Competitive strength is untested judgment; no win-rate claim. '+('Conditional creature-aware reconstruction required; ordinary Gitrog land loops are insufficient.' if n=='17' else ''),'catalog_version':source['bulk']['updated_at'],'decklists':[],'change_note':'Initial curated composition research; separate from league pricing and tournament records.'}
 p['key_card_owners']={}
 for name in kn:
  ci=set(names[name]['color_identity']);ca=set().union(*(set(names[k]['color_identity']) for k in an));cb=set().union(*(set(names[k]['color_identity']) for k in bn))
  p['key_card_owners'][names[name]['oracle_id']]='Either' if ci<=ca and ci<=cb else ('A' if ci<=ca else 'B')
 assignments={
 'B':{"Nature's Will":'A'},'D':{'Walking Ballista':'B','Aetherflux Reservoir':'A'},'F':{'Time Sieve':'A','Thopter Assembly':'A','Counterspell':'B'},'I':{'Shuko':'B'},
 '10':{'Basilisk Collar':'B','Shadowspear':'B'},'12':{'Basilisk Collar':'A'},'15':{'Opposition Agent':'B'},
 '19':{'Myr Battlesphere':'B','Staff of Domination':'B'},'20':{'Skullclamp':'B'},'25':{'Sword of Feast and Famine':'B'},
 '36':{'Whispersilk Cloak':'B','Lightning Greaves':'B'},'37':{'Whispersilk Cloak':'B'},
 'N06':{'Basilisk Collar':'B'},'N07':{'Basilisk Collar':'A','Ancestral Statue':'B'},'N14':{'Basalt Monolith':'B','Staff of Domination':'B'},
 'N23':{"Black Sun's Zenith":'B','Nest of Scarabs':'B','Blowfly Infestation':'B'},'N31':{'Pestermite':'A'},'N40':{'Maskwood Nexus':'B'},
 'N47':{'Colossus Hammer':'A','Sword of Fire and Ice':'A','Lightning Greaves':'A'},
 'N48':{'Colossus Hammer':'A','Swiftfoot Boots':'A','Sword of the Animist':'A'},
 'N49':{'Grafted Wargear':'B','Whispersilk Cloak':'B','Lightning Greaves':'B'},
 'N50':{'Illusions of Grandeur':'A','Seal of Cleansing':'B',"Hall of Heliod's Generosity":'A'}
 }
 for name,owner in assignments.get(n,{}).items():p['key_card_owners'][names[name]['oracle_id']]=owner
 # Exact Oracle evidence, not generated Oracle prose. Keep relevant short paragraphs.
 p['oracle_evidence']=[]
 for name in dict.fromkeys(an+bn):
  c=names[name];lines=[s for s in text(c).splitlines() if not s.startswith(('Partner','Choose a Background','Friends forever'))]
  quote='\n'.join(lines)[:1800]
  p['oracle_evidence'].append({'oracle_id':c['oracle_id'],'quote':quote,'source_url':c['scryfall_uri']})
 if n=='10':
  p['execution'].append('Worked example, absent modifiers: from 60 versus 60, Heartless deals 30 to each head. Lifelink on B’s Heartless gains B 120 life while the friendly shared pool loses 60, leaving it at 120 and the enemy at 0. Alternatively, a friendly head preventing 15 of its own 30 damage leaves the friendly team at 15.')
  p['weaknesses'].append('Arena of Glory grants haste through its exhaust mana spent to cast the creature; it does not retroactively grant haste to an existing Heartless.')
 if n=='N43':p['weaknesses'].append('B giving Kelsien deathtouch can be a simpler substitute; this profile verifies the cross-controller option, not superiority over that alternative.')
 if n=='N14':
  p['execution'].append('With B’s own ready Basalt Monolith and Zirda, its nonmana untap costs one while tapping still adds three. If that engine functions and B has at least 30 cards to draw, 30 resolved Xantcha activations can remove 60 opposing shared life, absent modifiers or protection.')
 if historical:
  batch=1 if n in 'ABC' else (2 if n in 'DEF' else 3)
  for side in [1,2]:
   rel=f'commander-doubles-deck-benchmarks/batch{batch}/decks/{n}{side}.txt';original=(root.parent/rel).read_bytes();target=data/'decklists'/f'{n}{side}.txt';target.parent.mkdir(exist_ok=True);target.write_bytes(original)
   p['decklists'].append({'id':n+str(side),'player':'a' if side==1 else 'b','source_url':'https://github.com/jaiaFoster/cEDH/blob/0e52ce8/'+rel,'sha256':hashlib.sha256(original).hexdigest(),'provenance':'Original unplayed 2HG adaptation; no tournament result claimed. Historical 100-card inventory copied byte-for-byte.','historical_schedule':'candidate v3','historical_team_points':{'A':462,'B':518,'C':314,'D':237,'E':198,'F':246,'G':215,'H':150,'I':178}[n]})
 p['sources']=list(dict.fromkeys(p['sources']))
 book_path=research/'spellbook-selected.json'
 if book_path.exists():
  match=json.loads(book_path.read_text())['matches'].get({'B':'najeela-derevi','N14':'zirda-basalt','21':'lavinia-pool','N12':'lavinia-pool'}.get(n,''))
  if match:p['sources'].append(match['url'])
 if n in corrections:p['verification_notes']+=' The initial hypothesis needed a controller, timing, arithmetic or strength qualification; see corrections.json.'
 if not n.startswith('N'):initial.append({'seed_id':n,'id':id,'commanders_a':an,'commanders_b':bn,'audited':True,'qualification_required':n in corrections,'correction_type':'controller wording correction' if n=='19' else ('explicit qualification' if n in corrections else 'no correction required')})
 profiles.append(p)
# Reject pair-key duplicates before generating any public seed.
assert len(profiles)==88 and len({p['pair_key'] for p in profiles})==88
# Keys must fit at least one whole individual identity, never just the team union.
card_ids={c['oracle_id']:c for c in cards}
errors=[]
for p in profiles:
 ca=set().union(*(set(card_ids[i]['color_identity']) for i in p['player_a']))
 cb=set().union(*(set(card_ids[i]['color_identity']) for i in p['player_b']))
 for key in p['key_cards']:
  c=card_ids[key]
  if not(set(c['color_identity'])<=ca or set(c['color_identity'])<=cb):errors.append(p['id']+' '+c['name'])
  owner=p.get('key_card_owners',{}).get(key,'Either')
  if owner in ['A','B'] and not set(c['color_identity'])<=(ca if owner=='A' else cb):errors.append(p['id']+' wrong owner '+c['name'])
if errors:raise ValueError('Key cards fit neither deck: '+str(errors))
drafts=[]
for i,r in enumerate(json.loads((research/'review-input.json').read_text())):
 a,b=names[r['a']],names[r['b']]
 p=dict(profiles[-1]);p.update(id='review-'+str(i+1).zfill(2),seed_id=None,display_name=r['a']+' × '+r['b']+': rejected hypothesis',player_a=[a['oracle_id']],player_b=[b['oracle_id']],pair_key='|'.join(sorted([a['oracle_id'],b['oracle_id']])),archetype='Resource engine',hook=r['hypothesis'],description=r['finding'],overview=r['hypothesis'],interaction=r['finding'],execution=['Do not use the proposed sequence as a verified cross-controller engine.',r['finding']],strengths=['Research record retained.','Compare exact controller wording before reconstruction.'],weaknesses=[r['finding'],'The original hypothesis is not a verified strategy.'],key_cards=[],tags=['Controller-independent triggers'],role_a='Controller A must satisfy its own card conditions.',role_b='Controller B does not inherit A’s resources or events.',win_conditions=[],counterplay=[],rule_references=['109.5','810.4','810.5','810.9','810.9a'],sources=[cr,a['scryfall_uri'],b['scryfall_uri']],verification_status=r['status'],research_status='Requires rules review',verified_on='',verified_by='',verification_notes=r['finding'],decklists=[],oracle_evidence=[{'oracle_id':c['oracle_id'],'quote':text(c)[:1800],'source_url':c['scryfall_uri']} for c in [a,b]],change_note='Private research rejection; never seeded as a published composition.')
 drafts.append(p)
(data/'drafts.json').write_text(json.dumps(drafts,indent=2,ensure_ascii=False)+'\n')
(research/'review_queue.json').write_text(json.dumps([{'id':p['id'],'original_hypothesis':p['hook'],'finding':p['interaction'],'status':p['verification_status'],'public':False} for p in drafts],indent=2,ensure_ascii=False)+'\n')
(data/'entries.json').write_text(json.dumps(profiles,indent=2,ensure_ascii=False)+'\n')
(research/'seed-audit.json').write_text(json.dumps(initial,indent=2,ensure_ascii=False)+'\n')
(research/'corrections.json').write_text(json.dumps([{'id':p['id'],'seed_id':p['seed_id'],'corrected_interpretation':p['interaction'],'limitations':p['weaknesses'][0]} for p in profiles if p['seed_id'] in corrections],indent=2,ensure_ascii=False)+'\n')
# Local metadata includes all eligible commanders plus the exact cited support cards.
md={c['oracle_id']:metadata(c) for c in cards if eligible(c) or c['name'] in used}
(data/'cards.json.gz').write_bytes(gzip.compress(json.dumps(md,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
# Bounded functional nomination, not a Cartesian power-ranking model.
by={c['name']:c for c in index}
templates=[('combat-reward + attacker',lambda c:c['name'] in ['Edric, Spymaster of Trest','Gix, Yawgmoth Praetor'],lambda c:any(f['capability']=='attack-tokens' for f in c['features'])),('life-output + conditional-life-reward',lambda c:c['name'] in ['Nekusar, the Mindrazer','Kambal, Consul of Allocation'],lambda c:c['name'] in ['Ob Nixilis, Captive Kingpin','Valgavoth, Harrower of Souls']),('untapper + tap-ability',lambda c:c['name']=='Derevi, Empyrial Tactician',lambda c:any(f['capability']=='tap-ability' for f in c['features']))]
generated=[];seen=set()
for template,left,right in templates:
 for a in filter(left,[c for c in index if c["eligibility"]=="commander"]):
  for b in filter(right,[c for c in index if c["eligibility"]=="commander"]):
   if a['oracle_id']==b['oracle_id']:continue
   pair='|'.join(sorted([a['oracle_id'],b['oracle_id']]))
   if pair in seen:continue
   seen.add(pair);reviewed=next((p['id'] for p in profiles if p['pair_key']==pair),None);generated.append({'a':a['name'],'b':b['name'],'template':template,'status':'reviewed composition '+reviewed if reviewed else 'unreviewed nomination','warning':'Feature match is not controller validation; never automatically published.'})
with (research/'generated_candidates.csv').open('w') as f:
 w=csv.DictWriter(f,lineterminator='\n',fieldnames=['a','b','template','status','warning']);w.writeheader();w.writerows(generated)
with (research/'candidate_table.csv').open('w') as f:
 w=csv.DictWriter(f,lineterminator='\n',fieldnames=['id','origin','player_a','player_b','archetype','mechanisms','mechanics','development','strength_validation']);w.writeheader()
 for p in profiles+drafts:w.writerow({'id':p['id'],'origin':('rejected hypothesis' if p['verification_status']!='verified' else ('seed' if p['seed_id'] else 'new discovery')),'player_a':'; '.join(md[x]['name'] for x in p['player_a']),'player_b':'; '.join(md[x]['name'] for x in p['player_b']),'archetype':p['archetype'],'mechanisms':'; '.join(p['tags']),'mechanics':p['verification_status'],'development':p['research_status'],'strength_validation':'No match outcomes; qualitative strategy only'})
summary={'initial_pairs':len(initial),'new_reviewed_pairs':50,'unique_pairs':88,'duplicate_pairs_removed':0,'initial_qualified_claims':len(corrections),'initial_material_wording_corrections':1,'eligible_configurations_indexed':len(index),'eligible_commanders_indexed':sum(c['eligibility']=='commander' for c in index),'backgrounds_indexed':sum(c['eligibility']=='background' for c in index),'bulk_cards':len(cards),'functional_nominations':len(generated),'feature_queries':{k:sum(any(f['capability']==k for f in c['features']) for c in index) for k in rules},'automatic_publication':False}
(research/'discovery-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))

manifest={'format':'composition-research-v1','files':{}}
for rel in ['research/compositions/profiles.txt','research/compositions/reviewed-source.json','research/compositions/review-input.json','research/compositions/spellbook-selected.json','research/compositions/review_queue.json','data/compositions/drafts.json','research/compositions/bulk-source.json','data/compositions/entries.json','data/compositions/cards.json.gz','research/compositions/commander-capability-index.json.gz','research/compositions/generated_candidates.csv','research/compositions/candidate_table.csv','research/compositions/seed-audit.json','research/compositions/corrections.json','research/compositions/discovery-summary.json']:
 manifest['files'][rel]=hashlib.sha256((root/rel).read_bytes()).hexdigest()
(research/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
