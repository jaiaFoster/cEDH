7 candidate interactions:

- `INT-0001`, `INT-0003` .. `INT-0006` — pulled from Commander Spellbook
  for the SIM-001 subject deck via `sim/ingestion/spellbook.py`.
  `INT-0001`, `INT-0004`, `INT-0005` (the three Faerie Mastermind +
  Smothering Tithe variants) share a notable reliability caveat: they
  require multiple opponents who don't pay Smothering Tithe's tax, an
  opponent decision, not something this deck controls — materially
  different reliability than the self-contained Devoted Druid lines.
  `INT-0006` (Oboro Breezecaller + Talon Gates + Gaea's Cradle) has an
  unresolved creature-count-threshold detail.
- `INT-0011`, `INT-0012` — found by independent manual review targeting
  the charter's named "Derevi" and "Birthing Pod chain" priority
  categories (Derevi + Gaea's Cradle bonus activations; Clever Impersonator
  copying Birthing Pod for a second chain).

All 5 candidates originally found by the independent pairwise scan of
Delney, Streetwise Lookout's triggered-ability-doubling clause
(`INT-0007..0010`, plus `INT-0014` found on a later, more exhaustive
re-scan that also caught the Kinnan hit now `interactions/verified/
INT-0013.json`) have since cleared Level 4 validation and moved to
`interactions/verified/` — see that directory's README for the full
Delney-doubling cluster writeup and its cross-cutting modeling
requirement.

See `docs/assignments/SIM-001.md` "Phase 2" and "Phase 3" for the full
write-up of each remaining candidate. None are `status: verified` yet
(see `interactions/verified/` for the 7 that are); Phase 3 exact-line
validation is tracked as `coverage_backlog` `SIM-0007`, and several
records carry an explicit note that this agent's own hand-parsed mana
accounting should not be trusted over a real engine reproduction once one
exists (`INFRA-0003`).
