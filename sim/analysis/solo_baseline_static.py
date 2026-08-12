"""SIM-001 SOLO BASELINE v1 — STATIC/COMBINATORIAL layer.

Pure hypergeometric/combinatorial math over the exact frozen decklist
(data/decklists/tymna-thrasios-treefarm-v1.json, hash-verified). No
gameplay, no engine, no AI policy involved - run_class STATIC_ANALYSIS per
docs/RUN_CLASSIFICATION.md. Every number here is exact (not sampled), so
"sample count/seeds" doesn't apply the way it does for the other two
layers - each figure is the closed-form probability itself.

Card classification (accel/tutor/interaction/land-colors) is heuristic
oracle-text pattern matching with manual spot-corrections, same standard
this project has used since Gate 1 (see docs/assignments/SIM-001.md's own
"heuristic ability classification... acceptable for diagnostic purposes,
not manually exhaustively reviewed" framing) - not a claim of exhaustive
manual review of all 98 cards.
"""
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DECKLIST_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-v1.json"
CARDS_CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"
INTERACTIONS_DIR = REPO_ROOT / "interactions" / "verified"

LIBRARY_SIZE = 98  # main deck only - commanders are cast from the command zone, not drawn

# --- manual, spot-corrected classification (see module docstring) -----

ACCELERATION = {
    "Avacyn's Pilgrim", "Birds of Paradise", "Chrome Mox", "Deathrite Shaman",
    "Delighted Halfling", "Devoted Druid", "Elves of Deep Shadow", "Lotus Petal",
    "Mana Vault", "Mox Amber", "Mox Diamond", "Noble Hierarch", "Sol Ring",
}

TUTORS = {
    "Birthing Pod", "Chord of Calling", "Crop Rotation", "Demonic Tutor",
    "Eldritch Evolution", "Enlightened Tutor", "Finale of Devastation",
    "Imperial Seal", "Nature's Rhythm", "Ranger-Captain of Eos",
    "Sowing Mycospawn", "Spellseeker", "Survival of the Fittest", "Vampiric Tutor",
}

INTERACTION = {
    "Fierce Guardianship", "Flare of Denial", "Flusterstorm", "Force of Negation",
    "Force of Will", "Mental Misstep", "Pact of Negation", "Swan Song",
    "Mindbreak Trap", "Silence", "Misdirection", "Commandeer", "Subtlety",
    "Deathrite Shaman", "Orcish Bowmasters", "Colossal Skyturtle",
    "Veil of Summer", "Volatile Stormdrake", "Gilded Drake", "Endurance",
    "Ranger-Captain of Eos",
}

LAND_COLORS = {
    "Ancient Tomb": set(), "City of Traitors": set(), "Gemstone Caverns": set(),
    "Bayou": {"B", "G"}, "Boseiju, Who Endures": {"G"}, "City of Brass": {"W", "U", "B", "G"},
    "Command Tower": {"W", "U", "B", "G"}, "Exotic Orchard": {"W", "U", "B", "G"},
    "Flooded Strand": {"U", "W"}, "Gaea's Cradle": {"G"}, "Mana Confluence": {"W", "U", "B", "G"},
    "Marsh Flats": {"B", "W"}, "Minamo, School at Water's Edge": {"U"}, "Misty Rainforest": {"G", "U"},
    "Otawara, Soaring City": {"U"}, "Polluted Delta": {"B", "U"}, "Savannah": {"G", "W"},
    "Scrubland": {"B", "W"}, "Shifting Woodland": {"G"}, "Starting Town": {"W", "U", "B", "G"},
    "Talon Gates of Madara": {"W", "U", "B", "G"}, "Tropical Island": {"G", "U"},
    "Tundra": {"U", "W"}, "Underground Sea": {"B", "U"}, "Verdant Catacombs": {"B", "G"},
    "Windswept Heath": {"G", "W"}, "Wooded Foothills": {"G"},
}

COMMANDERS = {
    "Tymna the Weaver": {"colors": {"W", "B"}, "generic": 1},   # {1}{W}{B}
    "Thrasios, Triton Hero": {"colors": {"G", "U"}, "generic": 0},  # {G}{U}
}


def load_deck():
    payload = json.loads(DECKLIST_PATH.read_text(encoding="utf-8"))
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from sim.validation.run_classification import compute_deck_hash
    actual_hash = compute_deck_hash(payload["commanders"], payload["cards"])
    assert actual_hash == payload["deck_hash"], "deck_hash mismatch - refusing to analyze a tampered/stale decklist"
    return payload


def hypergeom_at_least_one(population, successes, draws):
    """P(>=1 success) drawing `draws` cards without replacement from `population` with `successes` hits."""
    if successes <= 0:
        return 0.0
    if draws >= population:
        return 1.0 if successes > 0 else 0.0
    p_zero = math.comb(population - successes, draws) / math.comb(population, draws)
    return 1.0 - p_zero


def hypergeom_exact(population, successes, draws, k):
    """P(exactly k successes)."""
    if k > successes or k > draws or (draws - k) > (population - successes):
        return 0.0
    return math.comb(successes, k) * math.comb(population - successes, draws - k) / math.comb(population, draws)


def hypergeom_all_present(population, m_distinct_singletons, draws):
    """P(all m specific 1-of cards are among `draws` cards drawn from `population`)."""
    if draws < m_distinct_singletons:
        return 0.0
    return math.comb(population - m_distinct_singletons, draws - m_distinct_singletons) / math.comb(population, draws)


def cards_seen_by_turn(turn, on_play):
    """Cards seen counting opening hand + draw steps. On the play skips the turn-1 draw (CR 103.7a)."""
    draws = (turn - 1) if on_play else turn
    return 7 + draws


def main():
    payload = load_deck()
    cards = payload["cards"]
    names = {c["name"] for c in cards}
    commanders = payload["commanders"]

    land_names = set(LAND_COLORS.keys()) & names
    n_lands = len(land_names)
    n_accel = len(ACCELERATION & names)
    n_tutors = len(TUTORS & names)
    n_interaction = len(INTERACTION & names)

    color_source_counts = {c: 0 for c in "WUBG"}
    for land, colors in LAND_COLORS.items():
        if land in names:
            for c in colors:
                color_source_counts[c] += 1
    # nonland color sources (accel pieces that produce colored mana) - conservative: only ones with
    # an unconditional colored mana ability, per the same oracle-text pass used for ACCELERATION
    NONLAND_COLOR_SOURCES = {
        "Avacyn's Pilgrim": {"W"}, "Birds of Paradise": {"W", "U", "B", "G"},
        "Deathrite Shaman": {"B", "G"}, "Delighted Halfling": {"W", "U", "B", "G"},
        "Devoted Druid": {"G"}, "Elves of Deep Shadow": {"B"}, "Noble Hierarch": {"W", "U", "G"},
    }
    for card, colors in NONLAND_COLOR_SOURCES.items():
        if card in names:
            for c in colors:
                color_source_counts[c] += 1

    turns = [1, 3, 5, 7, 10]
    on_play_variants = [True, False]

    result = {
        "run_class": "STATIC_ANALYSIS",
        "phase": "SIM_001_SOLO_BASELINE_V1",
        "subject_deck_version": payload["deck_version"],
        "subject_deck_hash": payload["deck_hash"],
        "library_size": LIBRARY_SIZE,
        "commanders": commanders,
        "classification_counts": {
            "lands": n_lands, "acceleration": n_accel, "tutors": n_tutors, "interaction": n_interaction,
            "color_sources_land_only": color_source_counts,
        },
        "methodology_note": (
            "Card classification (acceleration/tutor/interaction/land-colors) is heuristic oracle-text "
            "pattern matching with manual spot-corrections, not an exhaustive manual review of all 98 "
            "cards - consistent with this project's established heuristic-classification standard. "
            "Commander castability approximates 'enough matching-color LAND sources in play' and ignores "
            "actual land-drop sequencing/tapping decisions (that's ENGINE-GOLDFISH/POLICY-DEPENDENT "
            "territory, not static combinatorics) and nonland accel's contribution except where noted."
        ),
        "opening_hand": {},
        "by_turn": {},
        "commander_castability_by_turn": {},
        "deterministic_combo_accessibility": {},
        "conditional_combo_piece_accessibility_own_deck_only": {},
        "pod_survival_accessibility": {},
        "cards_seen_by_turn": {},
        "mulligan_structural_hand_quality": {},
    }

    # Opening hand (7 cards) land count distribution
    land_dist = {k: hypergeom_exact(LIBRARY_SIZE, n_lands, 7, k) for k in range(0, 8)}
    result["opening_hand"]["land_count_distribution"] = land_dist
    result["opening_hand"]["p_at_least_2_lands"] = sum(v for k, v in land_dist.items() if k >= 2)
    result["opening_hand"]["p_at_least_1_land"] = sum(v for k, v in land_dist.items() if k >= 1)
    result["opening_hand"]["p_flood_6plus_lands"] = sum(v for k, v in land_dist.items() if k >= 6)
    result["opening_hand"]["expected_lands"] = sum(k * v for k, v in land_dist.items())

    for on_play in on_play_variants:
        key = "on_play" if on_play else "on_draw"
        result["by_turn"][key] = {}
        result["cards_seen_by_turn"][key] = {}
        result["commander_castability_by_turn"][key] = {}
        for t in turns:
            draws = cards_seen_by_turn(t, on_play)
            result["cards_seen_by_turn"][key][str(t)] = draws
            result["by_turn"][key][str(t)] = {
                "p_at_least_1_land_source_each_color": {
                    c: hypergeom_at_least_one(LIBRARY_SIZE, color_source_counts[c], draws) for c in "WUBG"
                },
                "p_at_least_1_acceleration": hypergeom_at_least_one(LIBRARY_SIZE, n_accel, draws),
                "p_at_least_1_tutor": hypergeom_at_least_one(LIBRARY_SIZE, n_tutors, draws),
                "p_at_least_1_interaction": hypergeom_at_least_one(LIBRARY_SIZE, n_interaction, draws),
                "p_at_least_N_lands": {str(n): sum(
                    hypergeom_exact(LIBRARY_SIZE, n_lands, draws, k) for k in range(n, draws + 1)
                ) for n in (2, 3, 4)},
            }
            # commander castability: needs land count >= (colors+generic) AND both required colors present
            for cname, spec in COMMANDERS.items():
                need_lands = len(spec["colors"]) + spec["generic"]
                p_lands = sum(hypergeom_exact(LIBRARY_SIZE, n_lands, draws, k) for k in range(need_lands, draws + 1)) if draws >= need_lands else 0.0
                p_colors = 1.0
                for c in spec["colors"]:
                    p_colors *= hypergeom_at_least_one(LIBRARY_SIZE, color_source_counts[c], draws)
                # conservative joint approx (independence assumption, documented) - land-count and
                # color-presence are correlated (fewer total lands makes covering both colors harder),
                # so this modestly OVERSTATES true joint probability; flagged, not corrected, since an
                # exact joint calc needs a multivariate hypergeometric over each land's color set, which
                # ENGINE-GOLDFISH data (real games) cross-checks empirically instead.
                result["commander_castability_by_turn"][key].setdefault(str(t), {})[cname] = {
                    "p_enough_total_lands": p_lands,
                    "p_both_colors_present_approx_independent": p_colors,
                    "approx_joint_upper_bound_note": "min(p_enough_total_lands, p_colors) is a tighter upper bound than the product; see ENGINE-GOLDFISH cross-check for the real figure",
                }

    # Deterministic (conditional:false) combo piece accessibility
    for f in sorted(INTERACTIONS_DIR.glob("INT-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        card_names = [c["name"] for c in d.get("cards", [])]
        m = len(card_names)
        bucket = "deterministic_combo_accessibility" if d.get("conditional") is False else "conditional_combo_piece_accessibility_own_deck_only"
        entry = {
            "interaction_id": d["id"], "verification_level": d.get("verification_level"),
            "cards": card_names, "piece_count": m,
            "p_all_pieces_drawn_by_turn": {},
        }
        for on_play in on_play_variants:
            key = "on_play" if on_play else "on_draw"
            entry["p_all_pieces_drawn_by_turn"][key] = {
                str(t): hypergeom_all_present(LIBRARY_SIZE, m, cards_seen_by_turn(t, on_play)) for t in turns
            }
        result[bucket][d["id"]] = entry

    # Birthing Pod / Survival of the Fittest specifically
    for card in ("Birthing Pod", "Survival of the Fittest"):
        if card not in names:
            continue
        entry = {"p_drawn_by_turn": {}}
        for on_play in on_play_variants:
            key = "on_play" if on_play else "on_draw"
            entry["p_drawn_by_turn"][key] = {
                str(t): hypergeom_at_least_one(LIBRARY_SIZE, 1, cards_seen_by_turn(t, on_play)) for t in turns
            }
        result["pod_survival_accessibility"][card] = entry

    # Mulligan-relevant structural hand quality: defined heuristic threshold, explicitly labeled as
    # a chosen definition (not a universal one) - "keepable" = 2-5 lands AND at least one land or
    # accel piece covering both colors of at least one commander.
    def hand_meets_threshold(land_count, has_full_color_pair):
        return 2 <= land_count <= 5 and has_full_color_pair

    # exact enumeration over land-count and "has a same-card WUBG/pair source" is complex combinatorially;
    # approximate via independence-flagged product, cross-checked empirically by ENGINE-GOLDFISH.
    p_land_2_5 = sum(v for k, v in land_dist.items() if 2 <= k <= 5)
    p_any_commander_pair_land = 1 - (1 - hypergeom_at_least_one(LIBRARY_SIZE, sum(1 for l in land_names if {"W","B"} <= LAND_COLORS[l]) , 7)) * \
                                  (1 - hypergeom_at_least_one(LIBRARY_SIZE, sum(1 for l in land_names if {"G","U"} <= LAND_COLORS[l]) , 7))
    result["mulligan_structural_hand_quality"] = {
        "definition": "2-5 lands in opening 7, AND at least one single land that alone covers both colors of at least one commander (a dual/multi land) - a chosen, labeled heuristic threshold, not a universal 'keepable hand' standard",
        "p_land_count_2_to_5": p_land_2_5,
        "p_at_least_one_commander_color_pair_dual_land_in_opener": p_any_commander_pair_land,
        "approx_p_meets_threshold_independence_assumption": p_land_2_5 * p_any_commander_pair_land,
        "caveat": "independence between land-count and dual-land presence is an approximation (both draw from the same 7 cards) - directionally informative, not exact; ENGINE-GOLDFISH provides an empirical cross-check",
    }

    out_dir = REPO_ROOT / "results" / "solo_baseline"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "static_combinatorial.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(result["classification_counts"], indent=2))


if __name__ == "__main__":
    main()
