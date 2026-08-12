**GATE_4A_2P_DIAGNOSTIC v2** — rerun of the 100-game batch after fixing the
hand-dealing defect found while building `results/solo_baseline/`
(`INFRA-0008`) — see that directory's README for the full explanation.
Same subject deck/hash as v1. **Sample reduced to 40 games** (seeds 1-40,
max turn 8, skill 6), not the original 100, because real hands make each
game much more expensive for the AI to search (avg 15.9s/game vs. v1's
2.87s) and this investigation+refix consumed most of this session's
remaining time budget — a follow-up run at n=100 is straightforward with
the same tooling, just takes longer wall-clock time than fit here.

40/40 completed, 0 exceptions, 0 engine errors. Mean 102.6 events/game
(vs. v1's 50.6 — real hands roughly doubled genuine activity). 3/40
detected winners, all three tracing to the identical `INFRA-0007`
mechanism (AI never pays Pact of Negation's deferred cost) already found
in v1 — confirms that finding is real and not a hand-size artifact.
Automated defect scan: 0 hits beyond the known Gilded Drake reminder-text
false positive. No new rules/adapter/transcript defects found.
