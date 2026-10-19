"""Experimental prices are policy scenarios, never permission to play a card."""
import re
from bs4 import BeautifulSoup
SPECIAL={
 'Primeval Titan':(75,'Repeatable any-two-land tutor plus 6/6 body; six-mana entry.','Finds utility lands and can supply a team plan; only controller gets the lands.','Fast mana-land chains, repeatable land tutoring; not intrinsically an immediate win.','Controlled testing only; predeclare land targets'),
 'Prophet of Kruphix':(90,'Untaps creatures and lands plus creature flash, a repeatable resource engine.','One opposing team turn per round gives fewer separate untaps than four-player FFA; still enables reactive team protection.','Repeated resource dominance and flash engines.','Retain ban pending dedicated testing'),
 'Golos, Tireless Pilgrim':(70,'ETB any-land tutor, five-color identity and repeatable free casting.','Reliable personal mana development can support a coordinated team plan.','Command-zone consistency, blink loops and powerful land targets.','Additional review; test only with commander access tracked'),
 'Rofellos, Llanowar Emissary':(85,'Two-mana commander can produce mana proportional to Forests.','Early resources belong to one player but teammate can protect engine.','Explosive early deployment; command-zone access is a major missing model term.','Retain ban'),
 'Dockside Extortionist':(110,'Two-mana ETB treasures proportional to opposing artifacts/enchantments.','Only two opponents rather than three in usual four-player FFA; teammate permanents do not count.','Treasure bursts, bounce and reanimation loops.','Retain ban'),
 'Jeweled Lotus':(85,'Zero-mana one-shot three mana restricted to commander.','Accelerates one commander; teammate can defend it; cannot pay teammate costs.','Early command-zone snowballing; varies dramatically by commander mana cost.','Retain ban'),
 'Mana Crypt':(100,'Zero-mana repeatable two-mana acceleration with random life loss.','Shared 60-life start makes life-loss drawback less restrictive relative to starting total.','Very early explosive development; easily reused in most decks.','Retain ban'),
 'Trade Secrets':(100,'Cheap draw spell permits repeated opponent cooperation.','Can target a teammate: voluntary repeatable draw is especially problematic.','Team collusion draw engine; point budget does not fix behavior.','Retain ban'),
 'Limited Resources':(100,'One-mana land sacrifice and land-play restriction.','Counts lands across four players; team coordination can monopolize land access.','Early persistent game lock.','Retain ban'),
 'Erayo, Soratami Ascendant':(100,'Flips into a repeatable first-spell counter effect.','Team can coordinate four spells; additionally explicitly banned in all constructed 2HG.','Early lock with other denial pieces.','Retain ban'),
 'Lutri, the Spellchaser':(15,'Three-mana flash body and conditional spell copy.','Normal mainboard or commander use is legal; companion access is prohibited.','Companion would add near-free access to extra card.','Keep companion ban; no unban needed for mainboard'),
}
# Functional reviews from the retained Oracle text; point magnitudes remain policy priors.
SPECIAL.update({
 'Ancestral Recall':(110,'One blue mana draws three cards at instant speed, exceptionally efficient card advantage.','Can target teammate to supply three cards.','Cheap velocity into early wins; recursion compounds advantage.','Retain ban'),
 'Balance':(80,'Two-mana symmetrical reduction of lands, creatures and hands; symmetry is readily broken.','Teammate is also affected; coordinated construction can exploit the reset.','Early resource denial and persistent advantage.','Retain ban'),
 'Black Lotus':(150,'Zero-mana artifact sacrifices for three mana of one color.','Mana is personal; enables a very early engine with teammate protection.','Extreme opening acceleration and recursion loops.','Retain ban'),
 'Chaos Orb':(25,'Physical flipping destruction is outside conventional card resolution.','Manual targeting and team board layout create adjudication problems.','Physical dexterity and tournament-policy concerns dominate price.','Retain ban; points do not resolve physical-play issues'),
 'Channel':(130,'Two-mana temporary life-to-colorless-mana conversion.','Shared 60 starting life increases available conversion resources.','Very early enormous mana and game-ending threats.','Retain ban'),
 'Emrakul, the Aeons Torn':(75,'Fifteen-mana protected flying annihilator threat with a cast extra turn.','Extra turns are team turns; cast trigger and annihilator threaten both team resources.','Cheating cast costs, turn loops and land denial.','Retain ban pending gameplay-policy review'),
 'Falling Star':(15,'Physical flipping damage spell has unusual targeting and resolution.','Board placement and shared combat complicate physical resolution.','Dexterity mechanic is unsuitable for ordinary league adjudication.','Retain ban; points do not resolve physical-play issues'),
 'Fastbond':(110,'One-mana permission for repeated land plays at a life cost.','Shared starting life makes repeated payments comparatively easier.','Explosive early mana with draw engines and land recursion.','Retain ban'),
 'Flash':(120,'Two-mana instant temporarily deploys a creature unless remaining cost is paid.','Teammate can defend a cheap instant-speed triggered-ability line.','Death/ETB triggers enable compact early wins despite sacrificed creature.','Retain ban'),
 'Griselbrand':(110,'Eight-mana flying lifelink threat with repeatable seven-life draw-seven activation.','Shared 60-life total supplies a larger draw budget; partner can protect it.','Cheated deployment followed by immediate massive draw.','Retain ban'),
 'Hullbreacher':(95,'Three-mana flash replaces opponents’ additional draws with controller Treasures.','Only opposing players are affected; teammate can deploy wheels and retain own draws.','Wheel-based hand denial and resource monopoly.','Retain ban'),
 'Iona, Shield of Emeria':(65,'Nine-mana flying threat prevents opponents casting a selected color.','Does not restrict teammate; mono-color opposing players may be shut out.','Reanimation into color lock; price cannot ensure interactive games.','Retain ban'),
 'Karakas':(85,'Untapped land with reusable legendary creature bounce.','Can protect teammate legends or repeatedly bounce opposing commanders.','Low-cost command-zone denial and repeated protection.','Retain ban'),
 'Leovold, Emissary of Trest':(95,'Three-mana draw restriction plus targeting-triggered personal draws.','Opponents are restricted while teammate can help create wheel locks.','Wheel-based hand denial; highly consistent command-zone access.','Retain ban'),
 'Library of Alexandria':(75,'Untapped land draws a card at exactly seven cards in hand.','Personal hand condition; teammate can cover tempo while cards accrue.','Early repeatable low-cost advantage, though seven-card condition matters.','Additional review; retain ban until dedicated trials'),
 'Mox Emerald':(100,'Zero-mana permanent green acceleration.','Accelerates its controller; teammate can protect resulting threats.','Opening-hand tempo and free artifact synergies.','Retain ban'),
 'Mox Jet':(100,'Zero-mana permanent black acceleration.','Accelerates its controller; teammate can protect resulting threats.','Opening-hand tempo and free artifact synergies.','Retain ban'),
 'Mox Pearl':(100,'Zero-mana permanent white acceleration.','Accelerates its controller; teammate can protect resulting threats.','Opening-hand tempo and free artifact synergies.','Retain ban'),
 'Mox Ruby':(100,'Zero-mana permanent red acceleration.','Accelerates its controller; teammate can protect resulting threats.','Opening-hand tempo and free artifact synergies.','Retain ban'),
 'Mox Sapphire':(100,'Zero-mana permanent blue acceleration.','Accelerates its controller; teammate can protect resulting threats.','Opening-hand tempo and free artifact synergies.','Retain ban'),
 'Nadu, Winged Wisdom':(100,'Three-mana engine grants targeted creatures limited repeated top-card draw/land deployment triggers.','Can trigger from allied targeting effects; teammate does not gain the granted ability on own creatures.','Zero-cost targeting and new-creature resets create long explosive chains.','Retain ban'),
 'Paradox Engine':(95,'Five-mana artifact untaps controller’s nonland permanents on each spell cast.','Only controller untaps, but teammate can defend the engine.','Mana-positive rocks plus cheap spells enable resource loops.','Retain ban'),
 'Recurring Nightmare':(75,'Three-mana reusable reanimation exchanges a creature and returns enchantment to hand as cost.','Teammate cannot normally supply sacrifice; can defend recursion turn.','Repeatable ETB/death loops and difficult-to-interact-with activation cost.','Additional review; retain ban pending loop-policy tests'),
 'Shahrazad':(25,'Two-mana subgame spell changes the play procedure and penalizes losing players.','Team subgame handling and shared life produce extensive logistics.','Repeated subgames and unacceptable match duration.','Retain ban; points cannot fix time and procedure'),
 'Sundering Titan':(80,'Eight-mana body destroys selected basic land types on entering and leaving.','Land choices can favor the allied team; blink multiplies denial.','Repeated land destruction and non-games.','Retain ban'),
 'Sylvan Primordial':(75,'Seven-mana reach creature removes opposing noncreature permanents and finds Forests.','Two opposing targets in 2HG, fewer than normal four-player FFA; teammate unaffected.','Blink/reanimation chains remove lands while ramping.','Retain ban pending land-denial policy review'),
 'Time Vault':(120,'Two-mana artifact exchanges a skipped turn for stored extra turn, with special untap restriction.','Skipped/extra turns operate on the team and reshape both players’ development.','External untap effects create team extra-turn loops.','Retain ban'),
 'Time Walk':(130,'Two-mana extra turn spell.','Extra turn benefits the team, with two players developing together.','Very efficient team extra turns and recursion loops.','Retain ban'),
 'Tinker':(110,'Three-mana artifact sacrifice tutor puts any artifact directly onto battlefield.','Can deploy a personal lock/engine protected by teammate.','Cheap enormous mana bypass and compact artifact locks.','Retain ban'),
 'Tolarian Academy':(110,'Legendary land produces blue mana proportional to controller’s artifacts.','Only personal artifacts count; free artifacts produce explosive team-supported starts.','Large early mana and untap loops.','Retain ban'),
 'Upheaval':(80,'Six-mana spell returns all permanents to hands.','A coordinated team can float mana and rebuild faster, though allied boards also return.','Large-scale mana reset and prolonged inability to redeploy.','Retain ban'),
 "Yawgmoth's Bargain":(105,'Six-mana enchantment skips normal draw for repeatable one-life draws.','Shared 60-life pool supplies many activation payments.','Cheated deployment or sufficient mana enables immediate mass draw and wins.','Retain ban'),
})
def build_unbans(cards,scores,raw):
 soup=BeautifulSoup((raw/'banned.html').read_text(),'html.parser');h=soup.find(lambda t:t.name in ['h2','h3'] and t.get_text(strip=True)=='Commander Banned Cards')
 named=[]
 if h:
  for el in h.find_next_siblings():
   if el.name in ['h2','h3']:break
   named.extend(li.get_text(' ',strip=True) for li in el.find_all('li'))
 ordered=sorted(cards.items(),key=lambda oc:0 if oc[1]['legalities'].get('commander')=='banned' else 1)
 exact={}
 for o,c in ordered:exact.setdefault(c['name'],o)
 for o,c in ordered:exact.setdefault(c['name'].split(' // ')[0],o)
 bans={exact[n] for n in named if n in exact}
 union=bans|{o for o,c in cards.items() if c['legalities'].get('commander')=='banned'}
 lutri=exact.get('Lutri, the Spellchaser')
 if lutri:union.add(lutri)
 rows=[]
 for o in sorted(union,key=lambda o:cards[o]['name']):
  c=cards[o];name=c['name'];front=name.split(' // ')[0];special=SPECIAL.get(name,SPECIAL.get(front));category='named Commander ban' if o in bans else 'category ban / Oracle banned; review exact official scope'
  if special:p,assessment,effect,risk,recommendation=special
  else:
   p=max(75,scores[o]['base_points']);assessment='Provisional stress-test reserve; generic feature model is unreliable for this banned card. Oracle text preserved in card database.';effect='Requires card-specific 2HG review; shared turns, shared life and two opponents may change impact.';risk='Unassessed; do not interpret price as sufficient mitigation.';recommendation='Retain ban pending card-specific review'
  if 'Conspiracy' in c['type_line'] or re.search(r'\bante\b',c.get('oracle_text',''),re.I) or c.get('security_stamp')=='triangle':
   recommendation='Retain ban; out-of-scope mechanics/category';category='category ban'
  if name=='Lutri, the Spellchaser':category='companion-only ban'
  rows.append(dict(oracle_id=o,card_name=name,current_legality=c['legalities'].get('commander'),official_status='banned' if o in bans else 'companion_only' if name=='Lutri, the Spellchaser' else 'category_or_oracle_banned',ban_category=category,proposed_points=p,model_base_points=scores[o]['base_points'],assessment=assessment,effect_2hg=effect,early_win_or_lock=risk,confidence='medium_function_low_price' if special else 'low_unreviewed',manually_reviewed=bool(special),recommendation=recommendation,legalized=False,source='https://magic.wizards.com/en/banned-restricted-list',retrieved_date='2026-10-19'))
 return rows
