10 candidate interactions:

- `INT-0001` .. `INT-0006` — pulled from Commander Spellbook for the
  SIM-001 subject deck via `sim/ingestion/spellbook.py`. `INT-0001`,
  `INT-0004`, `INT-0005` (the three Faerie Mastermind + Smothering Tithe
  variants) share a notable reliability caveat: they require multiple
  opponents who don't pay Smothering Tithe's tax, an opponent decision, not
  something this deck controls — materially different reliability than the
  self-contained Devoted Druid lines.
- `INT-0007` .. `INT-0010` — found by an independent pairwise scan (not
  from Spellbook's index) of Delney, Streetwise Lookout's triggered-ability-
  doubling clause against every power-≤2 creature's own trigger, done by
  grepping the ingested Oracle text for keyword buckets and manually
  reasoning through the hits — per charter Phase 2, Spellbook is a seed, not
  the complete graph.

See `docs/assignments/SIM-001.md` "Phase 2" and "Phase 3" for the full
write-up of each. None are `status: verified` yet; Phase 3 exact-line
validation is tracked as `coverage_backlog` `SIM-0007`, and several records
carry an explicit note that this agent's own hand-parsed mana accounting
should not be trusted over a real engine reproduction once one exists
(`INFRA-0003`).
