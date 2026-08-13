"""SIM-001 MULL-006 section 3 — pilot-supplied intrinsic engine-strength prior.

PILOT_SUPPLIED_STRATEGIC_PRIOR: NOT an empirical finding. This ranking was supplied directly by
the pilot as a starting point for testing how engine strength interacts with deployment speed,
seat, draw dependence, resilience, and pod context (assignment sections 3-5). Never write "the
simulation proves Tithe is S-tier" - the ranking itself is never simulated; only its INTERACTIONS
with the other contextual dimensions are tested against real simulated trajectories.

    S      : Smothering Tithe, Birthing Pod (only when FUNCTIONAL - see functional_pod())
    A+     : Rhystic Study
    A      : Mystic Remora, Faerie Mastermind
    A-     : Esper Sentinel, Archivist of Oghma
    B+     : Sylvan Library
    B      : Survival of the Fittest (only when FUNCTIONAL - see functional_survival())
    B-     : Heartwood Storyteller
    C+/B-  : Runic Armasaur (pilot placed this ON the C+/B- boundary, not cleanly in either band)

Abhorrent Oculus is deliberately NOT in this table - per assignment section 3, Oculus remains a
separate PREMIER DESTINATION, never folded into the resource-engine strength ranking. Its
trajectory quality is determined by deployment turn/route/resources consumed/resulting board/
follow-up/resilience/agency (sections 4 onward), exactly like every other destination, not by an
engine-strength label.

----------------------------------------------------------------------------------------------
FAERIE MASTERMIND CORRECTION (reverses part of MULL-005R's REALIZE-001 finding, by explicit
pilot instruction): Mastermind is a draw engine because of its PASSIVE triggered ability
("Whenever an opponent draws their second card each turn, you draw a card") - real Oracle text,
unconditional once Mastermind is on the battlefield. MULL-005R required its {3}{U} ACTIVATED
ability to be currently payable before granting ANY Tier-C credit, on the reasoning that the
passive is structurally unmeasurable by a solo/no-opponent model. MULL-006 explicitly overrides
that for ENGINE-STRENGTH purposes: engine status here does NOT require activation support -
Mastermind is proxy-credited as strength "A" on deployment alone, the same disclosed-proxy
treatment already given to Rhystic Study/Mystic Remora/Smothering Tithe (equally unmeasurable
opponent-triggered engines - TITHE-001's own consistency argument, now extended to Mastermind).
The {3}{U} activated ability remains real, additional utility/combo architecture on top, not a
prerequisite for the engine label.
----------------------------------------------------------------------------------------------
BIRTHING POD: "functional" means something concrete (assignment section 3), not "Pod is on the
battlefield": Pod actually deployed, legal fodder available, a useful legal activation currently
payable. This module does NOT additionally verify that the resulting conversion would be a
genuine upgrade (that would require replicating the bounded search's own target enumeration) -
disclosed simplification, see functional_pod()'s docstring.
----------------------------------------------------------------------------------------------
"""
from opening_hand_model import parse_cost

STRENGTH_PROVENANCE = "PILOT_SUPPLIED_STRATEGIC_PRIOR"

ENGINE_STRENGTH_PRIOR = {
    "Smothering Tithe": "S",
    "Birthing Pod": "S",              # gated - see functional_pod()
    "Rhystic Study": "A+",
    "Mystic Remora": "A",
    "Faerie Mastermind": "A",          # passive alone - see FAERIE MASTERMIND CORRECTION above
    "Esper Sentinel": "A-",
    "Archivist of Oghma": "A-",
    "Sylvan Library": "B+",
    "Survival of the Fittest": "B",    # gated - see functional_survival()
    "Heartwood Storyteller": "B-",
    "Runic Armasaur": "C+/B-",
}

# Ordinal rank, lower = stronger. "C+/B-" sits deliberately between B- and a hypothetical C band -
# the pilot did not give it a clean single label, so it is ranked immediately below B- rather than
# forced into either neighboring band.
STRENGTH_ORDER = ["S", "A+", "A", "A-", "B+", "B", "B-", "C+/B-"]
ENGINE_STRENGTH_RANK = {label: i for i, label in enumerate(STRENGTH_ORDER)}

POD_ACTIVATION_COST = "{1}{G/P}"
SURVIVAL_ACTIVATION_COST = "{G}"


def functional_pod(state, cards):
    """Concrete FUNCTIONAL test for Birthing Pod (assignment section 3): deployed + legal fodder
    + a useful legal activation currently payable. Does NOT verify the resulting found card would
    be a genuine upgrade (that would require replicating the bounded search's own target
    enumeration inside this coarse strength-prior check) - a disclosed simplification; the actual
    bounded search (trajectory_search.py's pod: candidate family) still separately verifies a real
    target exists and is reachable when computing the trajectory itself. This function only gates
    whether Pod COUNTS as a functional S-tier engine for the strength prior."""
    pod = next((p for p in state.nonland_perms if p.name == "Birthing Pod" and not p.tapped), None)
    if pod is None:
        return False
    fodder = [p for p in state.nonland_perms if p is not pod and "Creature" in cards[p.name]["type"]]
    if not fodder:
        return False
    from opening_hand_policy import _try_pay
    gen, pips, x = parse_cost(POD_ACTIVATION_COST)
    return _try_pay(state, gen, pips) is not None


def functional_survival(state, cards):
    """Concrete FUNCTIONAL test for Survival of the Fittest: deployed + a discardable creature
    card actually in hand + the {G} activation cost currently payable."""
    survival = next((p for p in state.nonland_perms if p.name == "Survival of the Fittest"), None)
    if survival is None:
        return False
    has_fuel = any("Creature" in cards[c]["type"] for c in state.hand)
    if not has_fuel:
        return False
    from opening_hand_policy import _try_pay
    gen, pips, x = parse_cost(SURVIVAL_ACTIVATION_COST)
    return _try_pay(state, gen, pips) is not None


def engine_strength(name, state, cards):
    """Returns the ordinal strength label (see STRENGTH_ORDER) for `name` given the CURRENT
    state, or None if `name` isn't in the pilot-supplied prior, isn't actually on the battlefield,
    or (Pod/Survival specifically) is deployed but not currently FUNCTIONAL. Deployment alone is
    NECESSARY for every entry (a card sitting in hand has no passive/static/activated ability
    live at all - the FAERIE MASTERMIND CORRECTION removes the ACTIVATION-support requirement,
    it does not remove the deployment requirement), and for Pod/Survival specifically it is not
    SUFFICIENT either - see functional_pod()/functional_survival()."""
    if name == "Birthing Pod":
        return "S" if functional_pod(state, cards) else None
    if name == "Survival of the Fittest":
        return "B" if functional_survival(state, cards) else None
    if name not in ENGINE_STRENGTH_PRIOR:
        return None
    on_battlefield = any(p.name == name for p in state.nonland_perms)
    return ENGINE_STRENGTH_PRIOR[name] if on_battlefield else None
