# PRIMER_MULLIGAN_DECISION_TREE_V1

SIM-001 MULL-006, section 25. This is the human-facing distillation of everything MULL-006 built:
engine strength (`engine_strength_prior.json`), relative deployment speed (`relative_speed_model.json`),
their combined matrix (`strength_speed_matrix.json`), draw dependence and outs
(`draw_dependence_analysis.json`, `outs_analysis.json`), fragility/recovery
(`trajectory_fragility_analysis.json`, `trajectory_recovery_analysis.json`), seat exposure
(`seat_adjusted_trajectory_census.json`, `seat_pod_matrix.json`), pod realization
(`pod_realization_prior.json`), relevant agency (`relevant_agency_analysis.json`), and the
re-derived mulligan-depth thresholds (`contextual_london_results.json`).

**The assignment's illustrative sketch had 7 questions. This tree uses 5.** The two dropped —
"does my remaining interaction matter in this pod" and an explicit seat question — are real,
measured effects (`seat_pod_matrix.json`: 9.1% of tracked hands flip decision across seats, 4.1%
flip across pod archetypes), but they are secondary in magnitude next to the four questions below,
so they are folded into a single "fine-tuning" note at the end rather than kept as full branches.
The evidence — not a desire for a fixed 7-question shape — is what set this length; see the
assignment's own instruction not to force the sketch if the evidence says otherwise.

---

## The Tree

```
Q1. DESTINATION
    Do I have a REAL destination? (a resource engine, a functional Birthing Pod or Survival
    of the Fittest, or an Oculus route - NOT "how much mana or interaction do I have")
        NO  -> MULLIGAN. Full stop.
               Mana, interaction, and card count NEVER rescue a hand with no destination -
               relevant_agency_analysis.json's own boundary check found 681/6000 sampled
               D/F-tier hands still had at least one live interaction spell, 136 had 2+, and
               EVERY one of them remained a mulligan.
        YES -> continue to Q2.

Q2. TIMING
    Is this destination arriving EARLY or ON TIME for THAT SPECIFIC ENGINE'S own normal curve,
    or is it LATE? (Not "what turn is it" in isolation - a turn-2 Mystic Remora is ON TIME;
    a turn-2 Smothering Tithe is AHEAD OF CURVE and exceptional; a turn-2 Faerie Mastermind is
    ON TIME; a turn-3 Faerie Mastermind is BEHIND CURVE.)
        LATE -> this destination alone is weak. It needs an unusually strong answer to Q3/Q4 to
                be worth keeping - otherwise lean MULLIGAN.
        EARLY / ON TIME -> continue to Q3.

Q3. IS IT ALREADY THERE?
    Look at the actual 7 cards in hand: can this destination be executed with what you're
    already holding (self-contained, or "broad outs" - many remaining cards would also work),
    or are you counting on drawing ONE specific card (narrow or exact outs)?
        NARROW / EXACT OUTS NEEDED -> this is the single biggest trap in this whole model.
               draw_dependence_analysis.json found 41.8% of size-7 hands whose best trajectory
               reaches an engine actually need that engine card to be a natural topdeck, not
               something already in hand - and outs_analysis.json shows that when the missing
               piece is the engine itself (not a land), there is exactly ONE copy left in a
               singleton deck (~1-2% chance by the turn it's needed). A hand that "has an
               engine" this way does not actually have one yet. Downgrade hard; don't keep on
               destination-name alone.
        SELF-CONTAINED / BROAD OUTS -> continue to Q4 with real confidence.

Q4. IF IT GETS ANSWERED, AM I DONE?
    If your one destination gets removed the moment it lands, do you still have real cards,
    mana, or a second plan - or does the whole hand evaporate?
        HAND COLLAPSES (ALL_IN) -> only keep if the destination itself is exceptional
               (S+ or S tier - a T1 functional Pod, a T1/T2 Smothering Tithe). An ordinary
               engine that also happens to be your entire hand is a real risk -
               trajectory_fragility_analysis.json found ALL_IN hands make up 7.1% of tracked
               trajectories, and they carry zero live interaction 100% of the time in that
               sample.
        SOMETHING LEFT (ROBUST / RECOVERABLE) -> keep, even for a merely-good destination.

Q5. IS THIS GOOD ENOUGH FOR MY CURRENT MULLIGAN DEPTH?
    At 7:  demand a real, mostly self-contained, on-time-or-better destination (roughly
           strength_speed_matrix's C band or better).
    At 6:  a solid destination is fine even if a little late or needing modest support
           (contextual_london_results.json's reused threshold: D or better).
    At 5:  a coherent secondary engine, or a trajectory that's a genuine but real "narrow outs"
           speculation, becomes acceptable (also D or better - the standard doesn't get
           stricter, but the POOL of hands you're choosing from is worse, so more of them clear
           the same bar).
    At 4:  coherence and playability dominate perfection - keep almost anything with a real,
           legal destination rather than mulligan further (mull005r_hand_size_thresholds.json's
           own economics already found no threshold clears the cost of a fifth mulligan).
```

## Fine-Tuning Note (seat and pod - real, but secondary)

Once the four questions above say KEEP, two more things can still nudge the decision, though
neither is large enough to deserve its own branch:

- **Seat**: a fragile or all-in trajectory is measurably worse from Seat 3/4 than Seat 1/2 -
  more opponent turns pass before you even land it. `seat_pod_matrix.json` found 9.1% of
  tracked hands flip KEEP/MULLIGAN purely from seat, concentrated in exactly the FRAGILE/ALL_IN
  hands Q4 already flags.
- **Pod**: an opponent-triggered engine (Rhystic Study, Mystic Remora, Esper Sentinel, Smothering
  Tithe, and the others in `pod_realization_prior.json`) is worth less against a pod that can
  easily pay through its tax, or that doesn't generate the triggers it needs. This is a
  STRATEGIC_PRIOR_UNVALIDATED qualitative adjustment, not a measured rate - `seat_pod_matrix.json`
  found a 4.1% flip rate from pod alone.

Neither fine-tuning factor can turn a genuine SNAP KEEP into a MULLIGAN on its own, and neither
can rescue a hand that failed Q1.

---

## Four Worked Examples (real simulated hands, from `contextual_disagreement_examples.json`)

**Q2 in action (STRENGTH x SPEED, disagreement A)**
`Chrome Mox, Exotic Orchard, Faerie Mastermind, Force of Will, Oboro Breezecaller, Scrubland,
Volatile Stormdrake` reaches T1 Faerie Mastermind (AHEAD OF CURVE for that engine) and grades
A+. A separate hand, `Birthing Pod, Esper Sentinel, Flare of Denial, Gemstone Caverns, Noble
Hierarch, Shifting Woodland, Smothering Tithe`, reaches T2 Esper Sentinel (BEHIND CURVE for that
engine) and grades only C+ - despite Sentinel being an intrinsically similar-or-stronger card.
Timing relative to the engine's OWN curve, not raw power, decided the gap.

**Q3 in action (DRAW DEPENDENCE, disagreement C)**
`Archivist of Oghma, Boseiju Who Endures, Chord of Calling, City of Traitors, Demonic Tutor,
Misty Rainforest, Rhystic Study` looks like a clean T2 Rhystic Study line. Rhystic Study is not
actually in this hand - the search only reaches it because this particular shuffle happened to
deal it on turn 2. A pilot reading the opening 7 alone would correctly see no engine at all.

**Q4 in action (FRAGILITY, disagreement D)**
Two real hands both reach Esper Sentinel as their best trajectory. `Bayou, Elvish Spirit Guide,
Gilded Drake, Mindbreak Trap, Nature's Rhythm, Polluted Delta, Sol Ring` keeps 4 cards and a
realized second destination (Runic Armasaur) - ROBUST. `Abhorrent Oculus, Boseiju Who Endures,
Demonic Tutor, Esper Sentinel, Marsh Flats, Misdirection, Tropical Island` keeps 0 cards with no
fallback if Sentinel is answered - ALL_IN, and the hand effectively collapses. Same destination
name; not the same trajectory.

**Q5 in action (MULLIGAN DEPTH, disagreement G)**
`Ancient Tomb, Devoted Druid, Mana Vault, Mystic Remora, Oboro Breezecaller, Starting Town,
Underground Sea` grades a contextual D - a mulligan at 7 (which demands C or better) but a keep
at 6 or 5 (which accepts D or better), with no bottoming or redraw needed at all. The same seven
cards; a different standard.

---

## What This Tree Deliberately Leaves Out

- It does not ask "how much mana do I have" as a standalone question - `acceleration remains a
  means, never a destination` throughout this project (Mana Vault, Sol Ring, Ancient Tomb, City
  of Traitors, Chrome Mox, Mox Diamond, Lotus Petal, dorks, Kinnan, and Gaea's Cradle all only
  matter insofar as they feed Q1's destination).
- It does not ask about Tymna (zero generic mulligan credit) or generically about Thrasios
  (relevant only via a concrete benefit already folded into whether a destination exists).
- It does not give live interaction its own top-level branch, because `relevant_agency_analysis.json`
  confirmed interaction can only ever UPGRADE an already-coherent hand (Q1 already passed),
  never rescue one that failed Q1.
