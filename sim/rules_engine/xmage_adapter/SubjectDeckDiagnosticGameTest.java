package org.mage.test.commander.duel;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.util.RandomUtil;
import org.junit.BeforeClass;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer7;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * Real deck-backed diagnostic game driver (INFRA-0004 / diagnostic gameplay
 * phase). Uses ComputerPlayer7 (mage.player.ai, skill 6) wrapped by
 * TestComputerPlayer7 for genuine simulation-based AI play across full
 * turns - NOT the plain ComputerPlayer used elsewhere in this project's
 * scripted interaction tests, whose priority() is a bare "pass" stub with
 * no real decision logic (see sim/rules_engine/xmage_adapter/README.md's
 * "known-defect log" for how that was discovered).
 */
public class SubjectDeckDiagnosticGameTest extends CardTestPlayerAPIImpl {

    /**
     * Must seed here, not in the @Test body: JUnit runs @Before (which
     * builds the game and loads/shuffles both decks - see reset() in
     * CardTestPlayerAPIImpl) before the @Test method executes. Seeding
     * inside runDiagnosticGame() was too late and silently produced a
     * fresh-entropy shuffle every run despite a fixed --diag.seed - a real
     * reproducibility defect found by re-running the same seed twice and
     * diffing the transcripts (see results/diagnostic/README.md).
     */
    @BeforeClass
    public static void seedRandomBeforeAnySetup() {
        long seed = Long.parseLong(System.getProperty("diag.seed", "1"));
        RandomUtil.setSeed(seed);
    }

    @Override
    protected TestPlayer createPlayer(String name, RangeOfInfluence rangeOfInfluence) {
        TestPlayer testPlayer = new TestPlayer(new TestComputerPlayer7(name, rangeOfInfluence, 6));
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
    public void runDiagnosticGame() {
        int maxTurn = Integer.parseInt(System.getProperty("diag.maxTurn", "6"));
        setStopAt(maxTurn, PhaseStep.END_TURN);
        execute();
    }
}
