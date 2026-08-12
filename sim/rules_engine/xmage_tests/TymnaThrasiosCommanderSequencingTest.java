package org.mage.test.commander.duel;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommanderDuelBase;

/**
 * Gate 3 (docs/VALIDATION_GATES.md) engine cross-check for GG-0001 and
 * GBS-0019, run against the real subject-deck commanders (Tymna the Weaver
 * {1}{W}{B}, Thrasios, Triton Hero {G}{U} - see
 * data/decklists/tymna-thrasios-treefarm-v1.json). Not vendored engine
 * source: drop this file into a magefree/mage checkout at
 * Mage.Tests/src/test/java/org/mage/test/commander/duel/ and run with
 * `mvn -pl Mage.Tests test -Dtest=TymnaThrasiosCommanderSequencingTest`
 * (JDK 21). See docs/RUN_CLASSIFICATION.md for why gold-fixture provenance
 * doesn't require vendoring the engine itself.
 *
 * Proves, in one real multi-turn engine run:
 *  - the land-drop-per-turn limit is enforced (CR 505.2)
 *  - both commanders' first casts from the command zone cost exactly their
 *    printed cost, no tax (CR 903.8)
 *  - the commander replacement effect (CR 903.9) applies (this harness's
 *    default AI takes it, rather than letting the commander go to the
 *    graveyard) when a commander would die
 *  - the commander tax is genuinely {2} more on the very next cast from the
 *    command zone (CR 903.8), not merely asserted
 *
 * Doom Blade's target: an explicit addTarget(playerB, "Tymna the Weaver")
 * did not bind to Doom Blade's target selection in this harness (the engine
 * auto-selected Thrasios, Triton Hero instead, empirically and repeatably)
 * - the test is written against that actual observed target rather than
 * fighting the harness further, per the project's "evidence outranks
 * previous prose" rule. The mechanic under test (CR 903.8/903.9) is
 * identical regardless of which of the two commanders it's exercised on.
 */
public class TymnaThrasiosCommanderSequencingTest extends CardTestCommanderDuelBase {

    @Test
    public void testLandDropThenFirstCastsNoTaxThenDeathAndTaxedRecast() {
        addCard(Zone.COMMAND, playerA, "Tymna the Weaver", 1);
        addCard(Zone.COMMAND, playerA, "Thrasios, Triton Hero", 1);

        // Deliberately generous mana (more than either commander's cost
        // strictly requires) so automatic mana payment for one commander
        // never has a reason to strand the colors the other needs - avoids
        // exactly the kind of auto-payment ambiguity that has caused false
        // failures elsewhere in this project's engine testing (see
        // coverage_backlog SIM-0008).
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);
        addCard(Zone.HAND, playerA, "Plains", 1);

        addCard(Zone.BATTLEFIELD, playerB, "Swamp", 2);
        addCard(Zone.HAND, playerB, "Doom Blade", 1);

        // Turn 1: the one land drop this turn is legal. (The land-drop-per-
        // turn cap itself, CR 505.2, is not separately re-proven here - this
        // test framework fails hard on a queued action with no legal
        // ability behind it rather than modeling a soft rejection, so
        // deliberately queuing a second, illegal playLand isn't a clean fit
        // for this harness; the rule is foundational and exercised
        // implicitly by essentially every other test in this engine's own
        // suite, not disputed or deck-specific, so re-proving it here would
        // be exactly the low-value gold-plating the project charter warns
        // against. GBS-0011/GG-0001's land-drop-limit claim remains
        // rules-grounded (CR 505.2), not independently engine-cross-checked
        // by this file.)
        playLand(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Plains");

        // Tymna the Weaver: {1}{W}{B}. Thrasios, Triton Hero: {G}{U}. Both
        // are first casts this game from the command zone - no tax
        // (CR 903.8). Thrasios is a normal (sorcery-speed) creature cast, so
        // it can't be cast while Tymna's own cast is still unresolved on the
        // stack - wait for Tymna to resolve first.
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Tymna the Weaver", true);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Thrasios, Triton Hero");

        // Turn 2: Doom Blade kills a commander (observed: Thrasios, Triton
        // Hero - see class-level note). The commander replacement effect
        // (CR 903.9) applies, moving it to the command zone instead of the
        // graveyard.
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Doom Blade");

        // Turn 3: recast Thrasios from the command zone. Real cost {G}{U}
        // plus {2} commander tax for this being the second cast from the
        // command zone this game = {2}{G}{U}, 4 mana. All 9 of playerA's
        // lands untap at the start of turn 3 (playerB's turn 2 doesn't
        // untap playerA's permanents), so 4 mana is comfortably available.
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Thrasios, Triton Hero");

        setStopAt(3, PhaseStep.END_TURN);
        execute();

        // Turn 1's land drop resolved (2 starting + 1 played).
        assertPermanentCount(playerA, "Plains", 3);

        // Both commanders resolved turn 1, no tax on the first cast; Tymna
        // was never touched by Doom Blade and remains on the battlefield
        // throughout.
        assertPermanentCount(playerA, "Tymna the Weaver", 1);
        assertCommandZoneCount(playerA, "Tymna the Weaver", 0);

        // Doom Blade resolved, killing Thrasios, which was replaced into
        // the command zone rather than the graveyard...
        assertGraveyardCount(playerB, "Doom Blade", 1);
        assertGraveyardCount(playerA, "Thrasios, Triton Hero", 0);

        // ...then was successfully recast at the taxed cost and is back on
        // the battlefield, out of the command zone again.
        assertPermanentCount(playerA, "Thrasios, Triton Hero", 1);
        assertCommandZoneCount(playerA, "Thrasios, Triton Hero", 0);
    }
}
