"""SIM-001 MULL-006 section 17 — do NOT naively sum scores: compare valuation architectures.

Implements the four required architectures over a contextual_trajectory_object.py object, all
sharing strength_speed_matrix.GRADE_ORDER as a common output currency (S+ through F) so their
outputs are directly comparable. None of the four is asserted correct - build_contextual_policy_
comparison.py (task #117) tests them against real simulated outcomes; this module only builds them
and discloses their differing structural properties, per the assignment's explicit "Do not assume
these exact gates are correct. Test alternatives."

A. WEIGHTED MODEL - numeric score, every dimension always contributes something (bounded).
B. LEXICOGRAPHIC MODEL - strict priority order; only the highest-priority NON-NEUTRAL dimension
   moves the grade, each move capped at one step - lower-priority dimensions never override a
   higher-priority one, even in combination.
C. GATED MODEL - directly implements the assignment's three named example gates as hard caps
   applied BEFORE any bonus, not as continuous weights.
D. RULE/TREE MODEL - mutually exclusive branches (not weights, not gates-then-bonus) - each hand
   takes exactly one path.

DRAW_DEPENDENCE_PROBABILITY_GATE_THRESHOLD (0.2) and the ALL_IN "exceptional" grade set are
disclosed, round conventions - not fit to data, not pilot-supplied.
"""
from strength_speed_matrix import GRADE_ORDER, GRADE_RANK

VALUATION_PROVENANCE = "MODEL_DERIVED"

DRAW_DEPENDENCE_PROBABILITY_GATE_THRESHOLD = 0.2
EXCEPTIONAL_GRADES = {"S+", "S", "A+"}

# SEAT_EXPOSURE_PENALTY / SEAT_EXCESS_EXPOSURE reuse seat_timing_model.py's own finding (task
# #107): excess_exposure_turns(seat) = seat - 1 is a pure, constant function of seat, independent
# of deployment turn or engine identity - the same quantity the section-6 seat census used to
# measure real KEEP->MULL flips. Folded into all four architectures here so seat can actually
# change a contextual grade at all (a trajectory object exposes seat-timing fields per section 16,
# but none of section 17's four architectures read them without this).
_DRAW_DEP_WEIGHT = {
    "SELF_CONTAINED": 0.0, "BROAD_OUTS": -0.5, "NARROW_OUTS": -1.0,
    "EXACT_OR_NEAR_EXACT": -1.5, "NOT_APPLICABLE_NO_DESTINATION": 0.0,
}
_RESILIENCE_WEIGHT = {"ROBUST": 0.5, "RECOVERABLE": 0.0, "FRAGILE": -0.5, "ALL_IN": -1.0, None: 0.0}
_POD_MODIFIER_WEIGHT = {"VERY_HIGH": 0.5, "HIGH": 0.25, "MODERATE": 0.0, "LOW": -0.25, "UNKNOWN": 0.0, None: 0.0}
SEAT_EXPOSURE_WEIGHT_PER_TURN = -0.15
FRAGILE_RESILIENCE_CLASSES = ("FRAGILE", "ALL_IN")


def _rank(grade):
    return GRADE_RANK[grade]


def _grade_at(rank):
    return GRADE_ORDER[max(0, min(len(GRADE_ORDER) - 1, rank))]


def _excess_exposure(obj):
    seat = obj.get("seat") or 1
    return seat - 1


def weighted_model(obj):
    base_rank = _rank(obj["base_trajectory_grade"])
    shift = 0.0
    shift += _DRAW_DEP_WEIGHT.get(obj["draw_dependence_class"], 0.0)
    shift += _RESILIENCE_WEIGHT.get(obj["resilience_class"], 0.0)
    relevant = obj["relevant_agency"] if isinstance(obj["relevant_agency"], int) else 0
    shift += min(0.75, 0.25 * relevant)
    shift += _POD_MODIFIER_WEIGHT.get(obj["pod_realization_modifier"], 0.0)
    shift += 0.5 if obj["verified_combo_proximity"] else 0.0
    shift += SEAT_EXPOSURE_WEIGHT_PER_TURN * _excess_exposure(obj)
    final_rank = base_rank - round(shift)  # lower rank = better grade
    return _grade_at(final_rank)


def lexicographic_model(obj):
    base_rank = _rank(obj["base_trajectory_grade"])
    dep, res = obj["draw_dependence_class"], obj["resilience_class"]
    if dep in ("NARROW_OUTS", "EXACT_OR_NEAR_EXACT"):
        return _grade_at(base_rank + 1)
    if res == "ALL_IN":
        return _grade_at(base_rank + 1)
    if obj.get("pod_realization_modifier") == "LOW" and dep != "SELF_CONTAINED":
        return _grade_at(base_rank + 1)
    if _excess_exposure(obj) >= 2 and res in FRAGILE_RESILIENCE_CLASSES:
        return _grade_at(base_rank + 1)
    if res == "ROBUST" and dep in ("SELF_CONTAINED", "BROAD_OUTS"):
        return _grade_at(base_rank - 1)
    relevant = obj["relevant_agency"] if isinstance(obj["relevant_agency"], int) else 0
    if relevant >= 2:
        return _grade_at(base_rank - 1)
    return obj["base_trajectory_grade"]


def gated_model(obj):
    rank = _rank(obj["base_trajectory_grade"])
    gate_triggered = False

    if obj["destination"] is None:
        gate_triggered = True
        rank = max(rank, _rank("C"))  # interaction cannot elevate above a C ceiling

    prob = obj["probability_of_trajectory"]
    if prob is not None and prob < DRAW_DEPENDENCE_PROBABILITY_GATE_THRESHOLD and \
            obj["draw_dependence_class"] in ("NARROW_OUTS", "EXACT_OR_NEAR_EXACT"):
        gate_triggered = True
        rank += 1  # downgrade BEFORE any agency bonus

    if obj["resilience_class"] == "ALL_IN" and obj["base_trajectory_grade"] not in EXCEPTIONAL_GRADES:
        gate_triggered = True
        rank = max(rank, _rank("C"))

    # seat-exposure gate: a fragile/all-in trajectory facing 2+ excess opponent turns of exposure
    # (Seat 3/4 relative to Seat 1) before it even lands is downgraded before any agency bonus -
    # generalizes the disclosed SEAT_EXPOSURE_PROBE_RULE from seat_adjusted_trajectory_census.json
    # (task #107) into a reusable architecture rule, not a one-off measurement script.
    if _excess_exposure(obj) >= 2 and obj["resilience_class"] in FRAGILE_RESILIENCE_CLASSES:
        gate_triggered = True
        rank += 1

    # pod-realization gate: an opponent-triggered engine with LOW expected realization against
    # this specific archetype, on a trajectory that ALSO already carries draw-dependence risk,
    # is downgraded before any agency bonus.
    if obj.get("pod_realization_modifier") == "LOW" and obj["draw_dependence_class"] != "SELF_CONTAINED":
        gate_triggered = True
        rank += 1

    if not gate_triggered:
        relevant = obj["relevant_agency"] if isinstance(obj["relevant_agency"], int) else 0
        if relevant >= 2:
            rank -= 1

    return _grade_at(rank)


def tree_model(obj):
    base = obj["base_trajectory_grade"]
    if obj["destination"] is None:
        return _grade_at(max(_rank(base), _rank("D")))
    if obj["resilience_class"] == "ALL_IN":
        if base in EXCEPTIONAL_GRADES:
            return base
        return _grade_at(_rank(base) + 2)
    if _excess_exposure(obj) >= 2 and obj["resilience_class"] == "FRAGILE":
        return _grade_at(_rank(base) + 1)
    if obj.get("pod_realization_modifier") == "LOW" and obj["draw_dependence_class"] != "SELF_CONTAINED":
        return _grade_at(_rank(base) + 1)
    prob = obj["probability_of_trajectory"]
    if obj["draw_dependence_class"] == "EXACT_OR_NEAR_EXACT" and prob is not None and prob < 0.1:
        return _grade_at(_rank(base) + 1)
    relevant = obj["relevant_agency"] if isinstance(obj["relevant_agency"], int) else 0
    if obj["resilience_class"] == "ROBUST" and relevant >= 1:
        return _grade_at(_rank(base) - 1)
    return base


ARCHITECTURES = {
    "weighted": weighted_model,
    "lexicographic": lexicographic_model,
    "gated": gated_model,
    "tree": tree_model,
}


def apply_all_architectures(obj):
    """Returns a NEW object with contextual_trajectory_grade filled in for all four
    architectures - does not mutate `obj`."""
    return {**obj, "contextual_trajectory_grade": {name: fn(obj) for name, fn in ARCHITECTURES.items()}}
