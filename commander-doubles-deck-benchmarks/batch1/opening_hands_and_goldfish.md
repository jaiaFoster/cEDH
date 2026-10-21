# Opening hands and goldfish demonstrations

**Possibilities, not observed games or average win turns.** All named cards occur in the submitted head’s own deck. No tutor counts as an extra opening card; tutors named below find the named card from that own library. These sequences assume timely land availability, no opponent successfully intervenes and specified combat connections. Shared team starts at60 under the league’s verified format; resource ownership remains separate. Opening-hand diagnostics later in this document deliberately simulate only random seven-card properties, without mulligans, colored-source solving, fetch sequencing, gameplay decisions or win simulation.

## A1: third-turn Oracle with independently deployed protection

A1 has Tundra, Underground Sea, Watery Grave, Oracle and Consultation by its third shared turn. Three untapped lands produce UUB; cast Oracle UU, then Consultation B with ETB on stack, naming Forest (absent from A1). A2 can deploy Kutzil before this using its own lands/dork; a possible start is Tropical Island/Birds, then Tundra, then Savannah. Kutzil protects both friendly heads from opposing spells on the shared friendly turn, not abilities. A1 has spent all three lands and cannot additionally claim a W Chant. Alternatively, on turn4 use four own sources UUBW and two independent W Chants, one per head targeting one opponent each. Counter Oracle/trigger or remove the protection first; simply killing Oracle does not necessarily prevent the empty-library win.

## A2: third-turn Caller mana, with a specific seven

Own opening seven: Tropical Island, Tundra, Savannah, Birds of Paradise, Valley Floodcaller, Retraction Helix, Tormod’s Crypt. T1 Tropical casts Bird. T2 Tundra: hold both lands plus Bird to flash Caller for2U at the opponent end step; these resources cannot also cast Thrasios on T2. T3 Savannah, Helix U on own ready Caller. Crypt costs0. Tap Caller to bounce own Crypt; tap Bird for any color; recast Crypt, letting Caller’s noncreature-cast trigger untap both own Otter and Bird. Repeat for arbitrary own mana. Cast own Thrasios from command zone, draw own deck, cast own Ballista with sufficient X and shoot. This works because Bird/Caller are ready by T3; a freshly cast ordinary Bird cannot tap immediately without a relevant permission. Intervene on Helix, cast trigger, Caller, Bird, Crypt, or outlet. This seven is demonstrated, not a stated likelihood.

## B: fourth-turn cross-head Bear Umbra combat engine

B1 opening seven: Savannah, Volcanic Island, Tropical Island, Bayou, Birds of Paradise, Demonic Tutor, Fierce Guardianship. T1 Savannah/Bird. T2 Volcanic, cast Najeela2R using two lands plus Bird. T3 Tropical, Tutor1B using Bird B and Savannah generic, find Bear Umbra. T4 Bayou: cast Umbra2GG on own Najeela using Savannah/Bayou GG, Volcanic and Bird generic; leave Tropical available. Attack Najeela: Umbra untaps four own lands. B2’s possible start is Tropical/Noble onT1, Tundra then Derevi GWU onT2, Savannah then Kutzil1GW onT3. OnT4 B2 Derevi must connect. Derevi trigger untaps B1 Bird; B1’s four lands provide G,R,U,B and Bird W. Activate Najeela WUBRG during combat damage before mana empties. Its extra shared combat untaps attacking Najeela, Derevi and tokens. Repeat the Umbra land untap and Derevi Bird untap while combat connections and required permanents survive. The Bird is not attacking; it relies on Derevi to untap each iteration. Opposing blockers, removal, ability counters and prevention make this conditional, not deterministic through resistance. B2 Kutzil can suppress opposing spells but not these other answers.

## B2: fourth-turn Pod route with explicit outlet

Own opening seven: Forest, Tropical Island, Savannah, Tundra, Llanowar Elves, Birthing Pod, Finale of Devastation. T1 Forest/Elf. T2 Tropical: three mana for Pod plus2 Phyrexian life. T3 Savannah: cast Derevi GWU with three lands, Elf pays1 plus2 life to Pod-sacrifice own Derevi3 into Preston4; return commander to CZ. T4 Tundra: use four own mana for Derevi’s1GWU command-zone ability. ETB and Preston copy supply untaps; legendary copy is not kept alongside the original. Pay1 plus2 life to Pod original Derevi3 into Guardian4. Original Guardian’s ETB can blink Forest, resolving before Preston’s copy trigger. Tap returned Forest G; copy Guardian blinks original Guardian. Repeat to generate arbitrary G and0/1 Illusions, then decline the optional blink to stop. Finale X=60 fetches Ballista; Finale’s immediate +60/+60 keeps zero-counter Ballista alive through SBAs. Pay4 repeatedly in this main phase to add actual counters (the ability itself has no sorcery-only restriction), then remove60 to damage an opposing head. Chord X=0 would not make an unbuffed Ballista survive, and Finale pump is not counters. Disruption of ETBs, Pod activation, Preston, Guardian, Finale or Ballista can break the line.

## C: third-turn two-library Draco burst

C1 seven: Underground Sea, Watery Grave, City of Brass, Changeling Outcast, Scheming Symmetry, Force of Will, Dispel. C2 can have its own three suitable lands, Changeling Outcast, Fierce Guardianship, Misdirection and Spellstutter Sprite; choose Underground Sea, Watery Grave and City of Brass as those lands. Both heads T1 Outcast and keep it throughT2. T3 C1 City B casts Symmetry targeting both friendly heads; each finds its own Draco. C1 retains UB from its other two lands, C2 spends own UB. After blockers, each commander-ninjutsus its own Yuriko returning its own unblocked Outcast. Each connecting Yuriko puts own Draco into hand and causes16 loss to each opposing head. Shared opposing life loses32+32=64. C1 Force plus Dispel pitch can protect Symmetry, but C2’s Fierce is not free until its own commander is already controlled: do not count it as free pre-arrival Symmetry protection. Draco in opening hand requires actual Brainstorm/Rack resources instead, and search/trigger/damage disruption remains relevant.

## C2: later alternate routes, without double-spending mana

Doomsday BBB before combat with own Yuriko and own connecting Outcast plus an actual evasion condition can stack Draco16, Blinkmoth Infusion14 and three planned cards. Two own Ninja damage triggers reveal30 total, losing60 opposing shared life. It costs half the shared friendly life once. This line requires two own Ninjas; the ally’s trigger does not consume C2’s library.

For Nanogene, have own Caller and Yuriko already on battlefield. After friendly Outcasts are unblocked, C2 spends3U and targets its own Yuriko. If C1 owns two total creatures and C2 owns three (Caller, Yuriko, Outcast), the resulting counts are2*1=2 and3*1=3 own triggers. Friendly head C1 may have spent its own B on Symmetry first; do not charge that B to C2 or assume C2 can pay Doomsday BBB and Nanogene3U with only four lands. Order lethal top reveals before draw triggers. Opposing creatures also copy; casting before blockers instead destroys the assumed fear advantage against black blockers.

## Measured raw-hand diagnostics

Fixed NumPy seed20261020,50,000 independent random seven-card hands per deck, without replacement within a hand. No draws/mulligans/game outcomes are simulated. Generator takes the first seven indices of a random permutation obtained by independent continuous keys; each seven-card subset is uniform. Fractions are descriptive Monte Carlo diagnostics only. Conditional Force support counts any other blue printed card, not a claim it should be pitched or is still in hand at a later turn. Land slots include MDFCs and conditional lands. Full integer numerators and denominators are in CSV.

| deck_id | samples | planned_land_slots | blue_cards_in_library | raw_seven_2to4_land_slots_fraction | force_support_fraction_given_force |
| --- | --- | --- | --- | --- | --- |
| A1 | 50000 | 32 | 34 | 0.69828 | 0.92183 |
| A2 | 50000 | 31 | 23 | 0.68602 |  |
| B1 | 50000 | 33 | 11 | 0.70728 |  |
| B2 | 50000 | 30 | 20 | 0.65826 | 0.73577 |
| C1 | 50000 | 31 | 52 | 0.67796 | 0.9865 |
| C2 | 50000 | 31 | 49 | 0.67806 |  |

No expected winning turn, win rate or matchup advantage was measured. Exact sequence feasibility above is conditional desk analysis.
