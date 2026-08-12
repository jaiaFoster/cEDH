"""Layer 1 - Rules: what is legal?

Not implemented yet. Planned responsibilities (see docs/ARCHITECTURE.md):
  - Adapter(s) to an executable engine (Forge and/or XMage, see
    docs/SOURCES.md Tier 2 and coverage_backlog/BACKLOG.md INFRA-0002) for
    Level 4 exact-line validation and Gate 2/3 gold-state/gold-game checks.
  - A native Level 1-2 structural/sequencing state tracker for Level 3
    four-player Monte Carlo simulation, cross-checked against the executable
    engine per Gate 2 before being trusted.

This layer must never encode strategy - it answers "is this legal", never
"is this good" (charter non-negotiable rule 3). Strategy lives in
sim/policies/.

Blocked on: subject decklist (coverage_backlog DECK-0001), network access to
Forge/XMage repos and card data (coverage_backlog ENV-0001), and the
Forge/XMage/native decision (coverage_backlog INFRA-0002).
"""
