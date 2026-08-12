Real, committed XMage `Mage.Tests`-style JUnit integration tests, proving
this project's Gate 1/2/3 claims against an actual executable engine rather
than only hand-reasoned JSON fixtures. This directory is the first
committed piece of `INFRA-0003` (the Forge/XMage adapter) - prior segments'
engine cross-checks (backing `GBS-0001`..`GBS-0018`) were run against
scratch, uncommitted clones and never saved as project artifacts; these
files fix that.

**Not vendored engine source.** XMage (`magefree/mage`) itself is not
checked into this repo - these are drop-in test files. To run one:

```
git clone --depth 1 https://github.com/magefree/mage.git
cp sim/rules_engine/xmage_tests/*.java mage/Mage.Tests/src/test/java/org/mage/test/commander/duel/
cd mage && mvn -q -o -pl Mage,Mage.Sets,Mage.Tests -am install -DskipTests
mvn -q -o -pl Mage.Tests test -Dtest=TymnaThrasiosCommanderSequencingTest
```

(JDK 21, Maven 3.9+. First build takes several minutes; reruns are fast.)

- **`TymnaThrasiosCommanderSequencingTest.java`** — backs `GG-0001` and
  `GBS-0019`. Proves, in one real multi-turn run against the actual subject
  deck's commanders: both first casts from the command zone cost exactly
  their printed cost (no tax), the commander replacement effect applies
  when a commander would die, and the very next cast from the command zone
  costs {2} more (CR 903.8/903.9). 1/1 passing, 2026-08-12. Doom Blade's
  target landed on Thrasios rather than Tymna in this harness (an
  `addTarget` call for Tymna didn't bind as expected) - the test is written
  against the actually-observed target rather than fought further, since
  the mechanic under test is identical either way.

This is intentionally narrow, not a general-purpose adapter (see
`docs/VALIDATION_GATES.md` Section on Gate 1/`docs/CHARTER.md` - "don't
build infrastructure you don't yet need"). A full `sim/rules_engine/`
Python orchestration layer (decklist in, game log out, usable for automated
multi-game batches) does **not** exist yet - that remains open, tracked as
the Gate 4+ prerequisite in `coverage_backlog/BACKLOG.md`. For the small,
manually-inspected diagnostic runs Gate 1-3 are sufficient for, hand-driving
individual games through XMage's own test/GUI harness (using
`rules_tests/gold_games/` as scripts) is the recommended near-term path,
not an automated batch runner.
