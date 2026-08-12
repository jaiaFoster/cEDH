package org.mage.test.commander.duel;

import mage.cards.Card;
import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.game.permanent.Permanent;
import mage.util.RandomUtil;
import org.apache.log4j.Logger;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestComputerPlayer7;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * SIM-001 SOLO BASELINE v1 - ENGINE-GOLDFISH layer (results/solo_baseline/).
 * Real XMage-executed, exact-frozen-deck solo sequencing: PlayerA is the
 * subject deck piloted by the real AI (ComputerPlayer7); PlayerB is a
 * deliberately inert opponent - the plain do-nothing ComputerPlayer (see
 * sim/rules_engine/xmage_adapter/README.md's "known-defect log": its
 * priority() is a bare pass() stub, which is exactly a goldfish-mode
 * opponent, not a bug here) - so PlayerA's development is unaffected by
 * any opposing disruption, matching docs/RUN_CLASSIFICATION.md's
 * DECK_BACKED_GOLDFISH definition.
 *
 * After each run, snapshots PlayerA's exact hand/battlefield/graveyard
 * CONTENTS (card names) via the log - not whether the AI "recognized" or
 * assembled any particular line. Accessibility analysis (Python side)
 * checks for named combo pieces directly against these snapshots, per the
 * owner's explicit "evaluate accessibility from game state rather than
 * requiring the AI to recognize the line" instruction.
 */
public class SoloGoldfishSnapshotTest extends CardTestPlayerAPIImpl {

    private static final Logger DIAG_LOGGER = Logger.getLogger("solo.baseline.markers");

    /**
     * See SubjectDeckDiagnosticGameTest's identical method for the full
     * explanation: the inherited execute() hardcodes
     * gameOptions.testMode = true, which skips real hand-dealing entirely
     * (GameImpl.init() only calls mulligan.drawHand() when
     * !gameOptions.testMode). Every solo-baseline snapshot before this fix
     * was taken from a genuinely empty-then-barely-refilled hand, not a
     * real opening 7 - a severe ADAPTER_DEFECT found and fixed while
     * building this project's SIM-001 SOLO BASELINE v1.
     */
    protected void executeWithRealHands() {
        mage.util.ThreadUtils.ensureRunInGameThread();
        mage.collectors.DataCollectorServices.init(true, mage.util.DebugUtil.TESTS_DATA_COLLECTORS_ENABLE_SAVE_GAME_HISTORY);
        gameOptions.testMode = false;
        gameOptions.stopOnTurn = stopOnTurn;
        gameOptions.stopAtStep = stopAtStep;
        currentGame.setGameOptions(gameOptions);
        if (currentGame.isPaused()) {
            currentGame.resume();
        }
        currentGame.start(activePlayer.getId());
        currentGame.setGameStopped(true);
    }

    @Override
    protected TestPlayer createPlayer(String name, RangeOfInfluence rangeOfInfluence) {
        if ("PlayerA".equals(name)) {
            int skill = Integer.parseInt(System.getProperty("diag.skill", "6"));
            TestPlayer p = new TestPlayer(new TestComputerPlayer7(name, rangeOfInfluence, skill));
            p.setAIPlayer(true);
            return p;
        } else {
            // Deliberately inert goldfish opponent - see class docstring.
            TestPlayer p = new TestPlayer(new TestComputerPlayer(name, rangeOfInfluence));
            p.setAIPlayer(true);
            return p;
        }
    }

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL, MulliganType.GAME_DEFAULT.getMulligan(0), 40, 7);
        String deckFile = System.getProperty("diag.deck", "TymnaThrasiosTreefarm.dck");
        playerA = createPlayer(game, "PlayerA", deckFile);
        playerB = createPlayer(game, "PlayerB", deckFile);
        return game;
    }

    private void snapshot(long seed, int turn) {
        StringBuilder hand = new StringBuilder();
        for (Card c : currentGame.getPlayer(playerA.getId()).getHand().getCards(currentGame)) {
            if (hand.length() > 0) hand.append("|");
            hand.append(c.getName());
        }
        StringBuilder battlefield = new StringBuilder();
        for (Permanent p : currentGame.getBattlefield().getAllActivePermanents(playerA.getId())) {
            if (battlefield.length() > 0) battlefield.append("|");
            battlefield.append(p.getName());
        }
        StringBuilder graveyard = new StringBuilder();
        for (Card c : currentGame.getPlayer(playerA.getId()).getGraveyard().getCards(currentGame)) {
            if (graveyard.length() > 0) graveyard.append("|");
            graveyard.append(c.getName());
        }
        StringBuilder exile = new StringBuilder();
        for (Card c : currentGame.getExile().getAllCards(currentGame)) {
            if (!playerA.getId().equals(c.getOwnerId())) continue;
            if (exile.length() > 0) exile.append("|");
            exile.append(c.getName());
        }
        int librarySize = currentGame.getPlayer(playerA.getId()).getLibrary().size();
        int life = currentGame.getPlayer(playerA.getId()).getLife();
        DIAG_LOGGER.info("===SOLO_SNAPSHOT seed=" + seed + " turn=" + turn + " life=" + life
                + " librarySize=" + librarySize
                + " HAND[" + hand + "] BATTLEFIELD[" + battlefield + "] GRAVEYARD[" + graveyard + "] EXILE[" + exile + "]===");
    }

    @Test
    public void runSoloGoldfishBatch() throws Exception {
        String seedsProp = System.getProperty("diag.seeds", System.getProperty("diag.seed", "1"));
        String turnsProp = System.getProperty("diag.turns", "1,3,5,7,10");
        int[] checkpoints;
        {
            String[] parts = turnsProp.split(",");
            checkpoints = new int[parts.length];
            for (int i = 0; i < parts.length; i++) checkpoints[i] = Integer.parseInt(parts[i].trim());
        }
        int maxTurn = checkpoints[checkpoints.length - 1];

        // IMPORTANT: calling execute() a second time on the same game object (without an
        // intervening reset()) does NOT continue the game - it re-triggers what looks like the
        // opening-hand/mulligan sequence (observed: a spurious extra "library is shuffled" +
        // "take the first turn" at the second execute() call, corrupting the hand/turn
        // trajectory). Each checkpoint is therefore an INDEPENDENT reset()+execute() run, not a
        // shared-prefix continuation - fine for this phase's purposes (independent Monte Carlo
        // samples per checkpoint turn is standard and arguably cleaner than a shared prefix
        // would have been anyway, especially given seed nondeterminism, INFRA-0005).
        for (String seedStr : seedsProp.split(",")) {
            long baseSeed = Long.parseLong(seedStr.trim());
            for (int checkpoint : checkpoints) {
                long runSeed = baseSeed * 1000 + checkpoint;
                DIAG_LOGGER.info("===DIAG_GAME_START seed=" + runSeed + " checkpointTurn=" + checkpoint + "===");
                long startNanos = System.nanoTime();
                try {
                    RandomUtil.setSeed(runSeed);
                    reset();
                    setStopAt(checkpoint, PhaseStep.END_TURN);
                    executeWithRealHands();
                    snapshot(runSeed, checkpoint);
                    long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
                    DIAG_LOGGER.info("===DIAG_GAME_END seed=" + runSeed + " status=OK elapsedMs=" + elapsedMs + "===");
                } catch (Throwable t) {
                    long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
                    DIAG_LOGGER.info("===DIAG_GAME_END seed=" + runSeed + " status=EXCEPTION elapsedMs=" + elapsedMs
                            + " exceptionClass=" + t.getClass().getName()
                            + " exceptionMsg=" + String.valueOf(t.getMessage()).replace("\n", " ") + "===");
                }
            }
        }
    }
}
