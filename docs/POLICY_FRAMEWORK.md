# Policy framework

Operationalizes the charter's "Decision policy" and "Threat assessment"
sections. A **policy** answers "given the legal actions the rules layer
returns, what would a competent pilot of this archetype plausibly do?" — a
distinct system from the rules layer, per the charter's non-negotiable rule
2 ("separate legality from decision-making").

## Policy record shape

Every archetype gets a policy record at `data/policies/<archetype-id>/v<N>.json`
(schema: `data/schemas/policy.schema.json`) containing:

- `archetype_id` — matches `data/archetypes/`.
- `evidence_sources` — cited primers, tournament reports, gameplay footage,
  with URLs/dates. A policy with no evidence sources is a guess, not a
  policy, and must be labeled `provisional` until sourced.
- `mechanism` — one of `deterministic_heuristic`, `probabilistic_heuristic`,
  `bounded_forward_search`, `agent_assisted_review`, per decision point (a
  single archetype's policy will mix mechanisms across different decision
  types — see below).
- `decision_points` — a list of the distinct decision types this policy
  covers (mulligan, tutor target selection, counterspell target selection,
  win-attempt timing, protection usage, threat assessment, development vs.
  interaction tradeoff, etc.), each with its own mechanism and rationale.
- `assumptions` — explicit list of anything asserted without direct evidence
  (e.g. "assumes pilot mulligans to 5 for a guaranteed T1 dork" without a
  cited source), so sensitivity analysis has a concrete list to perturb.

## Mechanism selection guide

| Mechanism | Use for | Cost |
|---|---|---|
| Deterministic heuristic | Obvious decisions with near-universal agreement (e.g. "always play a land if one is available and mana is needed") | Cheapest, most reproducible |
| Probabilistic heuristic | Decisions where competent pilots reasonably vary (e.g. mulligan aggression on a 2-lander) | Cheap; needs a defensible probability, not an invented one |
| Bounded forward search | Local tactical decisions among a small set of competing lines (e.g. which of 2-3 available tutor targets this turn) | More expensive; bound search depth/branching explicitly and record the bound |
| Agent-assisted review | Ambiguous or high-value positions, and policy *validation* (spot-checking whether a heuristic's output looks like something a real pilot would do) | Most expensive — never run per-decision across millions of games; used to build/validate the cheaper mechanisms, not to replace them at scale |

Per charter: do not use expensive general reasoning for every priority
decision in millions of simulations unless demonstrably necessary. The
default posture is deterministic/probabilistic heuristics informed by
agent-assisted review done *once*, at policy-authoring time, not per-game.

## Threat assessment (a specific, high-risk decision point)

Multiplayer threat assessment is the one decision point the charter
specifically warns against oversimplifying into "counter the strongest
spell." A threat-assessment policy must reason about, at minimum:

- probability the action actually wins the game;
- whether another player can respond instead of us;
- what interaction we have available, and who else at the table has
  interaction available (interaction ownership);
- who is the current resource leader;
- future threat, not just the immediate spell;
- seat order relative to the threat and relative to us;
- whether spending our interaction now exposes us to a different player;
- whether passing priority itself leaks information (e.g. signals we have
  no answer, or signals we're saving one).

This subsystem is explicitly expected to be imperfect. It must be a named,
separately-versioned component (not inlined ad hoc per archetype) so that
sensitivity analysis can vary it independently of other policy assumptions —
i.e. "how much does the matchup number change if our threat-assessment model
is wrong about interaction ownership" is a question we need to be able to
ask directly.

## Per-archetype differentiation

Per charter: "A RogSi policy should not behave like Kinnan. A Kinnan policy
should not behave like Blue Farm. A Sisay policy should not behave like
Tymna/Thrasios." Concretely, this means:

- No shared default policy that archetypes merely parameterize with
  different numbers — each archetype's `decision_points` list should reflect
  what actually matters for *that* archetype (e.g. a turbo-combo archetype's
  policy needs a sharp win-attempt-timing decision point; a stax archetype's
  policy needs a resource-denial-sequencing decision point that a turbo deck
  might not need at all).
- Shared *mechanisms* (the four types above) are fine and expected to be
  reused across archetypes; shared *heuristic content* is a smell unless
  justified (e.g. "always keep a hand with a T1 play" might genuinely apply
  broadly, but should still be independently cited per archetype rather than
  assumed to transfer).

## Status

No policies exist yet — blocked on the archetype registry (`data/archetypes/`,
itself blocked on tournament-data access) and on the subject deck's own
policy, which needs the decklist. This document defines the framework new
policies must conform to once those inputs arrive.
