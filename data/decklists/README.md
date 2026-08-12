# Decklists

The subject decklist for SIM-001 has been supplied (Tymna the Weaver /
Thrasios, Triton Hero, 98 main-deck cards) — see
`docs/assignments/SIM-001.md` for the full Phase 0 writeup.

It currently lives only as a **provisional** artifact:
`_provisional/tymna-thrasios-treefarm-v1.json`. That file deliberately does
not conform to `data/schemas/decklist.schema.json` (it has no real
`scryfall_id` per card, since bulk Scryfall access is blocked — see
`coverage_backlog/BACKLOG.md` `ENV-0001`). It's a name + WebSearch-spot-check
record, useful for legality/color-identity triage and for scoping the rest
of SIM-001, not the Level 1 "every characteristic retained" ingestion the
charter requires before rules modeling starts.

This top-level directory (matched by the regression suite's schema check)
stays empty until the real, schema-conformant
`tymna-thrasios-treefarm-v1.json` can be built — i.e. until every card is
resolved to a real Scryfall ID, either via a fixed network policy or an
out-of-band Scryfall bulk-data drop. At that point the provisional file is
superseded, not edited in place (per `docs/VERSIONING.md`'s immutability
rule) — the real file lands here directly.
