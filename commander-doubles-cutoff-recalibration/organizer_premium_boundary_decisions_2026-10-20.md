# Commander Doubles — Organizer premium and cutoff decisions

**Status: approved numerical proposals for next Season 0 consolidation; NOT activated.**

This records direct user decisions following review of the recalibrated schedule at commit `4809836` on `commander-doubles-cutoff-recalibration`. These are **actual construction points**, not 0–5 qualitative tiers. Later, explicit organizer numerical decisions take precedence over earlier agent working numerical suggestions. Preserve previous 50 qualitative anchors verbatim and list cross-scale tension transparently rather than silently deleting historical judgments. Apply in final unactivated candidate export, not the currently published `recalibrated_point_schedule.csv` until a separate regeneration/version step.

| Card | Location | Old | Organizer-selected | Delta |
|---|---|---:|---:|---:|
| Orim's Chant | main | 12 | **3** | -9 |
| Necrodominance | main | 12 | **11** | -1 |
| Heartless Hidetsugu | commanders | 12 | **10** | -2 |
| Time Sieve | main | 8 | **8** | +0 |
| Orcish Bowmasters | main | 8 | **3** | -5 |
| Sylvan Library | main | 8 | **7** | -1 |
| Expropriate | main | 7 | **8** | +1 |
| Trickbind | main | 1 | **0** | -1 |
| Faerie Mastermind | main | 1 | **0** | -1 |
| Snapcaster Mage | main | 1 | **0** | -1 |
| Anje Falkenrath | main | 1 | **0** | -1 |
| Disrupting Shoal | main | 1 | **2** | +1 |
| Aluren | main | 1 | **2** | +1 |
| Dream Halls | main | 1 | **2** | +1 |
| Misdirection | main | 0 | **2** | +2 |
| Urza, Lord High Artificer | main | 0 | **1** | +1 |
| Chains of Mephistopheles | main | 0 | **1** | +1 |

## Direct organizer reasoning

> Things like Dream Halls and Aluren still affect your opponents. While they have combo potential and may help your teammate, they help both opponents too. They deserve a couple of points, not a huge charge. Misdirection and Disrupting Shoal are bad free counterspells, but they're still free.

Interpretation:
- **Aluren 2, Dream Halls 2:** potentially significant in decks built around them, but effects help opponents too. No automatic surcharge for friendly deck construction or teammate synergy.
- **Misdirection 2, Disrupting Shoal 2:** conditional/weaker than premium free answers, but free casting itself is competitively valuable.
- **Orim's Chant 3** is a particularly substantial change; unlike Silence, it restricts *one target opponent*, leaving the other free to cast spells. The earlier qualitative tier-5 Orim's Chant anchor remains in historical record, but the *latest explicit numerical construction price is 3*, authoritative for the draft schedule. Flag qualitative-numeric inconsistency in approval summary; do not overwrite original tier.
- **Time Sieve 8** explicitly reaffirmed despite an assistant's lower suggestion; avoid automatic reduction.
- **Heartless Hidetsugu command-zone 10**, with main-deck price 8 remaining separately proposed (not newly approved by this decision).

## Implementation guidance

Persist these as Oracle-ID-keyed *zone-specific* numeric overrides after resolving exact printed names to card IDs from the original frozen/current Oracle data. Do not apply CZ price to main or vice versa. Rebuild preview totals and report 17 affected location entries, including unchanged Time Sieve. Retain existing bans, all 50 qualitative anchor observations, controller-specific 2HG rulings, cutoff recommendation >77.5, and team-budget recommendation as **proposals awaiting final adoption**. No official league activation, and no new combo restriction or unban is authorized.
