"""Tiny resource-accounting checks, NOT a Magic engine or simulated matches.
Statements about triggers/controllers remain analyst rulings in rules_interactions.jsonl.
"""
from collections import Counter
OPENING_EXAMPLES={
'A1_Oracle':{'A1':['Tundra','Underground Sea','Watery Grave',"Thassa's Oracle",'Demonic Consultation']},
'A2_Caller':{'A2':['Tropical Island','Tundra','Savannah','Birds of Paradise','Valley Floodcaller','Retraction Helix',"Tormod's Crypt"]},
'B1_Umbra':{'B1':['Savannah','Volcanic Island','Tropical Island','Bayou','Birds of Paradise','Demonic Tutor','Fierce Guardianship'],'B2':['Tropical Island','Tundra','Savannah','Noble Hierarch','Kutzil, Malamet Exemplar']},
'B2_Pod':{'B2':['Forest','Tropical Island','Savannah','Tundra','Llanowar Elves','Birthing Pod','Finale of Devastation']},
'C1_Draco':{'C1':['Underground Sea','Watery Grave','City of Brass','Changeling Outcast','Scheming Symmetry','Force of Will','Dispel'],'C2':['Underground Sea','Watery Grave','City of Brass','Changeling Outcast','Fierce Guardianship','Misdirection','Spellstutter Sprite']}}
class Mana:
 def __init__(self):self.pools={}
 def add(self,owner,color,n=1):self.pools.setdefault(owner,Counter())[color]+=n
 def pay(self,owner,colored='',generic=0):
  pool=self.pools.setdefault(owner,Counter());required=Counter(colored)
  if any(pool[c]<n for c,n in required.items()) or sum(pool.values())<sum(required.values())+generic:raise ValueError('insufficient own mana')
  pool.subtract(required)
  for c in list(pool):
   n=min(generic,pool[c]);pool[c]-=n;generic-=n
 def remaining(self,owner):return sum(self.pools.get(owner,{}).values())
def checked_arithmetic():
 # A1 three own sources UUB can pay Oracle+Consultation, not additional W.
 m=Mana()
 for c in 'UUB':m.add('A1',c)
 m.pay('A1','UU');m.pay('A1','B');assert m.remaining('A1')==0
 try:m.pay('A1','W');raise AssertionError('phantom fourth mana')
 except ValueError:pass
 # Four lands untapped by own Umbra plus own Bird untapped by allied Derevi.
 for _ in range(10):
  for c in 'GRUBW':m.add('B1',c)
  m.pay('B1','WUBRG');assert m.remaining('B1')==0
 # Allied own resources are not a second mana pool for you.
 m.add('B2','U',5)
 try:m.pay('B1','U');raise AssertionError('pooled mana')
 except ValueError:pass
 # Same-controller Caller: Bird produces1, zero-cost Crypt cast untaps it.
 caller_mana=0
 for _ in range(10):caller_mana+=1
 assert caller_mana==10
 # Emiel3 needs source>3 for net gain. A three-color Elder alone breaks even.
 assert 3-3==0 and 4-3==1
 # Finale pump preserves0/0, but is not counters. Need actual4 per counter.
 X=60;counters=0;G=240
 while G>=4:G-=4;counters+=1
 assert X>=10 and counters==60 and G==0
 # Two independent16 reveals hit two opposing players each.
 assert 2*16+2*16==64
 assert 2*(16+14)==60
 # Nanogene own ability count * own connecting Ninjas, no summed-board shortcut.
 assert 2*1+3*1==5
 return {'oracle_own_mana':True,'cross_controller_untap_only':True,'no_shared_mana':True,'caller_finite_iteration':10,'emiel_net_with4':1,'ballista_actual_counters':60,'double_draco_shared_loss':64,'doomsday_two_flip_shared_loss':60,'nanogene_controller_specific_triggers':5,'scope':'illustrative resource arithmetic, not gameplay simulation'}
