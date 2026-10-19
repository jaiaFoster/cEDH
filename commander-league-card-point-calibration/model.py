"""Fixed Oracle-ID model. No deck, cohort, printing, price or popularity input."""
import re, math, json
from pathlib import Path
DEFAULT={
 'version':'0.2.0-provisional','seed':20261019,'as_of':'2026-10-19',
 'global_multiplier':1.0,'nonland_base':2,'basic_land':2,'nonbasic_land':3,
 'land_fixing_bonus':3,'land_tapped_discount':2,'land_utility_bonus':3,
 'efficiency_decay':0.22,'mana_value_knee':2,'body_stats_per_mana':2,'second_role_fraction':0.35,'game_changer_floor':45,
 'high_impact_threshold':30,'team_cap':2000,'individual_cap':0,
 'commander_adjustment':0,'bracket3_design_anchor':1000,
 'role_weights':{'acceleration':20,'advantage':18,'tutor':24,'interaction':20,'board':10},
 'patterns':{
 'acceleration':r'(?i)(?:\{t\}[^.\n]{0,65}:? add |add \{[wubrgc]\}|create[^.\n]{0,65}treasure token|search your library for[^.\n]{0,80}land[^.\n]{0,100}(?:battlefield)|additional land on each|spells? you cast cost[^.\n]{0,30}less)',
 'advantage':r'(?i)(?:draw (?:a|an|two|three|four|five|six|seven|x|that many|cards? equal)|draws? a card|play[^.\n]{0,60}(?:top of your library|from exile)|cast[^.\n]{0,60}from your graveyard|return[^.\n]{0,60}from your graveyard to your hand)',
 'tutor':r'(?i)search your library for (?![^.\n]{0,70}\bland\b)[^.\n]{0,100}card',
 'interaction':r'(?i)(?:destroy (?:target|all|each)|exile (?:target|all|each)|counter target (?:spell|activated|triggered)|return (?:target|all)[^.\n]{0,70}to (?:its|their|the|owner)|target[^.\n]{0,40}gets? -\d+/-\d+|deals? \d+ damage to (?:any target|target creature))',
 'board':r'(?i)(?:create[^.\n]{0,100}(?:creature token|tokens? with)|creatures you control get|double[^.\n]{0,60}(?:power|damage)|additional combat|each opponent loses|damage to each opponent)'
 },
 'repeat_pattern':r'(?i)(?:whenever|at the beginning of|\{t\}[^.\n]*:|\{\d+\}[^.\n]*:)',
 'repeat_multiplier':1.35,'broad_interaction_multiplier':1.25,
 'broad_interaction_pattern':r'(?i)(?:destroy all|exile all|nonland permanent|any target)',
 'overrides':{},
 'override_policy':'Absolute final points, keyed by Oracle ID preferred; exact canonical names also accepted. No legality changes.',
 'coefficient_evidence':'Expert structural priors, not fitted effect sizes or win probabilities. All automatic ratings provisional.'
}
# Reviewed anchors describe functions; values are explicit policy priors, not observed strengths.
ANCHORS={
 'Sol Ring':(65,'One mana for repeatable two-mana acceleration; large opening-hand advantage.'),
 'Arcane Signet':(14,'Two-mana colored acceleration without additional activation cost.'),
 'Command Tower':(7,'Untapped unrestricted commander-color fixing.'),
 'Exotic Orchard':(6,'Usually broad fixing; opponent dependent.'),
 'Fellwar Stone':(13,'Two-mana conditional colored acceleration.'),
 'Cultivate':(12,'Three-mana land acceleration plus land to hand.'),
 "Kodama's Reach":(12,'Functional Cultivate analogue.'),
 'Rampant Growth':(13,'Two-mana basic land acceleration.'),
 "Nature's Lore":(19,'Two-mana Forest acceleration, potentially untapped typed dual.'),
 'Three Visits':(19,'Functional Nature’s Lore analogue.'),
 'Farseek':(16,'Efficient typed land acceleration, tapped.'),
 'Swords to Plowshares':(25,'One-mana unconditional creature exile with modest drawback.'),
 'Path to Exile':(22,'One-mana creature exile; gives opponent a land.'),
 'Beast Within':(20,'Flexible three-mana permanent removal with token drawback.'),
 'Generous Gift':(20,'Flexible three-mana permanent removal with token drawback.'),
 'Counterspell':(22,'Two-mana unconditional counterspell.'),
 'Negate':(15,'Efficient but restricted counterspell.'),
 'Swan Song':(25,'One-mana restricted counterspell with token drawback.'),
 'Cyclonic Rift':(60,'Cheap bounce or asymmetric seven-mana board reset.'),
 'Rhystic Study':(75,'Low-cost repeatable multiplayer card advantage; opponents can pay.'),
 'Mystic Remora':(60,'One-mana multiplayer draw engine, cumulative upkeep.'),
 'Smothering Tithe':(65,'Repeatable multiplayer resource engine.'),
 'Demonic Tutor':(65,'Two-mana unrestricted tutor directly to hand.'),
 'Vampiric Tutor':(60,'One-mana instant unrestricted top-deck tutor, card disadvantage.'),
 'Enlightened Tutor':(45,'One-mana restricted top-deck tutor, card disadvantage.'),
 'Worldly Tutor':(45,'One-mana creature top-deck tutor, card disadvantage.'),
 'Mystical Tutor':(50,'One-mana instant/sorcery top-deck tutor.'),
 'Diabolic Tutor':(12,'Four-mana unrestricted tutor: meaningful tempo cost.'),
 'Diabolic Intent':(45,'Efficient tutor requiring a sacrificed creature.'),
 'Skullclamp':(40,'Highly efficient repeatable draw, requires suitable creatures.'),
 'Esper Sentinel':(40,'Cheap conditional repeatable draw.'),
 'The One Ring':(70,'Protection plus repeatable escalating card draw.'),
 'Necropotence':(70,'Large life-to-cards conversion with timing and discard costs.'),
 "Bolas's Citadel":(55,'Life-paid top-deck casting engine, six-mana entry cost.'),
 'Consecrated Sphinx':(65,'Six-mana high-output opponent-draw engine.'),
 'Seedborn Muse':(50,'Untaps on opposing turns; requires mana sinks.'),
 "Teferi's Protection":(45,'Efficient broad defensive protection.'),
 'Fierce Guardianship':(60,'Conditional free noncreature counterspell.'),
 'Force of Will':(55,'Free counterspell at two-card cost.'),
 'Deflecting Swat':(40,'Conditional free redirection.'),
 'Deadly Rollick':(38,'Conditional free creature exile.'),
 'Flawless Maneuver':(30,'Conditional free creature protection.'),
 'Farewell':(45,'Flexible exile reset; official Game Changer, expensive.'),
 'Austere Command':(18,'Flexible six-mana destroy sweeper.'),
 'Blasphemous Act':(25,'Often one-mana damage sweeper.'),
 'Wrath of God':(20,'Four-mana creature sweeper.'),
 'Toxic Deluge':(35,'Three-mana scalable toughness sweeper with life cost.'),
 'Llanowar Elves':(18,'One-mana creature acceleration with summoning sickness.'),
 'Elvish Mystic':(18,'Functional Llanowar Elves analogue.'),
 'Fyndhorn Elves':(18,'Functional Llanowar Elves analogue.'),
 'Birds of Paradise':(23,'One-mana any-color creature acceleration.'),
 'Mana Vault':(65,'One-mana burst of three mana; costly untap.'),
 'Chrome Mox':(65,'Zero-mana acceleration requiring imprint card.'),
 'Mox Diamond':(65,'Zero-mana acceleration requiring land discard.'),
 'Ancient Tomb':(50,'Untapped land produces two mana at life cost.'),
 "Gaea's Cradle":(70,'Land scales with creature count, no standalone mana on empty board.'),
 'Mana Drain':(40,'Counterspell plus delayed mana advantage.'),
 'Reanimate':(30,'One-mana graveyard-to-battlefield effect with life cost.'),
 'Lightning Greaves':(16,'Low-cost reusable haste and protection; shroud drawback.'),
 'Swiftfoot Boots':(12,'Reusable haste and hexproof with equip cost.'),
 'Temple of the False God':(3,'Two-mana land with substantial early-game failure risk.'),
 'Evolving Wilds':(3,'Tapped basic-land fixing with sacrifice.'),
 'Terramorphic Expanse':(3,'Functional Evolving Wilds analogue.'),
 'Myriad Landscape':(5,'Tapped colorless land with slow two-basic ramp.'),
 'Solemn Simulacrum':(13,'Four-mana ramp body and delayed draw.'),
 'Thran Dynamo':(18,'Four-mana repeatable three-mana acceleration.'),
 'Gilded Lotus':(12,'Five-mana repeatable colored acceleration.'),
 "Commander's Sphere":(8,'Three-mana rock with sacrifice draw.'),
 'Mind Stone':(12,'Two-mana colorless rock with paid sacrifice draw.'),
 'Wayfarer\'s Bauble':(9,'Three total mana split over turns for basic land ramp.'),
 'Dark Ritual':(24,'One-mana temporary net two-mana acceleration.'),
 'Thassa\'s Oracle':(45,'Low standalone impact but compact game-ending enabler; Game Changer floor.'),
}
def load_config():
 p=Path('scoring_config.json')
 if not p.exists():
  # Preserve anchors separately from feature weights so every manual decision is editable.
  DEFAULT['overrides']={n:{'points':p,'reason':r,'evidence':'analyst functional assessment; provisional magnitude'} for n,(p,r) in ANCHORS.items()}
  p.write_text(json.dumps(DEFAULT,indent=2))
 return json.loads(p.read_text())
def features(c,cfg):
 text='\n'.join([c.get('oracle_text','')]+[f.get('oracle_text','') for f in c.get('card_faces',[])])
 # Reminder text is removed before matching; words in reminder examples are not functional effects.
 text=re.sub(r'\([^()]*\)','',text)
 land='Land' in c['type_line'].split(' // ')[0];basic='Basic' in c['type_line'].split(' // ')[0]
 roles={k:0. for k in cfg['role_weights']}
 if not land:
  for role,pat in cfg['patterns'].items():
   if re.search(pat,text):
    repeat=cfg['repeat_multiplier'] if role in ['acceleration','advantage','board'] and re.search(cfg['repeat_pattern'],text) else 1
    broad=cfg['broad_interaction_multiplier'] if role=='interaction' and re.search(cfg['broad_interaction_pattern'],text) else 1
    # One role occurrence per card, never multiply by text match count.
    roles[role]=cfg['role_weights'][role]*repeat*broad
  if 'Creature' in c['type_line']:
   try: body=max(0,float(c.get('power','0'))+float(c.get('toughness','0'))-cfg['body_stats_per_mana']*float(c['cmc']))
   except ValueError: body=0
   roles['board']=max(roles['board'],min(cfg['role_weights']['board'],body))
 if basic:landscore=cfg['basic_land']
 elif land:
  fixing=('{W}' in text and '{U}' in text) or 'any color' in text or len(c.get('produced_mana',[]))>=2
  tapped=bool(re.search(r'enters (?:the battlefield )?tapped',text,re.I))
  utility=bool(re.search(r'draw a card|destroy target|exile target|search your library|creature token',text,re.I))
  landscore=max(0,cfg['nonbasic_land']+fixing*cfg['land_fixing_bonus']-tapped*cfg['land_tapped_discount']+utility*cfg['land_utility_bonus'])
 else:landscore=0
 return text,roles,landscore,land,basic
def score(c,cfg,initial=False):
 text,roles,landscore,land,basic=features(c,cfg)
 efficiency=1/(1+cfg['efficiency_decay']*max(0,c['cmc']-cfg['mana_value_knee'])) if not initial else 1
 ranked=sorted(roles.values(),reverse=True)
 raw=landscore if land else cfg['nonland_base']+efficiency*(ranked[0]+cfg['second_role_fraction']*ranked[1])
 floor=cfg['game_changer_floor'] if c.get('game_changer',False) else 0
 estimated=max(raw,floor);entry=cfg['overrides'].get(c['oracle_id'],cfg['overrides'].get(c['name']))
 value=(entry['points'] if isinstance(entry,dict) else entry) if entry is not None else estimated
 points=math.floor(value*cfg['global_multiplier']+0.5)
 return dict(oracle_id=c['oracle_id'],card_name=c['name'],base_points=points,
  **{k+'_component':round(v*efficiency,4) for k,v in roles.items()},land_component=landscore,
  efficiency_factor=round(efficiency,5),automatic_estimate=math.floor(estimated*cfg['global_multiplier']+0.5),
  override_delta=points-math.floor(estimated*cfg['global_multiplier']+0.5),game_changer=bool(c.get('game_changer')),
  legality=c['legalities'].get('commander','not_legal'),confidence='medium_function_low_magnitude' if entry else 'low_provisional',
  manually_reviewed=entry is not None,notes=entry.get('reason','') if isinstance(entry,dict) else 'Automatic text features; conditional effects and synergy require review.',
  type_line=c['type_line'],mana_value=c['cmc'],color_identity=''.join(c.get('color_identity',[])),oracle_text=text,
  model_version=cfg['version'])
