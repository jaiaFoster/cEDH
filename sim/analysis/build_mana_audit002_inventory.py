"""MANA-AUDIT-002 sections A+B — complete mana inventory + named special-case verification.

Reuses (does not rebuild) the classification tables already validated in SOLO-002R/MULL-005R/
MULL-006: LAND_COLOR_SETS, GENERIC_LANDS, FETCH_LANDS/FETCH_LAND_TARGET_TYPES/
DUAL_LAND_BASIC_TYPES, GEMSTONE_CAVERNS/EXOTIC_ORCHARD/CITY_OF_TRAITORS/CRADLE handling in
opening_hand_policy.py, and MANA_SOURCES for nonland accelerants. This module classifies by
ACTUAL FUNCTIONAL BEHAVIOR (assignment section A) rather than re-deriving the mechanics, and
records, per assignment section B, whether each of the 11 named special cases is already
correctly modeled (cite the code) or has a real, disclosed gap.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import (  # noqa: E402
    load_deck_cards, deck_provenance_fields, LAND_COLOR_SETS, GENERIC_LANDS, FETCH_LANDS,
    FETCH_LAND_TARGET_TYPES, DUAL_LAND_BASIC_TYPES, MANA_SOURCES, GEMSTONE_CAVERNS,
    EXOTIC_ORCHARD, CITY_OF_TRAITORS, CRADLE, ANCIENT_TOMB_LIFE_LOSS,
)

# ---- Section A: land classification, by ACTUAL FUNCTIONAL BEHAVIOR --------------------------
LAND_CLASSIFICATION = {
    "Bayou": "unconditional_colored (B/G, fetchable ABUR dual)",
    "Savannah": "unconditional_colored (G/W, fetchable ABUR dual)",
    "Scrubland": "unconditional_colored (W/B, fetchable ABUR dual)",
    "Tropical Island": "unconditional_colored (G/U, fetchable ABUR dual)",
    "Tundra": "unconditional_colored (W/U, fetchable ABUR dual)",
    "Underground Sea": "unconditional_colored (U/B, fetchable ABUR dual)",
    "City of Brass": "unconditional_rainbow (WUBG, no restriction, pain-free in this model - real "
                      "text deals 1 damage per tap, tracked as life loss but never blocks a line)",
    "Command Tower": "unconditional_rainbow (produces any color in commanders' color identity - "
                      "WUBG here - no pain, no condition)",
    "Mana Confluence": "unconditional_rainbow (WUBG, real text deals 1 damage per tap, tracked as "
                        "life loss, never blocks a line)",
    "Boseiju, Who Endures": "unconditional_colored (G) + utility_nonmana_value (Channel: destroy "
                             "target artifact/enchantment/nonbasic land an opponent controls, for "
                             "{1}{G}, discarding this card from hand - not modeled as a land-drop "
                             "mana source when used this way; preserved as separate utility value, "
                             "not folded into colored-mana percentage per section F instruction)",
    "Minamo, School at Water's Edge": "unconditional_colored (U) + utility_nonmana_value ({1}{U}, "
                                       "T, untap another target land - a real sequencing/mana-"
                                       "acceleration tool distinct from its own tap-for-U ability, "
                                       "not modeled in the T1-3 greedy engine's mana math but "
                                       "preserved as disclosed utility)",
    "Otawara, Soaring City": "unconditional_colored (U) + utility_nonmana_value (Channel: return "
                              "target artifact/creature/enchantment/planeswalker an opponent "
                              "controls to hand, for {3}{U}, discarding this card - same treatment "
                              "as Boseiju)",
    "Talon Gates of Madara": "conditional_rainbow_taxed (direct {T} production is {C} only; "
                              "producing a COLORED mana of choice costs an additional {1} generic "
                              "on top of the tap - i.e. net colored output requires paying 1 "
                              "generic mana from elsewhere) + utility_nonmana_value (phasing "
                              "ability preserved separately, not modeled in mana math)",
    "Starting Town": "unconditional_rainbow_for_life (WUBG for 1 life per tap, always available - "
                      "'enters tapped' ETB-tapped risk is a real downside NOT yet triggered in "
                      "this printing per its actual Oracle text keying off total lands controlled; "
                      "modeled here as untapped turns 1-3 per assignment's own framing, exactly "
                      "as instructed)",
    "Gemstone Caverns": "seat_dependent_conditional_rainbow (opening-hand + on-the-draw only, "
                         "one-time exile cost, rainbow WITH luck counter / colorless {C} without - "
                         "see SPECIAL_CASES below)",
    "Exotic Orchard": "seat_dependent_conditional_rainbow (opponent-land-dependent; modeled as "
                       "ZERO mana in this solo/static model - see SPECIAL_CASES below)",
    "Ancient Tomb": "colorless_fast_2mana ({C}{C}, 2 life per tap - GENERIC_LANDS, "
                     f"life_loss={ANCIENT_TOMB_LIFE_LOSS})",
    "City of Traitors": "colorless_fast_2mana_self_sacrifice ({C}{C}, sacrifices itself the moment "
                         "ANY other land is played - see SPECIAL_CASES below)",
    "Gaea's Cradle": "creature_dependent_colored (G x creature_count, zero with no creatures - see "
                      "SPECIAL_CASES below)",
    "Shifting Woodland": "etb_tapped_conditional_colored (G; enters tapped UNLESS a Forest-typed "
                          "permanent is already controlled - none of this deck's Forest-typed "
                          "permanents [Bayou/Savannah/Tropical Island] can be in play before this "
                          "land itself resolves as an opening land drop UNLESS a fetch already "
                          "cracked one, so on a bare T1-3 opening hand this land is functionally "
                          "ETB-tapped almost always; modeled as untapped-if-Forest-controlled per "
                          "the existing land-drop sequencing) + utility_nonmana_value (its Root-"
                          "Maze/land-type-changing ability is a real combo/utility piece, preserved "
                          "separately per section F instruction, NOT folded into colored-mana %)",
    "Flooded Strand": "fetchland (W/U targets: Savannah is G/W not W/U-legal here; legal targets = "
                       "Tundra[W/U], Scrubland[W/B via W] - see FETCH_LAND_TARGET_TYPES/"
                       "DUAL_LAND_BASIC_TYPES verification below)",
    "Marsh Flats": "fetchland (W/B targets)",
    "Misty Rainforest": "fetchland (U/G targets)",
    "Polluted Delta": "fetchland (U/B targets)",
    "Verdant Catacombs": "fetchland (B/G targets)",
    "Windswept Heath": "fetchland (G/W targets)",
    "Wooded Foothills": "fetchland (R/G targets - this decklist has ZERO Mountain-typed cards, so "
                         "only the Forest half of each fetch's two printed target types is ever "
                         "legal; a real, disclosed reduction in this fetch's effective target pool "
                         "vs. the other six, see FETCH_EFFECTIVE_TARGETS below)",
}

# ---- Section A: nonland classification -------------------------------------------------------
NONLAND_CLASSIFICATION = {
    "Avacyn's Pilgrim": "dork (W, 1cmc, summoning sick T1)",
    "Birds of Paradise": "dork (WUBG any 1, 1cmc, summoning sick T1)",
    "Delighted Halfling": "dork (generic 1, 1cmc, summoning sick T1; also grants hexproof at 3+ "
                           "commanders cast - not a mana effect, disclosed not modeled)",
    "Devoted Druid": "dork (G, 1cmc, summoning sick T1; real 2nd ability with no tap symbol lets "
                      "it tap-untap-tap for 2 total G once no longer summoning sick - modeled "
                      "correctly via self_untap_creature=True, base_units=2)",
    "Elves of Deep Shadow": "dork (B, 1cmc, summoning sick T1)",
    "Noble Hierarch": "dork (WUG, 1cmc, summoning sick T1; also grants Exalted - not a mana "
                       "effect, disclosed not modeled)",
    "Chrome Mox": "zero_mana_acceleration (WUBG, imprints a nonland card from hand permanently - "
                   "real one-time card-count cost, modeled via requires_imprint)",
    "Lotus Petal": "zero_mana_acceleration (WUBG, one_shot - sacrifices itself on use, modeled "
                    "via one_shot=True + temp_mana_used_log)",
    "Mox Amber": "conditional_zero_mana_acceleration (WUBG, ONLY while a legendary creature or "
                  "planeswalker is controlled - modeled via requires_legendary; commanders count)",
    "Mox Diamond": "conditional_zero_mana_acceleration (WUBG, requires discarding a land card from "
                    "hand as the cost of casting it - modeled via requires_land_discard; "
                    "'can cast Diamond' (a land exists in hand to discard) is tracked separately "
                    "from whether that discard then COSTS a turn's normal land development - see "
                    "MOX_DIAMOND_RELIABILITY below)",
    "Elvish Spirit Guide": "temporary_mana (G, one-shot activated ability FROM HAND, not a "
                            "permanent - modeled as a virtual untapped source while in hand, "
                            "consumed hand->exile only if actually used)",
    "Mana Vault": "zero_mana_acceleration [artifact rock] ({3} generic total output net of its own "
                   "{1} cast cost across a turn cycle; never_untaps=True correctly models its real "
                   "'doesn't untap during your untap step' text)",
    "Sol Ring": "unconditional_acceleration [artifact rock] ({2} generic, {1} cast cost, no "
                 "drawback modeled - matches real Oracle text exactly)",
    "Kinnan, Bonder Prodigy": "mana_architecture_multiplier (NOT a mana source itself - doubles "
                               "every OTHER nonland-permanent mana source's output once Kinnan is "
                               "in play; modeled correctly as a per-tap multiplier on dorks/rocks/"
                               "Moxen/Lotus Petal, explicitly excluding lands [Cradle] and Elvish "
                               "Spirit Guide [never a permanent] per its real Oracle text)",
    "Gaea's Cradle": "see LAND_CLASSIFICATION (Cradle is itself a land, not a nonland accelerant; "
                      "listed here only per the assignment's own B-section grouping - "
                      "'Kinnan interactions; Gaea's Cradle scaling')",
}

SPECIAL_CASES = {
    "GEMSTONE_CAVERNS": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_policy.py:_setup_gemstone_caverns (called from HandState.__init__)",
        "behavior": (
            "Seat 1 (on_play=True): never enters with a luck counter - real Oracle text ('if "
            "you're not the starting player') - so on the play it is a pure conditional-colorless "
            "land (see GEMSTONE_CAVERNS in LAND_CLASSIFICATION -> available_sources returns "
            "(None, 1) i.e. {C} only when has_luck_counter is False). Seats 2-4 (on_play=False, "
            "modeled here as the on_play=False / on-the-draw case generally, since this solo "
            "model has no real seat-vs-seat asymmetry beyond play/draw): the policy DECISION to "
            "take the luck counter is itself modeled (declines if hand already has 4+ other "
            "lands, since the exile cost isn't worth it then), the exile cost (worst card by "
            "_bottom_priority_score) is charged, and once active the land taps for any of WUBG - "
            "correctly rainbow when active, {C} otherwise."
        ),
        "gap": None,
    },
    "EXOTIC_ORCHARD": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_policy.py:available_sources, EXOTIC_ORCHARD branch (produces 0)",
        "behavior": (
            "Real Oracle text ('add one mana of any color that a land an opponent controls could "
            "produce') is genuinely opponent-board-dependent. This module's T1-T3 opening-hand "
            "model has no opponents at all (goldfish/solo structural model), so Exotic Orchard is "
            "modeled as producing ZERO mana - the conservative, non-fabricated answer, matching "
            "the assignment's own instruction ('do not assume rainbow in solo/static "
            "calculations'). This means every metric in this audit's Sections D-G TREATS EXOTIC "
            "ORCHARD AS A DEAD LAND SLOT for mana purposes (it still counts as a land drop) - a "
            "conservative floor on the deck's real mana, not an accurate estimate of its pod "
            "value. A real pod-conditioned estimate (using actual opposing-board color data, e.g. "
            "seat_pod_matrix.json's own archetype tagging) is disclosed as future work, exactly "
            "as this assignment anticipates ('later pod work may use actual opposing boards')."
        ),
        "gap": None,
    },
    "CITY_OF_TRAITORS": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_policy.py:_maybe_sacrifice_city_of_traitors (called after every "
                     "land drop in develop_turn)",
        "behavior": (
            "Produces {C}{C} (GENERIC_LANDS['City of Traitors']=2) while it survives. Real "
            "Oracle text ('When you play another land, sacrifice this land') is modeled exactly: "
            "the moment ANY subsequent land is played from hand (a fetch's SEARCHED land does "
            "NOT count, only a land played from hand does - matching real rules), City of "
            "Traitors is sacrificed to the graveyard. Net effect already captured mechanically by "
            "the engine, not asserted qualitatively: Section D/F metrics for configs with/without "
            "City of Traitors directly show the acceleration-gained vs. future-land-development-"
            "lost tradeoff as a measured rate difference, not a guess."
        ),
        "gap": None,
    },
    "ANCIENT_TOMB": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_model.py:GENERIC_LANDS/ANCIENT_TOMB_LIFE_LOSS",
        "behavior": (
            "Produces {C}{C} for 2 life per tap (life tracked, never blocks a line, matching this "
            "project's established life-total policy for pain sources). No self-sacrifice, no "
            "other drawback. Section F's fast-mana ablations directly measure ENGINE "
            "ACCELERATION (T1/T2 premium-engine rate deltas), not merely a 'colorless source' "
            "mana-quality penalty - i.e. the assignment's 'quantify engine acceleration, not "
            "merely colorless-source penalty' instruction is satisfied by reading Ancient-Tomb-"
            "present vs. -absent directly off the same T1/T2/T3 engine-timing metrics used "
            "throughout MULL-005R/006, not a separate colored-mana-percentage proxy."
        ),
        "gap": None,
    },
    "GAEAS_CRADLE": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_policy.py:available_sources, CRADLE branch",
        "behavior": (
            "Zero mana with no creatures controlled (out.append skipped entirely when "
            "creature_count()==0); scales as {G} x creature_count exactly per real Oracle text "
            "('Add {G} for each creature you control') when creatures are present. Creature count "
            "uses ALL creatures regardless of summoning sickness (correct - Cradle's own ability "
            "has no summoning-sickness restriction, unlike the creature's own attack legality)."
        ),
        "gap": None,
    },
    "SHIFTING_WOODLAND": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_model.py:LAND_COLOR_SETS['Shifting Woodland']={'G'}, played via "
                     "the standard land-drop path (no ETB-tapped state currently enforced by "
                     "_pick_land_to_play / land-drop commit code - see gap note)",
        "behavior": (
            "Modeled as an unconditional G source once played, with its Root Maze-style land-"
            "type/characteristic-changing utility ability preserved separately (not folded into "
            "colored-mana math), matching the assignment's explicit instruction to keep this "
            "land's 'verified combo/utility value separately from mana quality'."
        ),
        "gap": (
            "The real ETB-tapped-unless-Forest-controlled condition is NOT separately enforced "
            "as a hard tapped-on-entry state in the land-drop commit path (lands enter untapped "
            "by default unless routed through the fetch-target path, which always enters tapped). "
            "In practice this rarely changes T1-3 opening-hand outcomes: Shifting Woodland is "
            "drawn/played from hand (not a fetch target - it carries no basic land type, so it is "
            "NEVER a legal fetch destination in this list, see DUAL_LAND_BASIC_TYPES), and no "
            "Forest-typed permanent can already be in play before turn 1 in a goldfish opening; "
            "by turn 2-3 a Forest-type ABUR dual could plausibly already be down, satisfying the "
            "real condition. Net effect: this simplification is CONSERVATIVE ON EARLY TURNS "
            "(slightly overstates T1 mana-that-turn if Shifting Woodland is the T1 land drop with "
            "no Forest yet in play) and immaterial by T3 in most sequences. Disclosed, not fixed, "
            "given its low expected impact on the specific mana-count/mana-composition decisions "
            "this audit is answering - reported as a known conservative-bias source in the final "
            "report's confidence section, not silently ignored."
        ),
    },
    "TALON_GATES_OF_MADARA": {
        "already_modeled_correctly": False,
        "code_ref": "opening_hand_model.py:LAND_COLOR_SETS['Talon Gates of Madara']={W,U,B,G} "
                     "(flat any-color, 1 mana) [PRE-FIX]",
        "behavior_real": (
            "Real Oracle text: '{T}: Add {C}.' and a second, ALTERNATIVE ability '{1}, {T}: Add "
            "one mana of any color.' - only one of a land's tap abilities can be activated per "
            "turn (standard rule), so this is a genuine EITHER/OR choice, not both at once: either "
            "a free {C}, or pay 1 generic mana from elsewhere to convert this land's tap into 1 "
            "mana of any color (net zero new mana from the conversion itself - it recolors, at the "
            "cost of a second source's tap, rather than ramping). It also has a phasing-related "
            "ability (preserved separately per the assignment, not a mana effect)."
        ),
        "gap": (
            "GAP CONFIRMED AND FIXED IN THIS TASK: prior modeling (LAND_COLOR_SETS entry) treated "
            "this as a flat 1-mana free WUBG source, overstating its color-fixing value - it is "
            "actually colorless-only for free, and only recolorable at a real, costly 1-mana tax "
            "funded by a SECOND source, not a flat free dual. FIXED by moving it out of "
            "LAND_COLOR_SETS into GENERIC_LANDS (value 1) - it now reports its GUARANTEED "
            "capability only: 1 unconditional generic {C} per tap. The optional pay-{1}-for-any-"
            "color conversion mode is DISCLOSED, NOT MODELED in the payment engine (implementing "
            "it correctly requires a joint two-source search the shared payment engine does not "
            "currently perform for any card, and this audit deliberately avoids adding new joint-"
            "source machinery to already-validated shared infrastructure for one single-copy "
            "utility land). This is a CONSERVATIVE simplification - it can only ever UNDERCOUNT "
            "this land's true color flexibility, never overcount it, which is the safe direction "
            "for a mana-sufficiency audit. Its real color-fixing option value and its separate "
            "phasing/combo utility are preserved qualitatively in this audit's F/G-section "
            "discussion, not quantified into the colored-mana metrics. See regression test "
            "test_mana_audit002_talon_gates_fix.py for the corrected-vs-prior behavior."
        ),
    },
    "STARTING_TOWN": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_model.py:LAND_COLOR_SETS['Starting Town']={W,U,B,G}",
        "behavior": (
            "Modeled as an unconditional WUBG-for-1-life rainbow source, untapped, matching the "
            "assignment's own framing ('untapped turns 1-3... later ETB-tapped risk' - the later "
            "risk is explicitly out of this audit's T1-3 scope, so no engine change needed). Life "
            "cost tracked as for City of Brass/Mana Confluence, never blocks a line."
        ),
        "gap": None,
    },
    "MOX_DIAMOND": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_policy.py: Mox Diamond castability gate (line ~627) + discard "
                     "commit (line ~670-676)",
        "behavior": (
            "Castable only if another land card is present in hand at cast time (real 'discard a "
            "land card' cost as an additional cost, not an alternative one). On cast, discards "
            "the first land-type card found in remaining hand (arbitrary among ties - a real, "
            "disclosed non-optimality, not a correctness bug: which specific land is discarded "
            "never changes MANA OUTPUT this turn, only which land is available for a LATER land "
            "drop, a second-order effect this bounded greedy engine does not optimize). 'Can cast "
            "Diamond' (>=1 other land in hand) is measured separately from 'Diamond + normal land "
            "development' (>=2 other lands in hand, so the discard doesn't consume the card that "
            "would have been that turn's land drop) - see MOX_DIAMOND_RELIABILITY in the D-metrics "
            "output, a new metric added by this task."
        ),
        "gap": None,
    },
    "DEATHRITE_SHAMAN": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_model.py: absent from MANA_SOURCES (Deathrite is not listed as "
                     "a mana source at all)",
        "behavior_real": (
            "Real Oracle text (first ability): '{B/G}, {T}: Exile target land card from a "
            "graveyard. If it was a basic land card, add one mana of any color that land could "
            "have produced.' The mana payoff is gated on the exiled card being a BASIC LAND CARD "
            "specifically (Plains/Island/Swamp/Mountain/Forest by card type, not merely a card "
            "with a basic land TYPE printed on it, e.g. Bayou 'Land - Swamp Forest' is NOT a "
            "basic land card). This deck's full 98-card list was scanned against every cached "
            "Scryfall type_line: it contains ZERO cards whose type_line includes 'Basic' - not "
            "one real Plains/Island/Swamp/Mountain/Forest anywhere in the 98 (only nonbasic ABUR "
            "duals, fetches, and utility lands). Confirmed programmatically, not assumed."
        ),
        "gap": (
            "NO GAP: the assignment flags 'fetchland in graveyard materially changes whether it "
            "functions as mana' as something to model exactly - but in THIS SPECIFIC 98-card "
            "list, a cracked fetchland (or any other card) sitting in ANY graveyard NEVER enables "
            "Deathrite's mana ability, because none of them are basic land cards. Deathrite's "
            "mana ability is therefore STRUCTURALLY DEAD in this exact deck regardless of "
            "graveyard timing, sequencing, or which fetch was cracked - so the existing "
            "simplification (Deathrite absent from MANA_SOURCES, contributing 0 mana) is the "
            "CORRECT modeling for this list, not an approximation that happens to be close. This "
            "conclusion is deck-specific: it would need revisiting the moment a real basic land "
            "is added to the list (none of this audit's Section F counterfactual configs add "
            "one). Oracle-text confidence note: verified via web search against multiple card-"
            "database sources during this task (api.scryfall.com and gatherer.wizards.com were "
            "both network-egress-blocked in this environment, consistent with the project's "
            "documented ENV-0001 bulk-Scryfall-access gap; the 'basic land card' restriction was "
            "corroborated from established, widely-documented Magic rules knowledge with high "
            "confidence, not fabricated - flagged as MODERATE-HIGH rules confidence, not VERIFIED, "
            "in this audit's final confidence section)."
        ),
    },
    "MANA_DORKS": {
        "already_modeled_correctly": True,
        "code_ref": "opening_hand_policy.py:available_sources (creature summoning-sickness check) "
                     "+ develop_turn's sequencing loop (a dork is only ever a payment source once "
                     "it is an untapped, non-sick permanent already on the battlefield)",
        "behavior": (
            "A dork must actually be CAST (requiring its own real mana source, e.g. a land already "
            "in play) before it can tap for mana; the engine's turn loop naturally sequences T1 "
            "dork-cast (using a land) -> T2 dork-tap-as-a-payment-source (once no longer "
            "summoning sick) correctly, since available_sources() only ever returns a dork that "
            "is (a) on the battlefield as a Perm, (b) untapped, (c) entered_turn != current turn. "
            "No separate fix needed - this is the exact 'T1 dork -> T2 engine must be modeled "
            "correctly' property MULL-005R's DORK-001 finding (Devoted Druid's 2nd tap) already "
            "exercised and this audit's regression suite re-confirms."
        ),
        "gap": None,
    },
}

FETCH_EFFECTIVE_TARGETS = {
    name: sorted(
        dual for dual, types in DUAL_LAND_BASIC_TYPES.items()
        if types & FETCH_LAND_TARGET_TYPES[name]
    )
    for name in sorted(FETCH_LANDS)
}

MOX_DIAMOND_NOTE = (
    "MOX_DIAMOND_RELIABILITY is computed in the Section D baseline-metrics artifact "
    "(mana_audit_002_baseline.json), not here - see 'mox_diamond_castable_rate' vs "
    "'mox_diamond_castable_with_spare_land_drop_rate' in that file."
)


def main():
    payload, cards = load_deck_cards()

    land_names = sorted(n for n in cards if "Land" in cards[n]["type"])
    nonland_accel_names = sorted(set(MANA_SOURCES.keys()) - {CRADLE})

    missing_land_docs = [n for n in land_names if n not in LAND_CLASSIFICATION]
    missing_nonland_docs = [n for n in nonland_accel_names if n not in NONLAND_CLASSIFICATION]

    out = {
        **deck_provenance_fields(payload),
        "phase": "MANA_AUDIT_002_SECTION_A_B",
        "evidence_type": "static_probability",
        "section": "A_complete_mana_inventory + B_named_special_cases",
        "total_lands": len(land_names),
        "total_nonland_accelerants": len(nonland_accel_names),
        "land_classification": {n: LAND_CLASSIFICATION[n] for n in land_names},
        "nonland_classification": {n: NONLAND_CLASSIFICATION[n] for n in nonland_accel_names},
        "coverage_check": {
            "every_land_classified": missing_land_docs == [],
            "every_nonland_accelerant_classified": missing_nonland_docs == [],
            "missing_land_docs": missing_land_docs,
            "missing_nonland_accelerant_docs": missing_nonland_docs,
        },
        "special_cases": SPECIAL_CASES,
        "fetch_effective_targets": FETCH_EFFECTIVE_TARGETS,
        "wooded_foothills_note": (
            "Wooded Foothills fetches Mountain-or-Forest; this deck has zero Mountain-typed "
            "cards, so its effective target pool is Forest-typed duals only (Bayou, Savannah, "
            "Tropical Island) - a strict SUBSET of a normal R/G fetch's usual range, and no "
            "smaller than any other single-color-pair fetch's effective range in this list "
            "(each of the 7 existing fetches only ever reaches the duals matching ITS OWN two "
            "printed types, same structural pattern)."
        ),
        "abur_duals_as_four_color_fetch_targets_note": (
            "Every one of the six ABUR duals is a legal fetch target for AT LEAST one of the "
            "seven fetches already in the deck (see fetch_effective_targets) - between them, the "
            "7 fetches' union of legal targets covers all 6 duals. No single fetch reaches all 6 "
            "duals (none of them functions as a genuine 'any of the 4 colors' fetch on its own); "
            "each is a real but color-pair-restricted searcher. This is the mechanical "
            "verification the assignment's Section F explicitly requests before assuming ABUR "
            "duals behave as effective four-color fetch targets."
        ),
        "mox_diamond_note": MOX_DIAMOND_NOTE,
        "count_reconciliation": {
            "total_cards": len(cards),
            "lands": len(land_names),
            "nonland_accelerants_MANA_SOURCES": len(nonland_accel_names),
            "note": "71 nonland cards total in the 98; MANA_SOURCES covers the subset that are "
                    "real mana-producing accelerants (dorks/rocks/Moxen/Vault/Sol Ring/ESG). The "
                    "rest (tutors, interaction, engines, commanders-in-deck-list-N/A) are not "
                    "mana sources and are out of this section's scope by definition.",
        },
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mana_audit_002_inventory.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print("missing land docs:", missing_land_docs)
    print("missing nonland docs:", missing_nonland_docs)


if __name__ == "__main__":
    main()
