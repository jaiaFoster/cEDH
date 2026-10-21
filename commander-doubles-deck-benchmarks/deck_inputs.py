"""Batch1 v1: deliberate complete builds; every slot has a primary role.
No automatic filler, ordinary point overrides, or claimed global optimization proof.
"""
def names(text):return [s.strip() for s in text.strip().splitlines() if s.strip()]
DECKS={
'A1':{'team':'A','title':'Blue Farm — Shared-Turn World Police','commanders':['Tymna the Weaver',"Kraum, Ludevic's Opus"],'archetype':'blue_farm','categories':{
'lands':names('''Arid Mesa
Bloodstained Mire
Flooded Strand
Marsh Flats
Misty Rainforest
Polluted Delta
Scalding Tarn
Verdant Catacombs
Windswept Heath
Wooded Foothills
Tundra
Underground Sea
Volcanic Island
Badlands
Scrubland
Plateau
Hallowed Fountain
Watery Grave
Steam Vents
Godless Shrine
Command Tower
City of Brass
Mana Confluence
Exotic Orchard
Forbidden Orchard
Morphic Pool
Sea of Clouds
Training Center
Gemstone Caverns
Otawara, Soaring City
Island
Swamp'''),
'mana':names('''Arcane Signet
Fellwar Stone
Talisman of Dominance
Talisman of Progress
Talisman of Creativity
Springleaf Drum
Lotho, Corrupt Shirriff
Ragavan, Nimble Pilferer'''),
'card_advantage_selection':names('''Esper Sentinel
Mystic Remora
Faerie Mastermind
Pollywog Prodigy
Ledger Shredder
Brainstorm
Ponder
Preordain
Gitaxian Probe
Lim-Dûl's Vault
Wishclaw Talisman
Beseech the Mirror
Scheming Symmetry'''),
'conversion':names('''Thassa's Oracle
Demonic Consultation
Tainted Pact'''),
'protection':names('''Orim's Chant
Abeyance
Teferi, Time Raveler
Tidal Barracuda
Snapcaster Mage'''),
'interaction':names('''Force of Will
Counterspell
Dovin's Veto
An Offer You Can't Refuse
Dispel
Spell Pierce
Spell Snare
Flare of Denial
Mindbreak Trap
Pyroblast
Red Elemental Blast
Consign to Memory
Wash Away
Daze
Orcish Bowmasters
Chain of Vapor
Cyclonic Rift
Into the Flood Maw
Abrade
Fire Covenant
Snuff Out
Stern Scolding
Dress Down
Soul Partition
Prismatic Ending
Loran of the Third Path
Sevinne's Reclamation''')
}},
'A2':{'team':'A','title':'Dawnwaker — Dork/Untap Conversion','commanders':['Thrasios, Triton Hero','Bruse Tarl, Boorish Herder'],'archetype':'dawnwaker','categories':{
'lands':names('''Arid Mesa
Bloodstained Mire
Flooded Strand
Marsh Flats
Misty Rainforest
Polluted Delta
Scalding Tarn
Verdant Catacombs
Windswept Heath
Wooded Foothills
Tropical Island
Tundra
Savannah
Volcanic Island
Taiga
Plateau
Breeding Pool
Temple Garden
Hallowed Fountain
Stomping Ground
Steam Vents
Command Tower
City of Brass
Mana Confluence
Exotic Orchard
Boseiju, Who Endures
Otawara, Soaring City
Minamo, School at Water's Edge
Forest
Island
'''),
'mana':names('''Birds of Paradise
Noble Hierarch
Delighted Halfling
Llanowar Elves
Elvish Mystic
Fyndhorn Elves
Avacyn's Pilgrim
Arbor Elf
Wild Growth
Utopia Sprawl
Carpet of Flowers
Bloom Tender
Faeburrow Elder
Devoted Druid
Kinnan, Bonder Prodigy
Arcane Signet'''),
'engines_conversion':names('''Zirda, the Dawnwaker
Basalt Monolith
Swift Reconfiguration
Vizier of Remedies
Freed from the Real
Training Grounds
Biomancer's Familiar
Walking Ballista
Seedborn Muse
Sylvan Library
Faerie Mastermind
Pollywog Prodigy
Enduring Vitality'''),
'creature_toolbox':names('''Birthing Pod
Eladamri's Call
Neoform
Eldritch Evolution
Green Sun's Zenith
Finale of Devastation
Chord of Calling
Wargate
Recruiter of the Guard
Imperial Recruiter
Drift of Phantasms
Muddle the Mixture
Eternal Witness
Sevinne's Reclamation'''),
'protection_interaction':names('''Fierce Guardianship
Orim's Chant
Kutzil, Malamet Exemplar
Teferi, Time Raveler
An Offer You Can't Refuse
Dovin's Veto
Counterspell
Dispel
Flare of Denial
Mindbreak Trap
Pyroblast
Red Elemental Blast
Consign to Memory
Force of Vigor
Nature's Claim
Chain of Vapor
Cyclonic Rift
Into the Flood Maw
Pongify
Rapid Hybridization
Endurance
Otawara, Soaring City''')
}},
'B1':{'team':'B','title':'Najeela — Five-Color Warrior Tempo','commanders':['Najeela, the Blade-Blossom'],'archetype':'najeela','categories':{
'lands':names('''Arid Mesa
Bloodstained Mire
Flooded Strand
Marsh Flats
Misty Rainforest
Polluted Delta
Scalding Tarn
Verdant Catacombs
Windswept Heath
Wooded Foothills
Tropical Island
Tundra
Savannah
Volcanic Island
Underground Sea
Bayou
Taiga
Badlands
Scrubland
Command Tower
City of Brass
Mana Confluence
Exotic Orchard
Forbidden Orchard
Gemstone Caverns
Boseiju, Who Endures
Otawara, Soaring City
Breeding Pool
Temple Garden
Watery Grave
Steam Vents
Forest'''),
'mana':names('''Birds of Paradise
Noble Hierarch
Ignoble Hierarch
Delighted Halfling
Llanowar Elves
Elvish Mystic
Fyndhorn Elves
Avacyn's Pilgrim
Deathrite Shaman
Tinder Wall
Wild Growth
Utopia Sprawl
Carpet of Flowers
Bloom Tender
'''),
'combat_engines':names('''Nature's Will
Druids' Repository
Bear Umbra
Sword of Feast and Famine
Derevi, Empyrial Tactician
Grim Hireling
Professional Face-Breaker
Samut, Vizier of Naktamun
Reconnaissance
'''),
'conversion_toolbox':names('''Dualcaster Mage
Twinflame
Goblin Bombardment
Eladamri's Call
Chord of Calling
Green Sun's Zenith
Finale of Devastation
Eldritch Evolution
Neoform
Idyllic Tutor
Scheming Symmetry
'''),
'protection_interaction':names('''Force of Will
Fierce Guardianship
Orim's Chant
Veil of Summer
Swords to Plowshares
Orcish Bowmasters
Kutzil, Malamet Exemplar
Teferi, Time Raveler
An Offer You Can't Refuse
Dovin's Veto
Dispel
Spell Pierce
Flare of Denial
Mindbreak Trap
Pyroblast
Red Elemental Blast
Consign to Memory
Abrupt Decay
Assassin's Trophy
Chain of Vapor
Cyclonic Rift
Fire Covenant
Nature's Claim
Force of Vigor
'''),
'value':names('''Faerie Mastermind
Toski, Bearer of Secrets
Oakhame Adversary
''')
}},
'B2':{'team':'B','title':'Derevi — Bant Pod and Untap Toolbox','commanders':['Derevi, Empyrial Tactician'],'archetype':'derevi','categories':{
'lands':names('''Flooded Strand
Misty Rainforest
Windswept Heath
Marsh Flats
Verdant Catacombs
Wooded Foothills
Scalding Tarn
Polluted Delta
Arid Mesa
Tropical Island
Tundra
Savannah
Breeding Pool
Temple Garden
Hallowed Fountain
Command Tower
City of Brass
Mana Confluence
Exotic Orchard
Boseiju, Who Endures
Otawara, Soaring City
Gaea's Cradle
Minamo, School at Water's Edge
Talon Gates of Madara
Forest
Snow-Covered Forest
Island
Snow-Covered Island
Plains
'''),
'mana':names('''Birds of Paradise
Noble Hierarch
Delighted Halfling
Llanowar Elves
Elvish Mystic
Fyndhorn Elves
Avacyn's Pilgrim
Arbor Elf
Wild Growth
Utopia Sprawl
Carpet of Flowers
Bloom Tender
Faeburrow Elder
Devoted Druid
Kinnan, Bonder Prodigy'''),
'pod_and_conversion':names('''Birthing Pod
Preston, the Vanisher
Felidar Guardian
Blasting Station
Emiel the Blessed
Swift Reconfiguration
Vizier of Remedies
Training Grounds
Biomancer's Familiar
Walking Ballista
Eladamri's Call
Green Sun's Zenith
Finale of Devastation
Chord of Calling
Neoform
Eldritch Evolution
Recruiter of the Guard
Eternal Witness
Ephemerate
'''),
'advantage_support':names('''Esper Sentinel
Mystic Remora
Faerie Mastermind
Seedborn Muse
Enduring Vitality
Teferi, Time Raveler
Kutzil, Malamet Exemplar
Drannith Magistrate
'''),
'interaction':names('''Force of Will
Fierce Guardianship
Orim's Chant
Veil of Summer
Swords to Plowshares
An Offer You Can't Refuse
Dovin's Veto
Counterspell
Dispel
Mindbreak Trap
Consign to Memory
Flare of Denial
Solitude
Endurance
Force of Vigor
Nature's Claim
Chain of Vapor
Cyclonic Rift
Into the Flood Maw
Spellskite
''')
}},
'C1':{'team':'C','title':'Yuriko — Ninja Tempo / Delver','commanders':["Yuriko, the Tiger's Shadow"],'archetype':'yuriko_tempo','categories':{
'land_slots':names('''Polluted Delta
Flooded Strand
Marsh Flats
Misty Rainforest
Scalding Tarn
Bloodstained Mire
Verdant Catacombs
Prismatic Vista
Underground Sea
Watery Grave
Undercity Sewers
Morphic Pool
Darkslick Shores
Underground River
Clearwater Pathway // Murkwater Pathway
Command Tower
City of Brass
Mana Confluence
Exotic Orchard
Gemstone Caverns
Otawara, Soaring City
Shizo, Death's Storehouse
Mystic Sanctuary
Island
Snow-Covered Island
Swamp
Snow-Covered Swamp
Minamo, School at Water's Edge
Takenuma, Abandoned Mire
Sink into Stupor // Soporific Springs
Agadeem's Awakening // Agadeem, the Undercrypt'''),
'evasion':names('''Changeling Outcast
Thousand-Faced Shadow
Mothdust Changeling
Ornithopter
Faerie Seer
Spectral Sailor
Wingcrafter
Slither Blade
Triton Shorestalker
Mist-Cloaked Herald
Network Disruptor
'''),
'ninja_tempo':names('''Moon-Circuit Hacker
Ninja of the Deep Hours
Ingenious Infiltrator
Prosperous Thief
Sakashima's Student
Mist-Syndicate Naga
Silver-Fur Master
Tetsuko Umezawa, Fugitive
Cover of Darkness
'''),
'card_selection':names('''Brainstorm
Ponder
Preordain
Portent
Consider
Gitaxian Probe
Scheming Symmetry
Lim-Dûl's Vault
Personal Tutor
Mystic Remora
'''),
'conversion':names('''Draco
Thassa's Oracle
Demonic Consultation
Time Warp
'''),
'interaction':names('''Force of Will
Flusterstorm
Disrupting Shoal
Misdirection
Flare of Denial
Mindbreak Trap
Counterspell
Drown in the Loch
An Offer You Can't Refuse
Dispel
Spell Pierce
Spell Snare
Consign to Memory
Wash Away
Daze
Orcish Bowmasters
Fatal Push
Snuff Out
Dismember
Flare of Malice
Chain of Vapor
Cyclonic Rift
Into the Flood Maw
Snap
Submerge
Brazen Borrower // Petty Theft
Stern Scolding
''')
}},
'C2':{'team':'C','title':'Yuriko — Big-Flip Topdeck Combo','commanders':["Yuriko, the Tiger's Shadow"],'archetype':'yuriko_combo','categories':{
'land_slots':names('''Polluted Delta
Flooded Strand
Marsh Flats
Misty Rainforest
Scalding Tarn
Bloodstained Mire
Verdant Catacombs
Prismatic Vista
Underground Sea
Watery Grave
Undercity Sewers
Morphic Pool
Darkslick Shores
Underground River
Clearwater Pathway // Murkwater Pathway
Command Tower
City of Brass
Mana Confluence
Exotic Orchard
Gemstone Caverns
Otawara, Soaring City
Shizo, Death's Storehouse
Mystic Sanctuary
Island
Snow-Covered Island
Swamp
Snow-Covered Swamp
Minamo, School at Water's Edge
Sink into Stupor // Soporific Springs
Agadeem's Awakening // Agadeem, the Undercrypt
Sea Gate Restoration // Sea Gate, Reborn
'''),
'evasion_and_ninjas':names('''Changeling Outcast
Thousand-Faced Shadow
Mothdust Changeling
Ornithopter
Faerie Seer
Wingcrafter
Slither Blade
Triton Shorestalker
Mist-Cloaked Herald
Moon-Circuit Hacker
Ninja of the Deep Hours
Ingenious Infiltrator
Prosperous Thief
Sakashima of a Thousand Faces
Roaming Throne
Tetsuko Umezawa, Fugitive
Cover of Darkness
'''),
'big_flips':names('''Draco
Shadow of Mortality
Blinkmoth Infusion
Temporal Mastery
Temporal Trespass
Dig Through Time
Treasure Cruise
Commit // Memory
Consign // Oblivion
Commandeer
'''),
'selection_conversion':names('''Doomsday
Scheming Symmetry
Brainstorm
Ponder
Preordain
Lim-Dûl's Vault
Vampiric Tutor
Mystical Tutor
Personal Tutor
Insidious Dreams
Scroll Rack
Sensei's Divining Top
Mystic Speculation
Mystic Retrieval
'''),
'interaction':names('''Fierce Guardianship
Disrupting Shoal
Misdirection
Flare of Denial
Mindbreak Trap
Counterspell
An Offer You Can't Refuse
Dispel
Consign to Memory
Chain of Vapor
Cyclonic Rift
Snuff Out
Dismember
Sickening Shoal
Flare of Malice
Snap
''')
}}
}
# Explicit construction revisions after exact price/legality checks, not automated filler.
REVISIONS=[]
def remove(did,name,reason):
 for cat,ns in DECKS[did]['categories'].items():
  if name in ns:ns.remove(name);REVISIONS.append({'deck_id':did,'action':'remove','card_name':name,'reason':reason});return
 raise KeyError((did,name))
def add(did,cat,text,reason):
 for name in names(text):
  DECKS[did]['categories'].setdefault(cat,[]).append(name);REVISIONS.append({'deck_id':did,'action':'add','card_name':name,'reason':reason})
for n in ['Mindbreak Trap','Flare of Denial','Gitaxian Probe','Snuff Out','Lotho, Corrupt Shirriff','Wishclaw Talisman',"An Offer You Can't Refuse"]:remove('A1',n,'Budget: preserve Force/Oracle/Consultation/Pact and command-zone farm; replace ancillary taxed interaction or mana with strong unpointed alternatives.')
add('A1','budget_control_and_value', '''Thoughtseize
Duress
Inquisition of Kozilek
Foil
Delay
Miscast
Stubborn Denial
Remand
Spell Queller
Lavinia, Azorius Renegade
Aven Mindcensor
Faerie Macabre
Night's Whisper
Expressive Iteration
Painful Truths
Dreadhorde Arcanist
Fable of the Mirror-Breaker // Reflection of Kiki-Jiki''','Proactive hand disruption, broad stack/permanent control, cheap value and evasive farm bodies; no filler.')
remove('A2','Otawara, Soaring City','Remove accidental duplicate utility land from initial draft; retain exactly one.')
for n in ['Mindbreak Trap','Endurance','Flare of Denial','Force of Vigor',"An Offer You Can't Refuse"]:remove('A2',n,'Concentrate points on efficient mana engines, Fierce and Library; A1 covers broad free interaction and graveyard response. Keep own counters and removal.')
add('A2','lands','Plains','31st land; basic white against nonbasic hate and independent WW/WU requirements.')
add('A2','budget_toolbox', '''Badgermole Cub
Formidable Speaker
Valley Floodcaller
Retraction Helix
Tormod's Crypt
Loran of the Third Path
Remorseful Cleric
Spell Queller''','Tournament-era creature mana/tutor engines, grave hate and secondary Floodcaller conversion, with creature interaction.')
for n in ['Mindbreak Trap','Flare of Denial','Force of Vigor',"An Offer You Can't Refuse"]:remove('B1',n,'Preserve Force/Fierce, Veil and dedicated combat converters; use zero-point proactive bodies/removal with ally stack coverage.')
add('B1','lands','Plateau','33rd land and untapped RW fetch target for warrior/protection sequence.')
add('B1','warrior_pressure_and_disruption', '''Badgermole Cub
Formidable Speaker
Ainok Strike Leader
Gornog, the Red Reaper
Stadium Headliner
Taunting Elf
Dolmen Gate
Thoughtseize
Duress''','Source-supported token/Warrior pressure, creature-mana throughput, purposeful unblock/combat resilience and hand disruption.')
for n in ['Mindbreak Trap',"An Offer You Can't Refuse",'Flare of Denial','Force of Vigor','Endurance','Solitude']:remove('B2',n,'Preserve premium free counters/Cradle plus Pod and engines; use tutorable zero-point permanent answers/yard hate instead of additional taxed free spells.')
add('B2','lands','Dryad Arbor','Green Sun Zenith X=0 ramp and Pod zero-to-one bridge; summoning sickness applies, not immediate mana.')
add('B2','budget_toolbox', '''Badgermole Cub
Formidable Speaker
Universal Automaton
Spell Queller
Aven Mindcensor
Lavinia, Azorius Renegade
Skyclave Apparition
Knight of Autumn
Spellstutter Sprite
Malevolent Hermit // Benevolent Geist
Scryb Ranger
Remorseful Cleric
Haywire Mite''','Tutorable proactive hate/answers, own mana throughput, blue interaction and a Warrior Pod seed to receive allied Najeela tokens.')
for n in ['Mindbreak Trap','Flare of Denial',"An Offer You Can't Refuse",'Gitaxian Probe','Snap','Snuff Out']:remove('C1',n,'Keep Force, Flusterstorm and Oracle/Consultation; replace auxiliary priced spells with strong unpointed tempo/selection.')
add('C1','tempo_selection_and_disruption', '''Scroll Rack
Sensei's Divining Top
Gush
Foil
Delay
Thoughtseize
Duress
Inquisition of Kozilek
Faerie Macabre
Murderous Cut
Baleful Strix
Spyglass Siren
Siren Stormtamer''','More stack/topdeck/hand interaction and cheap evasive bodies; Draco retained as deliberate two-head Symmetry target, not a generic tempo threat.')
remove('C2','Mystic Retrieval','Illegal red flashback color identity in UB; removed rather than treating flashback as irrelevant.')
for n in ['Mindbreak Trap',"An Offer You Can't Refuse",'Flare of Denial','Snap','Snuff Out','Commandeer']:remove('C2',n,'Keep Fierce plus both extra-team-turn flips, Doomsday and top tutors. Substitute unpointed conditional interaction and topdeck tools.')
add('C2','topdeck_control_and_resilience', '''Gush
Unmask
Force of Despair
Faerie Macabre
Submerge
Contagion
Discovery // Dispersal
Far // Away
Otherworldly Gaze
Soothsaying
Diabolic Vision
Cruel Tutor
Telling Time
Valley Floodcaller
Nanogene Conversion
Spellstutter Sprite
Augury Owl
Surgical Extraction''','Playable high-MV alternatives, free hand/creature/grave disruption, flash Nanogene line and reliable own-library manipulation; not arbitrary costly flips.')
remove('A2','Spell Queller','Interaction stress test: add a green tutorable artifact/enchantment answer reachable with Green Sun Zenith using only generated green mana; A1 retains Spell Queller and both heads keep stack answers.')
add('A2','budget_toolbox','Reclamation Sage','Green Sun Zenith/Chord/Finale can fetch a green answer to non-ETB-suppressing hate such as Cursed Totem; Torpor Orb still requires spell/land answers.')
remove('B1','Force of Will','Mana/pitch audit: only eleven other blue printed cards supported this five-color creature build. Replace the expensive pitch counter with unrestricted tutor consistency; B2 retains Force and both heads retain Fierce and ordinary stack answers.')
add('B1','conversion_toolbox','Demonic Tutor','One extra point buys immediate access to combat converter, Twinflame/Dualcaster, or protection without diluting Warrior/green creature identity for blue pitch density.')
remove('B2','Training Grounds','Transfer one point to B1 Demonic Tutor. Keep creature-tutorable Biomancer Familiar and independent Kinnan/Cub/Cradle routes; this reducer was narrow here because Thrasios is not this head commander.')
add('B2','budget_toolbox','Glen Elendra Archmage','Replace the narrow enchantment reducer slot with a blue Pod-reachable counter body; own Vizier removes the persist counter, permitting repeated U-funded noncreature counters, not free or teammate-paid counters.')
