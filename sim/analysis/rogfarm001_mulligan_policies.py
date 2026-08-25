"""SIM-ROGFARM-001 Section 6 — three pre-registered mulligan policies (P1 ENGINE_FORWARD, P2
BALANCED, P3 TURBO_RESPECTFUL), each a genuine, disclosed rule-based heuristic operationalizing
the assignment's own literal priority-ordered criteria (Section 6). Not generic XMage mulligans -
these are RogSi/Rog Farm/Blue Farm-specific, built around this project's own card classification
tables (opening_hand_model.ENGINES/TUTORS/INTERACTION_CASTABLE/ACCELERATION), matching the
project's established "structural hand grade" precedent (a lightweight, disclosed heuristic is a
legitimate Tier B method per the assignment's own evidence hierarchy - Section 0 explicitly
endorses "paired Monte Carlo / lightweight state model" for exactly this purpose, not a claim that
this IS the machine-optimal MULL-005R-style contextual policy built for the unrelated
Tymna/Thrasios deck).

Models multiplayer free mulligan (Commander variant: the FIRST mulligan draws a fresh 7 with NO
bottoming; only the second mulligan onward bottoms one additional card) + London bottoming with a
card-dependent (not random) bottom-selection heuristic.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import opening_hand_model as ohm  # noqa: E402

WHEEL_NAMES = {"Wheel of Fortune", "Timetwister", "Windfall", "Will of the Jeskai"}
WHEEL_PAYOFF_NAMES = {"Narset, Parter of Veils", "Notion Thief", "Faerie Mastermind"}
BREACH_PIECE_NAMES = {"Underworld Breach", "Lion's Eye Diamond", "Brain Freeze"}
THORACLE_PIECE_NAMES = {"Thassa's Oracle", "Demonic Consultation", "Tainted Pact"}


def _is_land(name, cards):
    return "Land" in cards[name]["type"]


def hand_features(hand, cards):
    lands = [c for c in hand if _is_land(c, cards)]
    engines = [c for c in hand if c in ohm.ENGINES]
    # Section 7's explicit caution: "Do not count Narset merely as 'engine online' without
    # identifying that its principal wheel value remains conditional." engine_count still
    # includes wheel-payoff cards (they ARE real engines for the generic online/timing census),
    # but non_wheel_engine_count excludes them - used by P2's conditional-blank check below so a
    # hand whose ONLY "engine" is a wheel payoff with no wheel synergy partner isn't laundered
    # into "meaningful access" by that classification alone.
    non_wheel_engines = [c for c in engines if c not in WHEEL_PAYOFF_NAMES]
    tutors = [c for c in hand if c in ohm.TUTORS]
    interaction = [c for c in hand if c in ohm.INTERACTION_CASTABLE]
    accel = [c for c in hand if c in ohm.ACCELERATION and not _is_land(c, cards)]
    wheels = [c for c in hand if c in WHEEL_NAMES]
    wheel_payoffs = [c for c in hand if c in WHEEL_PAYOFF_NAMES]
    breach_pieces = [c for c in hand if c in BREACH_PIECE_NAMES]
    thoracle_pieces = [c for c in hand if c in THORACLE_PIECE_NAMES]
    return {
        "land_count": len(lands), "engine_count": len(engines),
        "non_wheel_engine_count": len(non_wheel_engines), "tutor_count": len(tutors),
        "interaction_count": len(interaction), "accel_count": len(accel),
        "wheel_count": len(wheels), "wheel_payoff_count": len(wheel_payoffs),
        "breach_piece_count": len(breach_pieces), "thoracle_piece_count": len(thoracle_pieces),
        "any_engine_or_tutor": len(engines) + len(tutors) > 0,
        "any_win_access": len(breach_pieces) >= 2 or len(thoracle_pieces) >= 2,
    }


def _keep_value(name, cards, land_target):
    """Card-dependent bottom-selection score - higher survives bottoming longer."""
    if _is_land(name, cards):
        return 10.0  # lands are always valuable up to land_target, handled by the caller
    if name in ohm.ENGINES:
        return 9.0
    if name in ohm.TUTORS:
        return 8.0
    if name in BREACH_PIECE_NAMES or name in THORACLE_PIECE_NAMES:
        return 7.5
    if name in ohm.INTERACTION_CASTABLE:
        return 7.0
    if name in ohm.ACCELERATION:
        return 6.0
    if name in WHEEL_PAYOFF_NAMES:
        return 5.5
    if name in WHEEL_NAMES:
        return 4.0  # conditional payoff cards - genuinely lower floor value alone
    return 2.0  # generic filler


def bottom_to_size(hand, cards, target_size):
    """London mulligan bottoming: card-dependent, not random. Keeps a reasonable land count
    (min(land_count, 4) worth of lands preferentially) plus the highest-keep-value nonlands,
    bottoming the rest. Returns (kept_hand, bottomed_cards)."""
    if len(hand) <= target_size:
        return list(hand), []
    lands = [c for c in hand if _is_land(c, cards)]
    nonlands = [c for c in hand if not _is_land(c, cards)]
    land_keep_n = min(len(lands), max(2, min(4, target_size - 2)))
    kept_lands = lands[:land_keep_n]
    excess_lands = lands[land_keep_n:]
    nonlands_sorted = sorted(nonlands, key=lambda n: _keep_value(n, cards, land_keep_n), reverse=True)
    remaining_slots = target_size - len(kept_lands)
    kept_nonlands = nonlands_sorted[:remaining_slots]
    bottomed_nonlands = nonlands_sorted[remaining_slots:]
    kept = kept_lands + kept_nonlands
    bottomed = excess_lands + bottomed_nonlands
    # if we came up short on nonlands, pull back in some excess lands
    if len(kept) < target_size and excess_lands:
        pull = excess_lands[: target_size - len(kept)]
        kept += pull
        bottomed = [c for c in bottomed if c not in pull] + [c for c in excess_lands if c not in pull]
    return kept[:target_size], bottomed


# ---- P1 ENGINE_FORWARD: 1) T1 engine, 2) T2 protected/premium engine, 3) sufficient mana+interaction
def p1_keep(features):
    if features["land_count"] < 2 or features["land_count"] > 5:
        return False
    has_early_engine_access = features["engine_count"] > 0 or features["tutor_count"] > 0 or features["accel_count"] > 0
    if not has_early_engine_access:
        return False
    if features["land_count"] + features["accel_count"] < 2:
        return False
    return True


# ---- P2 BALANCED: 1) meaningful engine/win access, 2) sufficient mana, 3) interaction retained,
# 4) avoidance of conditional blanks (a hand that's ONLY wheels/payoffs with nothing else live)
def p2_keep(features):
    if features["land_count"] < 2 or features["land_count"] > 5:
        return False
    meaningful_access = (
        features["engine_count"] > 0 or features["tutor_count"] > 0
        or features["any_win_access"] or features["wheel_payoff_count"] > 0
    )
    if not meaningful_access:
        return False
    conditional_only = (
        (features["wheel_count"] + features["wheel_payoff_count"]) > 0
        and features["non_wheel_engine_count"] == 0 and features["tutor_count"] == 0
        and features["interaction_count"] == 0 and features["accel_count"] == 0
        and not features["any_win_access"]
    )
    if conditional_only:
        return False
    return True


# ---- P3 TURBO_RESPECTFUL: 1) credible early development, 2) ability to interact with a canonical
# T2 win, 3) engine/win access after retaining defense (i.e. keep enough back to still hold up
# interaction while developing)
def p3_keep(features):
    if features["land_count"] < 2 or features["land_count"] > 5:
        return False
    credible_development = features["land_count"] + features["accel_count"] >= 3
    if not credible_development:
        return False
    if features["interaction_count"] == 0:
        # Turbo-respectful hands without ANY interaction need overwhelming win access instead.
        if not (features["any_win_access"] or features["tutor_count"] >= 2):
            return False
    return True


POLICIES = {
    "P1_ENGINE_FORWARD": p1_keep,
    "P2_BALANCED": p2_keep,
    "P3_TURBO_RESPECTFUL": p3_keep,
}


def london_mulligan(library, cards, rng, policy_fn, on_play, max_mulligans=4):
    """Multiplayer free mulligan (first mulligan bottoms 0 extra cards) + London bottoming with
    the card-dependent bottom_to_size() heuristic above. Returns (kept_hand, remaining_library,
    mulligan_count)."""
    lib = list(library)
    rng.shuffle(lib)
    mulligan_count = 0
    while True:
        hand_full = lib[:7]
        rest = lib[7:]
        bottom_n = max(0, mulligan_count - 1)  # free first mulligan
        target_size = 7 - bottom_n
        kept, bottomed = bottom_to_size(hand_full, cards, target_size)
        features = hand_features(kept, cards)
        if policy_fn(features) or mulligan_count >= max_mulligans:
            library_out = bottomed + rest
            return kept, library_out, mulligan_count
        mulligan_count += 1
        rng.shuffle(lib)
