"""SIM-001 MULL-006 section 4 — relative deployment speed, independent of engine strength.

PILOT_SUPPLIED_STRATEGIC_PRIOR (initialization prior, not a conclusion - tested against real
simulated outcomes in strength_speed_sensitivity.json, task #106). "Expected deployment turn" is
explicitly NOT printed mana value (assignment section 4: "Smothering Tithe and Pod should NOT be
evaluated purely from printed mana value... 'expected deployment' is deck-specific") - it is a
second, independent deck-specific prior, back-derived here to exactly reproduce every worked
example the assignment gives:

    T1 functional Pod   -> S   T2 functional Pod -> A   =>  expected_turn(Pod)   = 3
    T1 Smothering Tithe -> S   T2 Smothering Tithe -> A  =>  expected_turn(Tithe) = 3
    T1 Rhystic/Mastermind/Archivist/Library/Heartwood/Armasaur -> A
    T2 Rhystic/Mastermind/Archivist/Library/Heartwood/Armasaur -> B
                                                              =>  expected_turn = 2 (all six)
    T1 Remora/Sentinel -> B   T2 Remora/Sentinel -> C     =>  expected_turn(Remora/Sentinel) = 1
    T3 two-drop engine -> C (expected=2, actual=3, diff=+1, matches the formula below)

From these, relative speed is a single linear function of (actual_turn - expected_turn):

    diff <= -2  ->  S  (EXTREMELY ACCELERATED)
    diff == -1  ->  A  (AHEAD OF CURVE)
    diff ==  0  ->  B  (ON TIME / EXPECTED)
    diff == +1  ->  C  (BEHIND CURVE)
    diff >= +2  ->  D  (SUBSTANTIALLY LATE)

Survival of the Fittest is NOT one of the assignment's worked examples - expected_turn=2 is an
EXTRAPOLATED prior (matched to the CMC-2 "mid" engine class it shares with Sylvan Library/
Faerie Mastermind), disclosed as extrapolated rather than pilot-verbatim, distinct from the other
six entries which are back-derived to exactly reproduce a given example.

Abhorrent Oculus deliberately has NO expected_deployment_turn here - per section 3, it is a
separate premier destination, never scored on this engine-speed scale either.
"""

SPEED_PROVENANCE = "PILOT_SUPPLIED_STRATEGIC_PRIOR"

EXPECTED_DEPLOYMENT_TURN = {
    "Mystic Remora": 1,
    "Esper Sentinel": 1,
    "Rhystic Study": 2,
    "Faerie Mastermind": 2,
    "Archivist of Oghma": 2,
    "Sylvan Library": 2,
    "Heartwood Storyteller": 2,
    "Runic Armasaur": 2,
    "Survival of the Fittest": 2,  # EXTRAPOLATED - not a worked example, see module docstring
    "Smothering Tithe": 3,
    "Birthing Pod": 3,
}
EXTRAPOLATED_ENTRIES = {"Survival of the Fittest"}

SPEED_ORDER = ["S", "A", "B", "C", "D"]
SPEED_RANK = {label: i for i, label in enumerate(SPEED_ORDER)}


def relative_speed(engine_name, actual_turn):
    """Returns the S/A/B/C/D relative-speed label for `engine_name` deployed on `actual_turn`, or
    None if `engine_name` has no expected_deployment_turn entry (e.g. Abhorrent Oculus, or any
    card outside this deck's named engine set)."""
    expected = EXPECTED_DEPLOYMENT_TURN.get(engine_name)
    if expected is None:
        return None
    diff = actual_turn - expected
    if diff <= -2:
        return "S"
    if diff == -1:
        return "A"
    if diff == 0:
        return "B"
    if diff == 1:
        return "C"
    return "D"
