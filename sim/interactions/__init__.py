"""Layer 2 - Interactions: what deterministic transitions exist?

Not implemented yet. Planned responsibility: load interactions/verified/*.json
(data/schemas/interaction.schema.json) and expose them to sim/simulation/ as
deterministic transitions. Must never load from interactions/candidate/ for
that purpose - candidates are unverified by definition (charter
non-negotiable rule 1).

Blocked on: subject decklist and the interaction discovery pass
(coverage_backlog DECK-0001).
"""
