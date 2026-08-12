# Coverage backlog

The mechanism required by charter section "Interaction coverage backlog":
log every state during ingestion/validation/simulation where legality is
uncertain, a card behavior is unsupported, an interaction is unencoded, a
tutor target's downstream value is unknown, the model can't determine
whether a line wins, policy can't rank meaningful legal actions, or an
unexpected rules interaction occurs.

Workflow: **simulate → discover coverage gaps → research → validate →
encode → regression test → simulate again.**

## Files

- `BACKLOG.md` — human-readable, ranked list. This is the source of truth
  for "what's currently unresolved."
- `backlog.jsonl` — one JSON object per line, machine-readable mirror of the
  same entries, conforming to `data/schemas/coverage_backlog_entry.schema.json`.
  Any tooling that scans for open high-impact gaps (e.g. a Gate 6 exit-check
  script) reads this file, not the markdown.

Every entry needs both a markdown row and a jsonl line — keep them in sync
by hand until/unless a generator script is written; do not let one drift
ahead of the other.

## Entry lifecycle

1. **Opened** — discovered during any layer's work. Gets an ID
   (`<AREA>-<NNNN>`, area is a short tag like `RULES`, `INTERACT`, `POLICY`,
   `ENV`, `INFRA`, `SIM`), a one-line summary, an impact note (what can't be
   answered while this is open), and a frequency note once observed during
   simulation (how often this state was hit, if known).
2. **Researched** — evidence gathered per the source hierarchy
   (`docs/SOURCES.md`); notes added, ID stays open.
3. **Validated** — legality/behavior confirmed (rules text + ideally an
   executable engine, per Tier 2). Recorded as validated with citations.
4. **Encoded** — implemented in the relevant layer (`sim/rules_engine/`,
   `sim/interactions/`, `sim/policies/`, etc.) and, if it moves an
   interaction from candidate to verified, the file moves from
   `interactions/candidate/` to `interactions/verified/`.
5. **Regression-tested** — a permanent test added under
   `rules_tests/regression/` so this is never silently relearned.
6. **Closed** — marked resolved in both `BACKLOG.md` and `backlog.jsonl`
   with a pointer to the regression test and/or the encoding commit. Entries
   are never deleted, only marked resolved, so history of what the model
   used to not know is preserved.

## Ranking

Rank open entries by **frequency × impact** — how often the gap is actually
hit during real ingestion/simulation, times how much it blocks (a gap that's
hit constantly but doesn't change any conclusion is lower priority than a
rare gap that would flip a headline finding). Frequency is often unknown
until Gate 4-6 simulation runs actually hit the state; entries opened before
any simulation exists (like the ones currently in this backlog) are ranked
by estimated impact only, and re-ranked once real hit-frequency data exists.
