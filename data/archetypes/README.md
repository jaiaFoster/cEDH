# Archetype registry

Two registry versions, both pulled from EDHTop16 (`edhtop16.com/api/graphql`)
on 2026-08-12 via `sim/ingestion/edhtop16.py`, filtered to tournaments of
32+ players:

- `archetypes-2026-02-12_2026-08-12/` — primary 6-month window (SIX_MONTHS),
  150 commander-pairing records, 23,281 total tracked entries.
- `archetypes-2025-08-12_2026-08-12/` — secondary 12-month window (ONE_YEAR),
  150 commander-pairing records, for broader comparison per charter.

**Scope limit, stated explicitly:** these are commander-pairing-level
records, not Phase-8-clustered strategic archetypes. Every record's
`strategic_architecture` field says so. The same commander pairing can
support materially different game plans (or, per charter, shouldn't be
split over trivial flex-slot differences) — distinguishing that needs a
primer/recent-decklist read per pairing, not done yet. Treat this registry
as the empirical census (Phases 6-7: what's actually being played, and how
much) that Phase 8 clustering will refine, not as Phase 8's output.

The subject deck's own commander pairing (Thrasios, Triton Hero / Tymna the
Weaver) is in both windows — #6 by popularity in the 6-month window (763
entries, 3 first-place representative decklists pulled from real
tournaments), giving early real calibration data before any simulation
exists.

See `docs/assignments/SIM-001.md` "Phase 6" for the full write-up and
`data/schemas/archetype.schema.json` for the record shape.
