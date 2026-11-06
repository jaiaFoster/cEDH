# Team Compositions research — November 5, 2026

The curated publication set has **88 unique team configurations: all 38 organizer seeds plus 50 additional pairings**. There were **zero duplicate curated pair keys**. **14 further distinct pair hypotheses were rejected and retained as private admin drafts**. Two additional rejected *setups* associated with existing pairs are retained in `rejected-setups.json`; they are not counted as two more distinct teams. One original concept, Konrad/Gitrog, remains explicitly conditional and labeled Research candidate rather than a deterministic combo.

These are agent-reviewed mechanics interpretations and unplayed strategy profiles, **not organizer-approved competitive rankings, tournament results or measured win probabilities**. Mechanics verification means the stated configuration follows the recorded Oracle/rules evidence, including its prerequisites. It does not establish that a deck is optimized or that a pairing is competitively strong.

## Acquisition and discovery

The November 5 Scryfall Oracle bulk snapshot contains **39,287 identities**. The downloaded compressed JSONL SHA256, URI, API metadata and date are recorded in `bulk-source.json`. A separate approval pin prevents a later bulk refresh from silently rebuilding published profiles under unreviewed Oracle changes. The league's active scoring catalog is neither replaced nor refreshed by this research.

The feature index has **3,473 potential standalone commanders plus 29 noncreature Backgrounds**, linked by Oracle ID to locally stored full text, face data, colors, mana value, types, keywords, image URLs and Scryfall links. Backgrounds require a compatible command zone. Legendary Background creatures are distinguished from enchantment-only Backgrounds. Rare pregame-color-choice commanders can be researched as drafts but require configuration support/review before publication; they are not silently assigned a chosen color.

17 feature queries cover the seven requested families plus output/input markers. Patterns record their matched Oracle fragment and scope warning. Functional templates nominate combat-reward/attacker, life-output/reward and untapper/tap-ability matches. They generated **1,023 deduplicated nominations**, not validated combos. 1,014 remain unreviewed nominations. Other reviewed proposals came from directed searches of target permissions, explicit team wording, public activated abilities, borrowed abilities and counter replacements.

No all-pairs strength model was fitted. Regex nominates capabilities; it does not decide control, legality, power or publication. The 50 additions were explicitly written/reviewed in `profiles.txt`, checked for each player's costs/control and matched to canonical identities. `candidate_table.csv` contains all 102 reviewed pair records; `generated_candidates.csv` is the larger unreviewed nomination pool. The 88-entry `data/compositions/entries.json` is the curated set, not the nomination output.

## Initial claims and corrections

**23 initial profiles received explicit qualifications**; this is not a claim that 23 organizer statements were false. The audit distinguishes one material wording correction in the initial Arcum/Feldon description (the artifact creature's controller sacrifices and searches) from ordinary timing/control qualifications. The complete per-seed audit and corrected explanations are in `seed-audit.json` and `corrections.json`.

Important checks:

- **Belbe:** CR805.9 means one chosen active head receives the mana. Both opponents losing life gives that head four colorless, not four to each teammate. This corrected an internal draft inference. The opposing active team can also benefit on its turn under the same recipient rule.
- **Heartless:** from 60 versus 60, unprotected damage can eliminate both teams. From 61 a team ends at 1. Lifelink on Heartless can yield 120 life gained across four 30-damage recipients; a prevention effect on one friendly head can instead preserve the team. Witch's Clinic can target an ally's commander, normal equip cannot. Arena's haste requires spending its exhaust mana on casting the creature.
- **Arcum/Feldon and Arcum/Myrel:** the target's controller sacrifices and searches *their own* library. A cannot take B's tutor result. Each library needs its own actual targets.
- **Najeela/Derevi:** B's own connecting creatures generate B's Derevi triggers. Those may untap A's sources, but A still pays Najeela's five colors. This is conditional on real repeatable funding and connections.
- **Jolene:** each attacking player receives their own Treasure; only Jolene's controller gets Jolene's extra-token replacement. A's Treasures do not pay B's Najeela.
- **Mishra/Adeline and Karlach/Winota:** shared trigger ordering under 805.7 matters. Entering tapped and attacking is not declaring an attack. Mishra can count the combined attacking board at resolution, while Winota only triggers from its controller's declared non-Human attackers.
- **Tymna/Edric/Gix:** check exact recipient and combat wording. An ally can qualify Tymna's opponent count; Edric/Gix can reward the connecting creature's controller. Toski's own-creature wording is different.
- **Kudo/Norn:** base-setting and modifying layers are distinct; opposing counters/buffs can save creatures. Norn does not buff its teammate's creatures.
- **Ivy:** observe the original cast; copies are not casts. A casting at B's Zada does not trigger B's Zada.
- **Jeska:** target the ally's creature, then demonstrate one-head damage. Natural Bruse triples/double-strikes for18, requiring a power increase for21; exalted solo Rafiq can deal24. No aggregation-across-heads interpretation was introduced.
- **Konrad/Gitrog:** land movement alone is insufficient; creature-card movement must be established. It remains a conditional research concept, not a proven standard Gitrog kill.
- **Zedruu/Zur:** the simple Immortal Coil setup was rejected because Zedruu lacks black identity and cannot donate B-controlled Coil without another transfer. The legal replacement uses A's blue Illusions of Grandeur and B's tutored Seal of Cleansing, with a finite 20-life gain/loss swing. It is not an automatic kill at 60.

Player-specific key-card assignments are validated against each entire individual command zone. Fitting the union of team colors is insufficient. These assignments also appear in the profile and can be edited with A:/B: prefixes in admin.

## Rules editions and independent sources

The Rules landing page now links a newly posted **November 6, 2026** rulebook. On the client research date, November 5, the September 25 edition remains the effective reference. Both were fetched. All 28 cited rule references were checked against the September index; the November comparison found only two cited text changes:109.5/113.8 expand a delayed-trigger cross-reference to include603.7g. The operative controller wording is unchanged, and the new static-action delayed-trigger case does not change these configurations. Whitespace/line-ending differences were normalized only for that comparison; raw document hashes are retained. No full rulebook is republished. Existing FAQ records and their source edition remain untouched.

Primary sources are [Wizards Rules](https://magic.wizards.com/en/rules), [the 2HG guide](https://magic.wizards.com/en/formats/two-headed-giant), the dated official TXT files and the actual Scryfall bulk API. Scryfall documentation returned403 through the research browser; the public bulk API and image service were accessible. We do not claim to have read inaccessible documentation or assert a blanket rights grant. Card data/imagery is attributed to Scryfall and Magic/Wizards; images are linked from recorded official API URLs, not redistributed image files.

Commander Spellbook's public bulk was examined over **119,349 variants**. Three requested exact card sets matched: Najeela/Derevi, Zirda/Basalt and Lavinia/Knowledge Pool. Kraj/Kiki/Pestermite and the original donated-Coil set did **not** match; the latter setup was subsequently rejected independently. Only factual card membership/IDs/links are retained with attribution; upstream descriptions/steps and the whole database are not redistributed. Software licensing does not establish a blanket data license. Spellbook membership never establishes cross-controller functionality and is not a runtime dependency.

## Breadth and research priorities

| Archetype | Curated profiles |
| --- | ---: |
| Artifact combo | 4 |
| Combat | 26 |
| Control | 14 |
| Creature combo | 2 |
| Graveyard | 5 |
| Midrange | 2 |
| Prison/stax | 8 |
| Resource engine | 16 |
| Spell combo | 6 |
| Turbo combo | 5 |

Shared combat, shared-life arithmetic, opponent-trigger scaling, global permissions, asymmetric restrictions, cross-player targeting/tutoring, counters, borrowed abilities, equipment and public activations are represented. Candidate scope warnings explicitly prevent treating you-control, sacrifice and mana costs as team resources.

Most useful next playtests: Belbe/Heartless for safe parity and real deployment; Arcum/Feldon for which player tutors; Xantcha/Zirda for a same-controller Basalt engine feeding a publicly activatable outlet; Kraj/Kiki for readiness and a Simic-owned Pestermite; Ardenn/Wyleth for equipment-control versus draw ownership; Gisela/Heartless for replacement math. These are qualitative priorities, not a power ranking.

`research-priorities.csv` records actual total commander mana values, bundled-v3 CZ comparisons, high/normal follow-up priorities and the limiting reason. Priority considers 2HG specificity, control compatibility, assembly burden, readiness/speed, disruption, protection and price. Speed/resilience were not measured; profile prerequisites and limitations substitute for unsupported numerical ratings. Several mechanically valid lines have simpler single-deck substitutes, explicitly noted for Vhati/Kelsien. Similar Edric/Gix or combat variants are distinct configurations, not independent empirical strength evidence.

## Deck and pricing evidence

All 18 original benchmark inventories are copied byte-for-byte, linked to their repository source and checked by SHA256. Recomputing the bundled accepted v3 schedule exactly reproduces the supplied team totals:462,518,314,237,198,246,215,150,178. All are above120, although supported construction checks pass. They are labeled historical benchmarks requiring reconstruction. No new 100-card lists or external tournament outcomes were invented.

The website joins Oracle IDs to its actual selected **published PostgreSQL price version**. It displays A/B/combined command-zone prices separately from full archived inventory scores. Known unlisted identities use zero; identities missing from the league catalog remain Pending. Search pages pin one published version; refresh explicitly loads the newest. Static research comparisons use bundled v3 and never claim to be a snapshot of a possibly edited hosted schedule. No price, budget or game rule is changed.

## Limits and delivery

No paired games or outcome measurements were available. Conditional lines require the exact named state, enough library/mana, and no relevant disruption. Published mechanics should still be reviewed by an organizer/judge, particularly after new Oracle/rules updates. Split-head commander damage remains the existing unresolved question; every numerical commander kill here uses one recipient. The optional live Discover commanders UI was omitted: the local index and existing Points/Scryfall page cover discovery without adding per-keystroke API traffic or automatic publication.

The feature reuses Express/PostgreSQL/vanilla JS. Separate immutable composition versions, drafts, publication, hide/restore and backup/recovery are implemented. Idempotent seeding never overwrites organizer edits. CI validates the reviewed corpus. Executed acceptance counts and deployment limits are in `acceptance-results.json`. Production is untouched; Railway OAuth refresh is expired, so hosted staging verification is unavailable. Local Chrome and actual-image smoke checks are local evidence, not hosted deployment evidence.
