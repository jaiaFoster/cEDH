"""Build persistent controller-aware ruling cache from pinned current primary sources."""
import gzip,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
CR='https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt'
# card groups, exact references, ruling, pricing implication, prerequisites
ADDITIONAL=[
('R43',['Final Fortune','Last Chance',"Warrior's Oath",'Sundial of the Infinite',"Angel's Grace"],['805.8','810.8a','603.7','724.1'],
 'Extra turn belongs to entire team. Delayed loss loses team; Grace must resolve during that extra turn. Sundial controlled by either friendly head may end the shared turn with loss trigger already on stack; Fortune-family text names THAT extra turn end step: ending earlier skips it, rather than deferring it. Distinct generic NEXT-end-step triggers can wait for a later end step if ended before triggering.',
 'Tax cheap extra team turn at seven; Sundial two is setup support, not priced like the offensive engine.', 'Loss trigger on stack, untapped Sundial, one mana, friendly turn; or Grace W held during the relevant extra turn.'),
('R44',['Time Warp','Temporal Manipulation','Capture of Jingzhou','Temporal Mastery','Temporal Trespass','Nexus of Fate','Walk the Aeons','Time Stretch'],['805.8','500.7'],
 'Each awarded extra turn is a full team turn. Card-specific costs, exile, delve, miracle or sacrifice requirements still belong to controller.',
 'Six or seven for efficient extra-team-turn spells; no assumption of free recursion.', 'Resolve spell and pay its actual cost; miracle timing/topdeck and delve colored costs are not waived.'),
('R45',['Savor the Moment'],['805.8','805.4b','805.4c'],
 'Entire friendly team takes extra turn and skips its untap step. Each friendly player still draws/plays land and may attack with untapped or vigilant creatures.',
 'Five proposed, below complete cheap team turns; not a full-untap spell.', 'Have untapped resources or use draw/land/combat advantage; no hidden teammate untap.'),
('R46',['Expropriate'],['805.8','500.7'],
 'Caster and teammate may both vote time; each time vote adds a turn for caster, hence team. Two friendly time votes give two turns, not one per effect. Opponent money votes transfer permanent owned by that voter to caster.',
 'Working seven: nine mana limits speed despite at least two cooperative extra turns.', 'Resolve nine-mana spell, each head votes independently; opponents choose their own votes.'),
('R47',['Mindslaver','Emrakul, the Promised End'],['805.8','723.1','723.3'],
 'Control of one opponent during next turn controls that whole opposing team. Emrakul then awards that opposing team a compensating extra turn; Mindslaver does not. Object controllers and mana ownership remain separate.',
 'Mindslaver accepted five; Emrakul proposed eight main/ten CZ, not free guaranteed lock.', 'Resolve ability/cast trigger. Cannot force concessions; turn controller bound by legal actions.'),
('R48',['Necropotence','Necrodominance'],['805.8','805.4b','810.9a','810.9b'],
 'Skip your draw step skips shared team draw step, so teammate also misses ordinary draw. Necropotence exiles and later puts cards into hand; this is not drawing. Necrodominance draws; life payments reduce shared pool.',
 'Necropotence fifteen approved range, Necrodominance twelve proposed with team draw downside.', 'Own activation/payment only; neither engine gives teammate cards or permission to pay your costs.'),
('R49',['Ad Nauseam',"Bolas's Citadel", "K'rrik, Son of Yawgmoth",'Sylvan Library'],['109.5','810.9a','810.9b','810.9h','903.8'],
 'Shared sixty funds controller life costs/loss; reveals/casts/cards stay individual. Krrik substitutes only own black symbols; generic commander tax still needs mana. Protection prohibiting life-total change prevents nonzero life payment.',
 'High life-engine prices, not blanket taxes on every life-related card.', 'Pay each required cost legally; team pool cannot be spent twice. Own library, permanents, cards and costs only.'),
('R50',['Sorin Markov','Hidetsugu\'s Second Rite','Aetherflux Reservoir','Test of Endurance','Felidar Sovereign'],['810.9a','810.9c','810.8a'],
 'Setting a head life to ten adjusts shared team to ten. Second Rite can then deal ten if its target still has ten at resolution. Reservoir one fifty-damage hit is not lethal from sixty. Test/Felidar see team life but trigger only at own upkeep with intervening condition.',
 'Organizer Sorin five, Reservoir one, Test working seven within six-eight, Felidar two.', 'Sorin -3 loyalty available and legal target; Rite ten-life condition; enchantment/creature survives until upkeep; no life prevention or replacement defeating line.'),
('R51',['Heartless Hidetsugu',"Angel's Grace","Teferi's Protection",'Fraying Omnipotence'],['810.9','810.9a','810.8a','704.5a'],
 'At shared sixty, two opposing head events each deal/lose thirty: total sixty. Unprotected symmetric activation can draw game; even/odd life, prevention and cannot-lose change result. Grace does not grant persistent team immunity; Protection freezes shared pool but phases out only own permanents.',
 'Proposed Hidetsugu eight main/twelve CZ, Fraying four; defensive cards retain separate lower prices.', 'Friendly survival asymmetry, usable Hidetsugu tap ability or resolve Fraying, relevant even/odd pool and damage/loss replacements checked.'),
('R52',['Narset, Parter of Veils','Notion Thief','Windfall','Wheel of Fortune','Timetwister','Consecrated Sphinx'],['109.5','805.4b','805.6a','810.5'],
 'Narset caps each opposing head draws individually per shared turn. Thief exempts each opponent first draw in their draw step, replaces others with own draw. Friendly draws trigger neither opposing-only Thief nor Sphinx; neither is a friendly draw loop.',
 'Narset working three, Thief five, Sphinx one; distinguish asymmetry from symmetric wheel.', 'Track each opposing head draw history. Wheel resolves with relevant restriction/Thief still present.'),
('R53',['Seedborn Muse','Smothering Tithe','Breena, the Demagogue','Silence',"Orim's Chant",'Cyclonic Rift'],['109.5','805.4','805.4b','810.5','810.9a'],
 'One opposing shared untap supports Muse once, only own permanents. Each opposing head draws and can trigger Tithe. Breena compares equal opposing shared life so strict comparison fails. Silence forbids both opponents spells; Chant targets one head only. Overloaded Rift affects teammate nonland permanents not controlled by caster.',
 'Muse working zero, Breena CZ zero proposed; Silence premium and Chant not literally equivalent; Rift human free.', 'Ordinary four-player two-team game, separate controllers. Spell prohibitions do not counter spells already on stack or forbid activated abilities.'),
('R54',['Time Sieve','Tivit, Seller of Secrets','Wanderwine Prophets','Sage of Hours','Timestream Navigator','Lighthouse Chronologist'],['805.8','701.21a','302.6'],
 'Sieve sacrifices five artifacts its controller controls. Tivit provides five vote artifacts in a four-player game with its extra vote, but split Tivit/Sieve cannot sacrifice teammate artifacts. Each successful Prophets/Sage/Navigator/Chronologist extra turn is a team turn, not two turns for two heads.',
 'Tax recurring converters by realistic setup and deployment; do not tax every artifact/token producer.', 'Sieve untapped; own five artifacts. Prophets connects and sacrifices own Merfolk; Sage has five counters; Navigator ascend/tap and four mana; Chronologist leveled and opposing end step.'),
('R55',['False Cure','Beacon of Immortality','Tainted Remedy'],['810.9a','810.9','603.2','614.1'],
 'Beacon on opponent at sixty produces gain sixty. Cure triggers that head to lose twice actual gain: team 120 then loses120 to zero. Remedy instead replaces gain sixty with loss sixty. Split friendly controllers can function because Cure global/Remedy opponent conditions match.',
 'Slow multi-card life conversion remains a separate review case, not an automatic combo surcharge.', 'Opposing sixty, Beacon six mana plus Cure BB on same turn or Remedy already present; responses/life replacements can defeat line.'),
('R56',['Obeka, Brute Chronologist'],['805.8','724.1'],
 'Obeka gives player whose turn it is the choice to end it. On shared team turn teammates can agree to end; cannot force opponents to accept end of their turn.',
 'CZ three proposed for guaranteed loss-trigger bypass, not unlimited forced opponent turn skipping.', 'Untapped Obeka not summoning sick; relevant player accepts; correct trigger timing as with Sundial.'),
]
def generate_rules(index,prior):
 manifest=json.loads((HERE/'data/source_snapshot_manifest.json').read_text());rules=gzip.decompress((HERE/'data/comprehensive_rules.gz').read_bytes()).decode('utf-8-sig')
 records=[]
 for c in prior['combos']:
  records.append({'id':c['id'],'names':list(dict.fromkeys(c['cards_A']+c['cards_B'])),'rules':c['rules_citations'].split(';'),'ruling':c['outcome'],'controller_configuration':{'A':c['cards_A'],'B':c['cards_B']},'prerequisites':c.get('required_game_state','See pinned prior controller analysis; game-state verification required.'),'pricing_implications':'No combo/team surcharge; price individual cards separately.','status':c['status'],'source_analysis':'commander-doubles-final-audit/team_combo_database.csv'})
 for ident,names,refs,ruling,pricing,prereq in ADDITIONAL:
  records.append({'id':ident,'names':names,'rules':refs,'ruling':ruling,'controller_configuration':'Controller owns each referenced you/your resource; explicitly described cross-team split only.','prerequisites':prereq,'pricing_implications':pricing,'status':'verified_conditional_interpretation'})
 for r in records:
  r['cards']=[]
  for name in r.pop('names'):
   oid=index.resolve(name);c=index.cards[oid]
   text=c.get('oracle_text') or '\n'.join(f.get('oracle_text','') for f in c.get('card_faces',[]))
   r['cards'].append({'oracle_id':oid,'card_name':c['name'],'current_oracle_text':text,'oracle_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'source_url':'https://api.scryfall.com/cards/'+c['id'],'commander_legality':c.get('legalities',{}).get('commander')})
  refs=[];unresolved=[]
  for ref in r.pop('rules'):
   ref=ref.strip()
   # Prior prose sometimes includes broad rule families; retain each exact enumerated rule or explicit unresolved marker.
   for token in re.findall(r'\b\d{3}(?:\.\d+[a-z]?)?\b',ref):
    if any(line.startswith(token+'.') or line.startswith(token+' ') for line in rules.splitlines()):refs.append(token)
    else:unresolved.append(token)
  r.update({'version':'2hg-cache-2026-10-20-v1','verified_date':'2026-10-20','comprehensive_rules_effective':'2026-09-25','exact_rule_references':list(dict.fromkeys(refs)),'unresolved_rule_references':unresolved,'rule_source_url':CR,'source_urls':[CR,'https://magic.wizards.com/en/formats/two-headed-giant','https://scryfall.com/docs/api/bulk-data'],'rules_sha256':manifest['official']['comprehensive_rules']['sha256'],'oracle_snapshot_updated_at':manifest['oracle_bulk']['updated_at'],'shared_team_vs_individual':'Shared turn and life; hands/mana/ownership/control remain individual. Outcome only under listed prerequisites.','invalidators':['Changed Oracle text of a component','Changed cited CR clause','Different team size, starting life, controller configuration or loss/turn house rule'],'automatic_combo_certification':False})
  if unresolved:r['status']='unresolved_citation_recheck_required'
 return records
ADDITIONAL += [
('R57',['Magosi, the Waterveil','Second Chance'],['805.8','810.9a'],
 'Magosi skips a whole future team turn when storing an eon counter; cashout needs own land and returns it. Second Chance tests shared life at own upkeep and sacrifices itself. Neither is automatically a free repeating team-turn loop.',
 'Magosi stays free; Second Chance two proposed for narrow low-life conversion.', 'Own counter/land/trigger and actual shared-life threshold; additional counter or recursion machinery separately required.'),
('R58',['Havoc Festival','Fraying Omnipotence'],['805.4d','810.9a','810.9g'],
 'Havoc Festival creates separate per-player upkeep triggers. At sixty, resolve first half-loss to thirty, second queries thirty and loses fifteen, leaving fifteen. Fraying single simultaneous each-player loss instead computes thirty per head from sixty, leaving zero.',
 'Do not price every half-life effect as identical; Fraying proposed four is based on simultaneous team-life conversion.', 'No replacement/prevention or intervening life changes; both upkeep triggers resolve normally.'),
('R59',['Perch Protection','Eon Frolicker',"Teferi's Protection"],['805.8','810.5','810.9h'],
 'Gift/opponent extra turns go to OPPOSING team, not friendly team. Protective you wording does not automatically phase out or protect teammate permanents. Shared life freeze applies team pool; that does not freeze other loss conditions.',
 'Defensive gift/turn prevention cards stay free; organizer Teferi three remains distinct.', 'Actual promised gift/cast condition, separate controllers and legal target opponent.'),
('R60',['Teferi, Master of Time','Plea for Power','Lighthouse Chronologist'],['805.4','606.3','805.8'],
 'Teferi does not get two loyalty activations just because two heads share a turn. Plea opponents can each choose knowledge, tie two friendly time votes and force draw-three. Chronologist triggers once at opposing shared end step, not once per head.',
 'Teferi/Plea free after explicit family review; Chronologist five proposed for leveled recurring team-turn engine.', 'No additional independent activation permissions. Each head votes separately, ties follow printed text.'),
('R61',['Hatred','Unspeakable Symbol','Children of Korlis','Tree of Perdition'],['109.5','810.9a','810.9c','810.9','903.10a'],
 'Life-payment boosts use shared pool but improve own/target creature as printed. Children counts life its controller lost, not all friendly losses. Tree exchanges target opposing life/team pool with its own toughness; separate control and summoning sickness remain.',
 'Hatred three/Symbol three/Children one/Tree two are specialized proposals, not an automatic tax on all life text.', 'Own life costs affordable, attack actually connects, individual commander-damage tracking, tap eligibility and life replacements verified.'),
]
ADDITIONAL += [
('R62',["Nature's Will",'Bear Umbra','Sword of Feast and Famine',"Druids' Repository"],['109.5','603.3a','810.5','805.10'],
 'Nature Will checks creatures its own controller controls and untaps that controller lands. Bear Umbra grants a triggered ability to enchanted creature: teammate creature means teammate controls trigger and untaps teammate lands. Sword trigger remains on equipment: A Sword on B attacker untaps A lands. Repository counts own attacking creatures and mana goes to its controller.',
 'Proposed Nature Will four, Umbra/Sword/Repository three; no commander-pair premium. Controllers determine resources, not team-wide mana sharing.',
 'Actual attack/connection as printed, legal attachment/control, own available mana resources, instant removal/countering trigger can interrupt.'),
]
