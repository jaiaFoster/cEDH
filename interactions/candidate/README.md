13 candidate interactions:

- `INT-0001` .. `INT-0006` — pulled from Commander Spellbook for the
  SIM-001 subject deck via `sim/ingestion/spellbook.py`. `INT-0001`,
  `INT-0004`, `INT-0005` (the three Faerie Mastermind + Smothering Tithe
  variants) share a notable reliability caveat: they require multiple
  opponents who don't pay Smothering Tithe's tax, an opponent decision, not
  something this deck controls — materially different reliability than the
  self-contained Devoted Druid lines.
- `INT-0007` .. `INT-0010`, `INT-0013`, `INT-0014` — found by an
  independent pairwise scan (not from Spellbook's index) of Delney,
  Streetwise Lookout's triggered-ability-doubling clause against every
  power-≤2 creature's own trigger. The first pass (`INT-0007..0010`)
  missed two real hits — Kinnan, Bonder Prodigy's own mana-doubling
  trigger (`INT-0013`, notable: this doubles Kinnan's trigger a second
  time, tripling mana from nonland sources rather than merely doubling
  it) and Archivist of Oghma (`INT-0014`) — found on a later, more
  exhaustive re-scan. Kept as an explicit lesson: an early "independent
  scan" claiming completeness should still be treated as provisional
  until re-checked, the same discipline the project already applies to
  Commander Spellbook's own index.
- `INT-0011`, `INT-0012` — found by independent manual review targeting
  the charter's named "Derevi" and "Birthing Pod chain" priority
  categories (Derevi + Gaea's Cradle bonus activations; Clever Impersonator
  copying Birthing Pod for a second chain).

See `docs/assignments/SIM-001.md` "Phase 2" and "Phase 3" for the full
write-up of each. None are `status: verified` yet; Phase 3 exact-line
validation is tracked as `coverage_backlog` `SIM-0007`, and several records
carry an explicit note that this agent's own hand-parsed mana accounting
should not be trusted over a real engine reproduction once one exists
(`INFRA-0003`).
