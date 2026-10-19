# Additive scoring methods compared
All construction models must have one globally fixed integer price per Oracle ID. Deck/commander/team interactions stay outside the sum.

| Model | Executed implementation | Fit to philosophy | Main limitation |
|---|---|---|---|
| A baseline | Original v0.2 values, unchanged | Fixed, deterministic | Failed small external comparisons; subjective text heuristics |
| B published ratings | zarzak cache, canonicalized to Oracle IDs | Strong structural fit; source 0–100 integers | LLM judgments, missing cards, inconsistent basics, no outcome calibration |
| C sparse consensus control | One vote each for Canlander pointed and Game Changer flags | Fixed additive, auditable | Sparse and correlated judgments; not a complete strength estimate |
| D additive approximation | Ridge emulation of permitted B card-score sums, chronological holdout | Tests inference machinery | Not independent strength validation; huge null space and poor recovery |
| E hybrid diagnostic | B with a fixed 30 for rated basic lands | Fixed and global; explicit structural assumption | Does not fix other rating errors; not selected by fitting opinions |
| Open-source alternative | XMage card-component adapter | Fixed after removing commander-zone bonus | Another text heuristic with stale lists and renderer mismatch |
| Other controls | Canlander points and Game Changer counts | Real expert policy indicators | Most precons tie; zero is policy, not evidence of harmlessness |
| Partial diagnostics | Published creature CSV, log adoption rank | Useful error/coverage probes | No fully covered decks; cannot serve as complete prices |

B and E are separate experimental candidates, not replacements written into the baseline database. Raw cached judgments require no paid calls for ordinary calculations. We made no paid calls to fill missing cards.

## External algorithm inspection
XMage takes category maxima across 57 flags, applies planeswalker/name-list floors and credits listed combo pieces. We apply the same card component to commanders and main-deck cards; contextual command-zone bonuses are omitted. This is not exact Java rules rendering or a native XMage service score.

The published LLM scorer has explicit anchored bands, independent-power instructions and a cached model/text version. It provides an external prior with transparent instructions but hidden model weights and no recorded per-card rationale. Determinism means frozen cache determinism; temperature zero alone does not guarantee regeneration.

EDHPowerLevel exposes impacts but full permitted data/implementation were not acquired. CommanderSalt's current internals were not acquired. No undocumented service endpoints, inferred private APIs or third-party scores were used as training labels.

## Recovering prices from deck scores
Let X be deck-by-card counts. Here X is 174 by 6,429, rank 174: at least 6,255 coefficient directions cannot be identified. 4,382 cards occur in one deck. Identical inclusion patterns group 4,766 cards into 317 groups with multiple cards. Cards in the same group cannot have separate effects estimated from these deck totals alone. Constant 100-card row sums also confound a global card-price offset with an intercept.

- NNLS prevents negative prices but does not remove the null space or make sparse cards identifiable. A corner solution can arbitrarily allocate shared credit. It was researched, not executed here.
- Ridge selects a solution near a prior. The executed zero-prior diagnostic shows why the chosen prior matters; it can still produce negative coefficients and poor future-deck predictions.
- Elastic net can select a few representatives from correlated groups. That sparsity is not proof the excluded cards have no independent power. Not executed.
- Hierarchical/Bayesian shrinkage can share information by verified role/mana/category, preserve nonnegativity and report uncertainty, but hierarchy and priors remain assumptions. Not executed; no posterior evidence is claimed.
- A strong reusable card-level prior makes inversion largely unnecessary. If permitted holistic service scores later become available, fit only a small number of calibration dimensions or shrink deviations from that prior rather than estimating thousands of free prices.

Our ridge diagnostic uses the already additive, permitted cache sums as labels, not scraped evaluator scores. It trains on complete decks through 2023 and tests complete 2024–2026 decks. It tests emulation/generalization, not competitive deck-strength prediction. Negative coefficients make those outputs unsuitable league prices; none is installed.

## Ensembles and leakage
The sparse expert vote control is not a validated consensus model. We do not average price, adoption, GC, salt and combo degree indiscriminately: they overlap, measure different concepts and have incompatible scales. No ensemble weight was fitted on the small opinion sets. The basic-land control is a stated equality assumption, not an optimized parameter.

The expanded evaluation freezes five within-year best/worst pairs from Josh Nelson's 2025 articles. It is not a total ordering. The older EDHREC and Reddit samples remain separate. Public reviews could have been seen during an LLM's training; external publication is not proof of training-set independence.

## Structural ceiling of additive scoring
If two decks have the same card counts, any additive model assigns the same score. Nonlinear interactions, commander access, mana consistency, pilot decisions and opposing pods can differ in a holistic evaluation. We cannot estimate a numerical agreement ceiling without appropriate matched decks/outcomes, but the structural limitation follows directly from the model.

The league explicitly accepts this gap to reward construction and team coordination. A legality analyzer can restrict unacceptable combinations without adding hidden synergy charges to prices. Banned-card review remains separate, and a high numerical price never silently changes legality.
