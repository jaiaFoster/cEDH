**GATE_4A_2P_DIAGNOSTIC** — rules-engine/adapter/basic-policy stress test,
NOT cEDH metagame inference. 100 real, deck-backed 2-player Commander Duel
games, `tymna-thrasios-treefarm-v1` mirrored on both seats (deck hash
`4edee0fc60768fcd759a2e9fd3c34277d9d37c0d6a27a663ea7beff76b05e20a`, recorded
on every game record), `ComputerPlayer7` skill 6, seeds 1-100, max turn 12,
batch `gate4a-2p-batch001`. See `gate4a-2p-batch001-SUMMARY.json` for the
raw operational numbers.

## Operational statistics (not strategic evidence)

- 100/100 games completed (`status: OK`), 0 exceptions, 0 chunk
  failures/timeouts, 0 engine (log ERROR-level) failures.
- 5,065 total events, mean 50.6/game (min 17, max 158).
- Mean 2.87s/game (max 18.6s) - no game approached the 280s per-chunk
  timeout; no hang observed.
- 5/100 games reached a detected winner (`"has won/lost the game"` in the
  transcript) within the 12-turn window; the other 95 were still in
  progress at the turn cap, which is expected and not itself a problem -
  `max-turn 12` was chosen for batch throughput, not to guarantee
  game-enders.

**Per the owner's explicit instruction, none of the above (nor the 5/100
"win rate") should be read as win-rate, matchup, mulligan, card-strength,
or cEDH-competitiveness evidence.** This is a rules/adapter/policy
integration stress test against one mirror-matched deck under one specific
default AI - see the finding below for a concrete illustration of why.

## Defect review

Reviewed all 100 transcripts: automated scan for illegal/exception/crash
keywords (2 hits, both false positives - see below), mechanic-specific
spot-checks (Birthing Pod, Survival of the Fittest, Force of Will,
Evoke, fetchlands, commander casting/tax), activity-distribution outlier
review (slowest and lowest-event games), and full manual read of every
game that reached a winner.

**Zero RULES_DEFECT, ADAPTER_DEFECT, or TRANSCRIPT_DEFECT found.**
Specifically confirmed correct:
- `seed10`: Force of Will cast at its alternative cost (1 life + exile a
  blue card) targeting an opponent's Lotus Petal spell on the stack; the
  opponent responded with Veil of Summer ("spells you control can't be
  countered this turn"), which resolved first (LIFO) - Force of Will then
  correctly failed to counter Lotus Petal ("could not be countered") while
  still going to the graveyard itself. A genuinely sophisticated,
  correctly-sequenced multi-spell stack interaction, not scripted.
- `seed99`: Birthing Pod cast (paying 2 life for its Phyrexian pip),
  activated (pay {1}{G/P}, sacrifice Thrasios [mana value 3], search for
  and find Runic Armasaur [mana value 4], shuffle) - the search-restriction
  math is correct.
- The two `"illegal"` keyword hits (`seed6`, `seed94`) are both Gilded
  Drake's own printed reminder text ("This ability still resolves if its
  target becomes illegal") - not actual illegal actions.

**One real, systemic finding — `XMAGE_AI_POLICY_LIMITATION` (not a rules
defect, not fixed, per the owner's "do not fix bad strategic play by
modifying rules behavior" instruction):** Pact of Negation appeared in 6
games. In every one of the 5 that reached its deferred-cost upkeep trigger
("pay {3}{U}{U} or lose the game") within the turn window, **the AI did
not pay and lost** (`seed21`, `35`, `54`, `61`, `78`; `seed76`'s trigger
hadn't come due yet at the turn cap). The rules engine executed this
exactly correctly (Pact's actual printed text) - the AI simply never
banks/reserves the mana to pay a mandatory future cost it created for
itself. This is the entire explanation for all 5 detected wins in this
batch: **100% of "win" outcomes here are an artifact of one AI blind spot
around a single card's delayed cost, not gameplay quality** - concrete,
first-party evidence for why this phase's win data must not be read as
strategic signal. Logged as `INFRA-0007` (open, not blocking - see
`coverage_backlog/BACKLOG.md`).
