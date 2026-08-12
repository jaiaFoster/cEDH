"""Layer 1 - Rules: what is legal?

No Python orchestration adapter (decklist in, game log out) exists yet -
that remains open (Gate 4+ prerequisite, see coverage_backlog/BACKLOG.md).
What does exist, in xmage_tests/: real, committed XMage Mage.Tests-style
JUnit integration tests backing this project's Gate 1-3 claims against an
actual executable engine (not just hand-reasoned JSON fixtures) - see
xmage_tests/README.md for how to run them and what they currently cover.

Planned responsibilities (see docs/ARCHITECTURE.md) beyond what's built:
  - A general adapter to an executable engine (Forge and/or XMage, see
    docs/SOURCES.md Tier 2 and coverage_backlog/BACKLOG.md INFRA-0002) for
    Level 4 exact-line validation and Gate 2/3 gold-state/gold-game checks
    at automated-batch scale, not just individually hand-authored tests.
  - A native Level 1-2 structural/sequencing state tracker for Level 3
    four-player Monte Carlo simulation, cross-checked against the executable
    engine per Gate 2 before being trusted.

This layer must never encode strategy - it answers "is this legal", never
"is this good" (charter non-negotiable rule 3). Strategy lives in
sim/policies/.
"""
