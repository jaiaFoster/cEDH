5 candidate interactions — the entire remaining population is the
mana-accounting-sensitive Tithe/Oboro group, pulled from Commander
Spellbook for the SIM-001 subject deck via `sim/ingestion/spellbook.py`:

- `INT-0001`, `INT-0004`, `INT-0005` (the three Faerie Mastermind +
  Smothering Tithe variants) share a notable reliability caveat: they
  require multiple opponents who don't pay Smothering Tithe's tax, an
  opponent decision, not something this deck controls — materially
  different reliability than the self-contained Devoted Druid lines.
- `INT-0003` — see `interactions/verified/` note: this exact combo
  (Hazel's Brewmaster + Devoted Druid, infinite green mana) has NOT yet
  itself been Level 4 validated, despite a later duplicate-discovery pass
  briefly re-finding the same pair independently (see `INT-0013`'s
  history in `coverage_backlog/BACKLOG.md`).
- `INT-0006` (Oboro Breezecaller + Talon Gates + Gaea's Cradle) has an
  unresolved creature-count-threshold detail.

Every "cheap," rules-only candidate this project has found is now
verified — the full Delney-doubling cluster (`INT-0007..0010`, `INT-0014`,
discovered via independent pairwise scan of Delney, Streetwise Lookout's
triggered-ability-doubling clause, plus the Kinnan hit `INT-0013`) and the
two "Derevi"/"Birthing Pod chain" priority-category finds (`INT-0011`,
`INT-0012`) have all cleared Level 4 validation and moved to
`interactions/verified/` — see that directory's README for the full
writeups, including the Delney cluster's cross-cutting modeling
requirement and `INT-0012`'s engine-harness methodology finding.

See `docs/assignments/SIM-001.md` "Phase 2" and "Phase 3" for the full
write-up of each remaining candidate. None are `status: verified` yet
(see `interactions/verified/` for the 9 that are); Phase 3 exact-line
validation is tracked as `coverage_backlog` `SIM-0007`, and several
records carry an explicit note that this agent's own hand-parsed mana
accounting should not be trusted over a real engine reproduction once one
exists (`INFRA-0003`).
