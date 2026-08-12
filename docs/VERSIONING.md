# Versioning & provenance conventions

Every result must be traceable: `deck version → model version → dataset →
simulation configuration → raw result` (charter, "Output provenance"). This
document defines the concrete IDs and file conventions that make that true
mechanically, not just as a principle.

## Identifiers

| ID | Format | Set by | Lives in |
|---|---|---|---|
| Deck version | `<deckname>-v<N>` e.g. `tymna-thrasios-treefarm-v1` | Bumped whenever the subject or an opponent decklist changes by even one card | `data/decklists/<deck-version>.json` |
| Rules-data version | `oracle-<YYYY-MM-DD>` | Date the Scryfall/MTGJSON pull was made | `data/cards_cache/<oracle-version>/` |
| Interaction-set version | `interactions-v<N>` | Bumped when `interactions/verified/` changes | recorded in the interaction files' own `verified_date` + this repo's git history |
| Archetype-registry version | `archetypes-<tournament-window>` e.g. `archetypes-2026H1` | The tournament date window the census was built from | `data/archetypes/<version>/` |
| Policy version | `<archetype-id>-policy-v<N>` | Bumped when policy logic or its evidence sources change | `data/policies/<archetype-id>/v<N>.json` |
| Simulator version | `sim-v<N>` (also the git commit SHA at run time) | Bumped on any change to `sim/` that could affect output | recorded in every run's config |
| Tournament-data window | `topdeck+edhtop16-<start>-<end>` | The actual date range pulled | `data/tournament_snapshots/<window>/` |
| Run ID | `run-<YYYYMMDD>-<slug>-<seed>` | One per simulation invocation | `results/raw/<run-id>/` |

## What every run must record

A run is not valid evidence without a config file at
`results/raw/<run-id>/config.json` containing, at minimum (see
`data/schemas/simulation_result.schema.json` for the enforced shape):

- `simulator_version` (git SHA)
- `rules_awareness_level` (0-4, per charter)
- `subject_deck_version`
- `opponent_deck_versions` (list, one per seat)
- `archetype_registry_version`
- `policy_versions` (one per archetype instantiated in the run)
- `tournament_data_window` (if pod sampling used empirical distributions)
- `random_seed(s)`
- `game_count`
- `known_coverage_gaps` — explicit pointer to the relevant
  `coverage_backlog/` entries open at run time, so a reader can see what the
  result does *not* account for without cross-referencing separately.

## Distinguishing evidence types

Every artifact under `results/` and every Findings Packet must carry an
explicit `evidence_type` field, one of: `simulation`, `goldfish`,
`static_probability`, `practice_game`, `tournament_game`. These are never
merged or presented as interchangeable (charter, "Simulation is not
tournament data"). A comparison across evidence types is allowed and often
useful (e.g. "does simulation agree with tournament calibration data?") but
must show both types labeled, not blended into one number.

## Confidence dimensions

Per charter ("Confidence reporting"), report — using qualitative labels
(`low` / `moderate` / `high`, plus a one-line reason) wherever numeric
precision would be false — the following, wherever a result is presented
outside raw internal logs:

- **Sampling confidence** — Monte Carlo noise given `game_count` and effect
  size.
- **Rules confidence** — how completely the relevant mechanics are modeled
  at the `rules_awareness_level` used.
- **Policy confidence** — how well the archetype policy is believed to
  resemble competent play (tie back to its evidence sources in
  `data/policies/`).
- **List confidence** — how representative the modeled opponent decklist(s)
  are of what's actually played.
- **Metagame confidence** — strength of the underlying tournament sample
  behind any pod-distribution weighting used.
- **Sensitivity** — does the conclusion survive reasonable perturbation of
  uncertain assumptions (ablation / matched-comparison results, if run)?

## File-naming and immutability rules

- Nothing under `results/raw/<run-id>/` is edited after the run completes —
  a correction is a new run, not a mutation, so old citations stay valid.
- `data/decklists/`, `data/policies/`, `interactions/verified/` are
  append/version, not overwrite: a changed card list gets a new
  `<deckname>-v<N+1>.json` file; the old version stays for reproducibility of
  anything that cited it.
- `coverage_backlog/BACKLOG.md` entries are never deleted, only marked
  resolved with a pointer to the regression test or fix that closed them
  (see `coverage_backlog/README.md`).

## Findings Packets

`results/findings_packets/<slug>.md` files must include, per charter format,
a **Provenance** block listing evidence type, sample size, `simulator_version`
(or "N/A — static probability" etc.), and `subject_deck_version`. A Findings
Packet with no provenance block is not publishable per this project's
standard, regardless of how clean the underlying chart looks.
