"""Layer 4 - Policies: given legal actions, what would this archetype choose?

Not implemented yet. Executable counterpart to the policy *definitions* in
data/policies/ (data/schemas/policy.schema.json). See
docs/POLICY_FRAMEWORK.md for the mechanism types (deterministic heuristic,
probabilistic heuristic, bounded forward search, agent-assisted review) and
the threat-assessment subsystem requirements.

Must stay strictly separate from sim/rules_engine/ - this module decides
what a competent pilot would do among the rules engine's legal actions; it
never determines legality itself (charter non-negotiable rule 3).

Blocked on: the archetype registry (Layer 3) and, for the subject deck's own
policy, the decklist.
"""
