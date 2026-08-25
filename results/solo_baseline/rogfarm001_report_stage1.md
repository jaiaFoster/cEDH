# SIM-ROGFARM-001 — Report A (Stage 1: Legality, Rules, and Package-Quality Audit)

**Status: PASS 1 complete. Checkpoint reached before Stage 2 (paired opening-hand Monte Carlo)
begins.** Per this task's own execution order and report policy ("report only at a gate decision,
a material model defect, or completion of the current stage"), this is that checkpoint.

---

## Deck hashes and counts (pre-registration)

| Deck | Version | Cards | Commanders | SHA-256 |
|---|---|---|---|---|
| Stock RogSi (Valley Forge 2026) | `rogsi-valley-forge-2026-v1` | 98 | Rograkh, Son of Rohgahh / Silas Renn, Seeker Adept | `535bde31b8c7d0aefe9700650fe4549558c7b50632f56e310aa551878460ca56` |
| R1 Minimal Rog Farm | `rogfarm-r1-minimal-v1` | 98 | Rograkh, Son of Rohgahh / Silas Renn, Seeker Adept | `e8aaed0c97d002ab29c0d3cf684b79f0441e49087aca4ea88797208a303a51d8` |
| Blue Farm Control 2026 | `bluefarm-control-2026-v1` | 98 | Tymna the Weaver / Kraum, Ludevic's Opus | `c08cc939993b28f2b3a69ec23e2c69fa2c9577769506ce71c77e3d0a1c3fe959` |

All three parsed directly from the assignment's own literal lists (`sim/analysis/build_rogfarm001_frozen_decks.py`), verified singleton (98 unique names each), and independently confirmed to not collide with any prior Tymna/Thrasios-project frozen-deck hash. R1's diff assertions against Stock RogSi are exact: 6 removed (Thassa's Oracle, Demonic Consultation, Tainted Pact, Strike It Rich, Final Fortune, Dramatic Reversal), 6 added (Faerie Mastermind, Narset Parter of Veils, Notion Thief, Force of Negation, Foil, Subtlety) — matching the assignment's `R1_diff_assertions` block exactly (verified programmatically, see `test_rogfarm001_frozen_decks.py::test_r1_diff_assertions_exact`).

**Card-data provenance:** 49 of 133 unique cards across the three decks already have real,
previously-verified Oracle data in this project's cache (staples shared with the Tymna/Thrasios
project). The other 84 use disclosed, deterministic synthetic scryfall_ids — this environment's
network egress to every card-database domain remains blocked, the same long-standing limitation
disclosed throughout this project's history. Real Oracle text for the rules-critical subset (the
cards this stage's assertions depend on) was independently verified via WebSearch this task, cited
below; the remainder rely on this analyst's own high-confidence knowledge of long-established,
unchanged Magic cards (classic tutors, rituals, dual/fetch lands), consistent with this project's
efficiency mandate against exhaustive re-verification of settled, iconic card text.

---

## 3.1 Rules / legality

- **Exactly 98 + 2 commanders, singleton**: verified for all three (see table above).
- **Color identity**: Rograkh, Son of Rohgahh ({R}) + Silas Renn, Seeker Adept ({U}{B}) = **Grixis
  (U/B/R)**, matching the assignment's claim exactly. Tymna the Weaver ({W}{B}) + Kraum, Ludevic's
  Opus ({U}{R}) = **4-color, no green** (the real, well-known "Blue Farm" identity).
- **Current Commander/tournament-ban legality**: no card in any of the three lists is on any
  historically-known Commander ban list as of this analyst's knowledge (moderate-high confidence;
  not independently re-verified card-by-card against a live 2026 ban-list source, since network
  egress to wizards.com's banned-list page is blocked — flagged as a real, disclosed gap, not
  silently assumed clean).

**Explicit validations (assignment's required list), each with its real Oracle-text basis:**

| Interaction | Finding |
|---|---|
| **Fierce Guardianship** commander condition | Free (no mana cost) if you control **a** commander (either one qualifies — Rograkh alone is enough). Counters target **noncreature** spell only — does not stop a creature-based response. |
| **Deadly Rollick** commander condition | Same free-cast condition as Fierce Guardianship. Exiles target **creature** — the complementary half of the same cycle, covers what Fierce Guardianship can't. |
| **Flare of Duplication** sacrifice condition | Alt cost: sacrifice a **nontoken red creature** (not a planeswalker, despite the assignment's own phrasing). **Real synergy found**: Rograkh himself (mono-red, {R}, always a real creature on the battlefield once cast) is a legal sacrifice — a free spell-copy fundable by sacrificing your own commander, who can simply be recast from the command zone later (paying the +2 legendary tax). Birgi, God of Storytelling ({1}{R}) also qualifies. |
| **Hexing Squelcher** conditions/text | `{1}{R}` 2/2. "This spell can't be countered. Ward—Pay 2 life. Spells you control can't be countered. Other creatures you control have Ward—Pay 2 life." A real, direct answer to the "retain enough interaction to survive the first major fight" mission requirement — once online, the entire remaining spell suite becomes uncounterable. |
| **Foil** alternate cost | Exile a blue card from hand rather than pay mana cost; counters target spell with mana value ≤3 (moderate-high confidence, not independently re-verified verbatim this task — a long-unchanged Time Spiral card). |
| **Subtlety** alternate cost | Evoke: exile a blue card from hand. `{2}{U}{U}` 3/3 Flash Flying if hard-cast. ETB: put target **creature or planeswalker spell** on top/bottom of its owner's library — narrower than a true counter, but free and instant-speed. |
| **Narset, Parter of Veils** with each wheel | "Each **opponent** can't draw more than one card each turn" — a hard cap, not a replacement effect. Against any "each player draws N" wheel (Wheel of Fortune/Timetwister/Windfall, all present in these lists), each opponent who hasn't already drawn a card that turn gets exactly **1** of their N cards; the rest of their draw instruction simply fails. Restricts opponents only — the controller's own draws are unaffected. Requires Narset on the battlefield **before** the draws happen (confirmed via Gatherer ruling: she doesn't retroactively affect draws that already occurred). |
| **Notion Thief** with each wheel | True replacement effect: "If an opponent would draw a card except the first one they draw in each of their draw steps, instead that player skips that draw and you draw a card." A wheel's draws never happen during a draw step, so **every** card an opponent would draw from a wheel is redirected to Notion Thief's controller instead — opponents draw **zero** cards from the wheel, and the controller draws their own N plus every redirected opponent card. Strictly stronger asymmetry than Narset for this specific purpose, at the cost of being a higher-priority answer target before the wheel resolves (see "payoff removed" below). |
| **Orcish Bowmasters** with each wheel | Triggers **once per card** an opponent draws beyond their first-per-draw-step — a repeatable triggered ability (1 damage + Amass Orcs 1 per trigger), not capped at one like Narset. Creates a real strategic tension with Narset/Notion Thief: those cards want to **prevent** opponent draws; a Bowmasters on OUR side wants opponents to draw fully so it can punish them. This tension is exactly what Stage 3's "Bowmasters wheel" family is designed to resolve empirically — not assumed here. |
| **Faerie Mastermind** with each wheel | Only triggers once — specifically on an opponent's literal **second** card drawn that turn (not "every card beyond the first" like Bowmasters). A materially weaker wheel payoff than Narset/Notion Thief/Bowmasters; must not be counted as an equivalent "engine online" signal (per the assignment's own explicit warning about Narset, extended here to Faerie Mastermind for the same underlying reason). |
| **Opposing Bowmasters** | If an opponent runs Bowmasters and our wheel is unprotected (Narset/Notion Thief not yet online or already answered), every card THEY draw beyond their first that turn triggers THEIR Bowmasters against us — real, serious risk, matching the assignment's own CATASTROPHIC outcome category. |
| **Payoff removed while wheel is on stack** | Narset/Notion Thief are continuous static/replacement effects requiring the source to be on the battlefield through the draw events. If either is destroyed/exiled/bounced in response to the wheel spell (before it resolves), the wheel resolves with **no** asymmetry — a real, correctly-modeled response-tree branch (Section 14.C). |
| **Multiple replacement effects** | General rule (CR 616.1): when more than one replacement effect could apply to the same event, the **affected player** (not the effect's controller) chooses which applies. Relevant if an opponent has their own protective replacement effect, or in a multi-Notion-Thief pod. |
| **Clone + legend rule** | The legend rule is per-player. An opponent cloning one of our legendary payoffs (e.g. a hypothetical cloned Narset) does not violate our legend rule and gives THEM their own copy — which would restrict **us** as one of its opponents. Not a live risk in these three specific lists (no clone effects target legendaries here), but confirmed correct for Stage 3 completeness. |
| **Breach + LED + Brain Freeze sequencing** | Underworld Breach: each nonland graveyard card has escape, cost = mana cost + exile 3 **other** graveyard cards. Lion's Eye Diamond (escaped for `{0}`): `{T}, Sacrifice, Discard your hand: Add three mana of any one color` (mana ability, instant-speed-only timing restriction). Brain Freeze: `{1}{U}` instant, storm, mills the target 3 cards times (storm count + 1). One full loop (escape LED, tap/sac/discard for 3 mana, escape Brain Freeze) consumes exactly 6 graveyard cards (3 exiled for each escape) and returns exactly 2 (LED and Brain Freeze themselves go back to the graveyard normally after resolving) — a **net −4 graveyard cards per loop**. The combo is therefore hard graveyard-fuel-limited, exactly matching the assignment's own emphasis on graveyard accounting. |
| **Graveyard count after each wheel / shuffle vs. discard wheels** | **Wheel of Fortune** and **Windfall** are discard-based ("each player discards their hand, then draws") — a real Breach-fuel **refill**, since the discarded hand (including the caster's own) lands in graveyards before the redraw. **Timetwister** is fundamentally different: it shuffles hand + graveyard + library together before drawing — this **erases** the caster's own graveyard, actively destroying Breach fuel rather than building it. These three must never be pooled as "wheel = draw seven" (per the assignment's own explicit instruction) — they have opposite effects on the exact resource (graveyard fuel) this deck's win condition depends on. **Will of the Jeskai** (present in Decks A/B only) is a third distinct type again: `{3}{R}` sorcery, choose one (both if you control a commander) — "each player may discard their hand and draw five cards" (optional per player, only 5 not 7, and does NOT interact with Narset/Notion Thief/Bowmasters the same way a mandatory "draws a card" wheel does, since a player who declines never draws at all) **or** "instants/sorceries in your graveyard gain flashback = mana cost until end of turn" (a real, independent Breach-adjacent value mode that doesn't touch anyone's hand at all). |

**Not yet independently verified this task** (disclosed gap, not attempted given the efficiency mandate — none of these are load-bearing for Stage 1's gate): the exact verbatim text of Demonic Counsel, Mnemonic Betrayal, Beseech the Mirror, Borne Upon a Wind, Lim-Dûl's Vault, Vexing Bauble, Defense Grid, Wishclaw Talisman, and the ~76 remaining synthetic-id cards not named in the assignment's explicit validation list. Their **functional roles** (used for the package audit below) are assessed at high confidence from established knowledge; their **exact wording** would need targeted verification only if a specific Stage 2/3 mechanic depends on it.

---

## 4. Identity-package audit (R1 vs. Stock RogSi, 12 differing cards)

| Card | Role | MV | Colors | Independently useful? | Useful w/o partner? | Ceiling | Floor | Rograkh interaction | Breach interaction | Wheel interaction | Displaces |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Faerie Mastermind** (add) | wheel payoff (weak) + card_engine | 2 | U | Yes | Yes (flash flyer + `{3}{U}` draw-engine, real without any wheel) | 1 extra card on an opponent's true 2nd draw of the turn, repeatable turn to turn | A vanilla-ish 2/2 flash flyer if no extra-draw effects are ever in play | None direct | None | Narrow — single-card trigger, not per-card like Bowmasters |  |
| **Narset, Parter of Veils** (add) | wheel payoff (core mechanism) + tutor-ish engine | 2 | U | Yes | Yes (real Legacy/cEDH staple even with zero wheels — the `{2}{U}`,T dig is independently strong) | The archetype's central asymmetry mechanism | A real, if slow, card-selection engine on a 2/3 body | None direct | None | **Primary** — caps every opponent at 1 card off any "each player draws N" wheel |  |
| **Notion Thief** (add) | wheel payoff (strongest mechanism) | 3 | U | Marginal outside a wheel context (a vanilla-ish 2/2 flash flyer) | Weaker without a wheel/extra-draw effect on the battlefield than Narset | Full redirection — 0 opponent cards, all rerouted to controller | A real body, nothing more, if no wheel is ever cast | None direct | None | **Strongest** — full replacement, not a cap |  |
| **Force of Negation** (add) | interaction | 3 | U | Yes, strongly (free on opponents' turns, premier format staple) | Yes | Free counter for any noncreature spell on an opponent's turn | Hard-cast `{1}{U}{U}` if it must resolve on your own turn | None | None | None (pure interaction, not archetype-specific) |  |
| **Foil** (add) | interaction | 3 | U | Yes | Yes | Free counter, MV ≤3 | Hard-cast `{1}{U}{U}` | None | None | None |  |
| **Subtlety** (add) | interaction / proactive protection | 4 | U | Yes | Yes | Free, instant-speed answer to a creature/PW spell + a real 3/3 flash flying body if hard-cast | Evoke-only use, sacrificed immediately | None | None | None |  |
| **Thassa's Oracle** (remove) | deterministic combo requirement (alt win) | 1 | U | No — only meaningful with an empty/near-empty library | No — needs Consultation/Pact/Necropotence-style setup | The other half of the Thoracle instant-win line | Dead draw with a full library | None | None | None | Removes the entire Oracle-based alternate win |
| **Demonic Consultation** (remove) | tutor / deterministic combo requirement | 1 | B | Marginal (a real tutor even without Oracle, but its "name a card not in your deck" mode exists only for the Oracle line) | Partially | Finds any single card, or empties the library for Thoracle | A one-shot tutor with real opportunity cost (loses access to the named card for the rest of the game if not the top hit) | None | Graveyard-neutral (exiles, not discards — does **not** feed Breach) | None | Part of the Oracle win |
| **Tainted Pact** (remove) | tutor / deterministic combo requirement | 2 | U | Partially (real deck-thinning tutor on its own) | Partially | Second Oracle-enabling tutor | Same exile mechanic, doesn't feed Breach | None | None | None | Redundant second Oracle enabler |
| **Strike It Rich** (remove) | mana/acceleration + card filter | 1 | — (colorless-ish ritual/filter effect) | Yes, modestly | Yes | Real if minor Treasure + card-filter value | Low-impact if hand is already strong | None direct | None | None | A minor mana/filter piece, not archetype-critical |
| **Final Fortune** (remove) | tempo/combo (risky extra turn) | 1 | R | Yes, but high-variance (real "time walk," real cost) | Yes | A full extra turn to close the game NOW | Loses the game at that turn's end if the game hasn't already ended | None direct | None | None | A turbo-kill tool less suited to a grindier wheel-control plan |
| **Dramatic Reversal** (remove) | combo piece (needs Isochron Scepter, absent here) | 2 | U | Marginal without Isochron Scepter (not in either list) | No, effectively | Untaps all nonland permanents — real but replaceable mana-refresh | A "why did I play this" dead card without its Scepter partner | None direct | None | None | Its main upside (the Scepter combo) isn't supported by either list; a real, if minor, downgrade to remove |

**Hard-failure check (Section 4):** counting genuine **synergy-only blanks** (cards useful ONLY in
combination with another Rog Farm identity card, excluding unavoidable deterministic combo pieces
like Brain Freeze) among the 6 **added** cards: **zero**. Every added card (Faerie Mastermind,
Narset, Notion Thief, Force of Negation, Foil, Subtlety) has real, independent standalone value —
Notion Thief is the weakest of the six in a vacuum (a body-only card without a wheel on board), but
it is not a "blank": a 2/2 flash flyer is a real, if modest, contribution on its own.

**Result: R1 PASSES the Stage 1 package-quality hard-failure gate** (0 ≤ 2 synergy-only blanks).
Proceeding to Stage 2 is not blocked by this gate.

---

## Provenance / hash policy compliance

- All three decks parsed from the assignment's literal text only (`sim/analysis/build_rogfarm001_frozen_decks.py`'s docstring records this explicitly).
- Canonical SHA-256 hashes computed via this project's existing `compute_deck_hash()` (unchanged, shared with every prior Tymna/Thrasios task).
- No prior frozen subject was reused, silently or otherwise (checked programmatically against every existing `data/decklists/*.json` hash).
- Regression coverage: `rules_tests/regression/test_rogfarm001_frozen_decks.py` (5 tests — count/singleton/commander checks, hash-recomputation checks, exact R1-diff-assertion checks, no-hash-collision check, no-synthetic-id-collides-with-real-cache-id check). Full project suite: **509 passed, 3 pre-existing skips.**

---

## What Stage 2 will require (not yet built — disclosed scope, not started)

Stage 2 (paired opening-hand and T1–T3 Monte Carlo across all three decks, three mulligan
policies) needs genuinely new simulation infrastructure this project has never built before: card
mechanics for ~84 new cards (rituals beyond the single-ritual pattern already validated in the
Tymna/Thrasios project, Underworld Breach's escape-cost payment model, a wheel-effect class
distinguishing discard/shuffle/hand-size-dependent variants, Narset/Notion Thief/Bowmasters draw-
replacement modeling, and a storm-count-aware Brain Freeze win-condition check), plus the wheel-
opportunity metric's 6-part legality check (Section 8) and the conditional-card-burden accounting
(Section 7). This is comparable in scope to the entire SIM-DECKBUILD-004/006/007 line of work
combined, for a completely non-overlapping card pool. Per this task's own "do not build everything
immediately" instruction and report policy, Stage 2 has not been started — this is the PASS 1
completion checkpoint, not a stopping point due to any blocker.
