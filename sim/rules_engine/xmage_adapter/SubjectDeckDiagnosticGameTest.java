package org.mage.test.commander.duel;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.util.RandomUtil;
import org.apache.log4j.Logger;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer7;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * Real deck-backed diagnostic game driver (INFRA-0004 / diagnostic gameplay
 * phase, GATE_4A_2P_DIAGNOSTIC). Uses ComputerPlayer7 (mage.player.ai,
 * skill configurable via -Ddiag.skill) wrapped by TestComputerPlayer7 for
 * genuine simulation-based AI play across full turns - NOT the plain
 * ComputerPlayer used elsewhere in this project's scripted interaction
 * tests, whose priority() is a bare "pass" stub with no real decision
 * logic (see sim/rules_engine/xmage_adapter/README.md's "known-defect log"
 * for how that was discovered).
 *
 * Runs a BATCH of games in a single JVM (one per entry in -Ddiag.seeds, a
 * comma-separated list) to avoid ~100x Maven/JVM startup overhead for the
 * ~100-game GATE_4A_2P_DIAGNOSTIC batch. Each game gets a fresh reset()
 * (JUnit's own @Before hook, called here a second+ time per batch entry -
 * it fully reinitializes currentGame/players/command queues, see its own
 * source). Per-game output is delimited on stdout so the Python
 * orchestrator (run_diagnostic_game.py) can split one combined log into
 * per-game transcripts.
 */
public class SubjectDeckDiagnosticGameTest extends CardTestPlayerAPIImpl {

    // Markers must go through the same log4j file appender as
    // PrintGameLogsDataCollector's [LOG][GAME] lines (magetest.log), not
    // System.out - System.out is captured separately (in Surefire's
    // per-test XML report) and can't be reliably interleaved with the
    // file-appender stream by timestamp/order alone.
    private static final Logger DIAG_LOGGER = Logger.getLogger("diag.batch.markers");

    @Override
    protected TestPlayer createPlayer(String name, RangeOfInfluence rangeOfInfluence) {
        int skill = Integer.parseInt(System.getProperty("diag.skill", "6"));
        TestPlayer testPlayer = new TestPlayer(new TestComputerPlayer7(name, rangeOfInfluence, skill));
        testPlayer.setAIPlayer(true); // full autoplay, not one-off AI-assist commands
        return testPlayer;
    }

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        // Real Commander life total (CR 903.7: 40, any pod size) - the
        // reusable CardTestCommander4Players base in this engine defaults
        // to 20, which is wrong for genuine Commander diagnostics, so this
        // class builds its own game instead of extending that base.
        Game game = new CommanderFreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL, MulliganType.GAME_DEFAULT.getMulligan(0), 40, 7);
        String deckFile = System.getProperty("diag.deck", "TymnaThrasiosTreefarm.dck");
        int seats = Integer.parseInt(System.getProperty("diag.seats", "2"));
        playerA = createPlayer(game, "PlayerA", deckFile);
        playerB = createPlayer(game, "PlayerB", deckFile);
        if (seats >= 3) {
            playerC = createPlayer(game, "PlayerC", deckFile);
        }
        if (seats >= 4) {
            playerD = createPlayer(game, "PlayerD", deckFile);
        }
        return game;
    }

    @Test
    public void runDiagnosticBatch() throws Exception {
        String seedsProp = System.getProperty("diag.seeds", System.getProperty("diag.seed", "1"));
        int maxTurn = Integer.parseInt(System.getProperty("diag.maxTurn", "6"));
        for (String seedStr : seedsProp.split(",")) {
            long seed = Long.parseLong(seedStr.trim());
            DIAG_LOGGER.info("===DIAG_GAME_START seed=" + seed + "===");
            long startNanos = System.nanoTime();
            try {
                // Must seed before reset()'s deck load/shuffle, same
                // ordering bug/fix as the single-game driver's
                // @BeforeClass (see results/diagnostic/README.md finding
                // #1) - here reset() is called per-iteration, not once,
                // so the seed call just needs to precede each one.
                RandomUtil.setSeed(seed);
                reset();
                setStopAt(maxTurn, PhaseStep.END_TURN);
                execute();
                long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
                DIAG_LOGGER.info("===DIAG_GAME_END seed=" + seed + " status=OK elapsedMs=" + elapsedMs + "===");
            } catch (Throwable t) {
                long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
                DIAG_LOGGER.info("===DIAG_GAME_END seed=" + seed + " status=EXCEPTION elapsedMs=" + elapsedMs
                        + " exceptionClass=" + t.getClass().getName()
                        + " exceptionMsg=" + String.valueOf(t.getMessage()).replace("\n", " ") + "===");
            }
        }
    }
}
