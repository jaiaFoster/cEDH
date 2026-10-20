# Final audit decision package — season0-proposed

**Not ready for a permanent league lock. Ready for organizer review and a monitored Season 0 pilot only after separate line/lock policy is approved.** Fixed additive prices are internally coherent as construction resources, but cannot enforce Bracket 3 intent. The audit found actual zero-budget early wins under the saved backend with ordinary free commanders.

| cohort | n | median | p10 | p90 | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| adversarial_fixture | 26 | 1.5 | 0.0 | 10.0 | 0 | 39 |
| bracket3_declared | 150 | 66.0 | 19.0 | 139.2 | 1 | 198 |
| cedh_holdout | 2520 | 278.0 | 160.0 | 425.1 | 7 | 505 |
| official_precons | 174 | 16.0 | 15.0 | 22.0 | 1 | 30 |

1. Philosophy: coherent; fixed location prices, no synergy surcharge. It intentionally leaves synergistic advantages uncharged.
2. Largest anchor effects: Chant/Food Chain/proactive protection increase; five commanders become free; Tithe becomes elite. Qualitative tiers all preserved, numbers provisional.
3. Ten largest human-anchor reprices:

| card_name | zone | old_points | new_points | change |
| --- | --- | --- | --- | --- |
| Food Chain | main | 1 | 12 | 11 |
| Orim's Chant | main | 1 | 12 | 11 |
| Grand Abolisher | main | 3 | 13 | 10 |
| Ranger-Captain of Eos | main | 3 | 13 | 10 |
| Silence | main | 5 | 14 | 9 |
| Voice of Victory | main | 3 | 12 | 9 |
| Fierce Guardianship | main | 5 | 13 | 8 |
| Inalla, Archmage Ritualist | commanders | 8 | 0 | -8 |
| Kenrith, the Returned King | commanders | 8 | 0 | -8 |
| Najeela, the Blade-Blossom | commanders | 8 | 0 | -8 |

4. Exceptional free resources remain: Kenrith/Najeela/Inalla/Derevi/Yuriko command access, many ordinary interchangeable payoffs, utility fixing and some high-ceiling specialized cards. See unpointed_high_power_cards.csv.
5. Clear removal: Rift main becomes0 per human authority; five commander prices become0. Skullclamp reduced. Other inherited marginal1-point utility lacks strong evidence; review queue is not hidden.
6. Largest free-commander risks: Inalla copy engine, Kenrith outlet/counter engine, Najeela repeat combat, double Yuriko damage; Derevi supports untapping/locks without shared mana.
7. Genuine split combos include Chain/Apprentice, Dualcaster/Twinflame, RIP/Helm, Painter/Grindstone, Alarm/token producer, Displacer/Drake and active Ascension/Mindcrank. Bond/Blood, Kinnan/Basalt and Oracle/Consultation split fail.
8. Most severe constructed examples: baseline T01 zero-point turn-two drain; T03 zero-point turn-three hasty army; T02 2-point turn-one Chancellor line. These are possible conditional openings, not measured reliability. Current proposed costs are in adversarial_team_scores.csv.
9. Material rules: separate event/control/resource ownership, both-opponent drain, shared turns/extra turns/control, Grace team cannot-lose vs Protection shared-life lock, per-head commander damage conflict.
10. Individual enablers can be repriced (Chain/Dualcaster3, Alarm4, tutors/fast mana/protection); prices alone cannot remove all equivalent combinations.
11. Repeatable engines, early reliable deterministic lines and severe participation/land locks need separate written legality review. No early invulnerability or combat loophole.
12. Recommended pointed size: 321 currently legal identities (269 main, 79 command-zone; overlap allowed). This is policy, not a natural optimum.
13. Pilot budget:60 reference each,120 team,72 individual maximum, at most12 transferred from teammate's unused reference. Do not adopt without separate gameplay policy.
14. Uncertainty: biased labelled cohorts, no paired 2HG outcomes, hypothetical opening consistency,423 inherited low-confidence tail rows, subjective boundary/price judgments and fresh rulebreaker coverage.
15. Permanent lock: no. Version all approvals and run actual paired playtests first.

| Urgency | Organizer approval needed | Proposed decision |
| --- | --- | --- |
| P0 | Gameplay legality scope | Published controller-aware prohibited-line register and appeal process; explicit engine/lock/early-line review. |
| P0 | Commander damage | DetailedCR:21 to individual head; disclose website conflict. |
| P0 | Free commander risks | Preserve all human zeros; approve separate strategy restrictions or knowingly accept them. |
| P1 | Numeric schedule and budget | season0-proposed;60/120/72 with20% transfer, not official activation. |
| P1 | Current snapshot release | Refresh/resolve rulebreaker and missing new cards before accepting such decks. |
| P2 | Experimental unbans | None approved; keep all official bans. |


The default audited_point_schedule.csv contains only legal pointed identities. Hypothetical banned prices are isolated in hypothetical_inclusive_point_schedule.csv and experimental_unban_review.csv. Organizer approval questions, exact options and supporting cases are in organizer_decisions.csv. D05 explicitly addresses the finite double-Yuriko line, which an infinite-loop ban alone would miss.
