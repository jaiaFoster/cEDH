"""SIM-DECKBUILD-007 Workstream 4 — role classification of the 99 main-deck cards + role
saturation counts, feeding the final 101st-card cut ranking in the final report.

Primary role only (each card gets exactly one) plus important secondary roles (a card may have
0-2). Classification is a manual, disclosed judgment call (not derived from card text parsing) -
this is the "integrating deliverable" step the assignment itself frames as synthesis, not a new
simulation. Cross-checked against ENGINES/TUTORS/INTERACTION_CASTABLE/ACCELERATION/MANA_SOURCES
where a card is already programmatically classified elsewhere in this project, to keep the two
views consistent.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

ROLES = {
    "mana_acceleration": [
        "Ancient Tomb", "Birds of Paradise", "Chrome Mox", "City of Brass", "City of Traitors",
        "Deathrite Shaman", "Delighted Halfling", "Devoted Druid", "Elvish Spirit Guide",
        "Exotic Orchard", "Gemstone Caverns", "Lotus Petal", "Mana Confluence", "Mana Vault",
        "Mox Amber", "Mox Diamond", "Noble Hierarch", "Sol Ring", "Command Tower", "Dark Ritual",
        "Bayou", "Flooded Strand", "Marsh Flats", "Misty Rainforest", "Polluted Delta", "Savannah",
        "Scalding Tarn", "Scrubland", "Starting Town", "Talon Gates of Madara", "Tropical Island",
        "Tundra", "Underground Sea", "Verdant Catacombs", "Windswept Heath", "Wooded Foothills",
    ],
    "card_engine": [
        "Archivist of Oghma", "Esper Sentinel", "Mystic Remora", "Rhystic Study",
        "Smothering Tithe", "Sylvan Library", "Faerie Mastermind", "Orcish Bowmasters",
        "Runic Armasaur", "The Cabbage Merchant",
    ],
    "mana_engine": [
        "Kinnan, Bonder Prodigy", "Gaea's Cradle", "Badgermole Cub", "Lotho, Corrupt Shirriff",
        "Enduring Vitality", "Seedborn Muse",
    ],
    "tutor_conversion": [
        "Chord of Calling", "Crop Rotation", "Demonic Tutor", "Eldritch Evolution",
        "Enlightened Tutor", "Finale of Devastation", "Imperial Seal", "Nature's Rhythm",
        "Ranger-Captain of Eos", "Spellseeker", "Survival of the Fittest", "Vampiric Tutor",
        "Birthing Pod", "Neoform", "Birthing Ritual",
    ],
    "interaction": [
        "Endurance", "Fierce Guardianship", "Flare of Denial", "Flusterstorm", "Force of Negation",
        "Force of Will", "Mental Misstep", "Mindbreak Trap", "Pact of Negation", "Silence",
        "Subtlety", "Veil of Summer", "Commandeer",
    ],
    "proactive_protection": ["Grand Abolisher", "Talion, the Kindly Lord"],
    "combo_core": [
        "Colossal Skyturtle", "Gilded Drake", "Abhorrent Oculus", "Derevi, Empyrial Tactician",
        "Swift Reconfiguration",
    ],
    "toolbox_clone_utility": [
        "Clever Impersonator", "Sowing Mycospawn", "Hazel's Brewmaster", "Gleaming Splendor",
        "Oboro Breezecaller", "Biomancer's Familiar", "Delney, Streetwise Lookout",
        "Boseiju, Who Endures", "Otawara, Soaring City", "Minamo, School at Water's Edge",
        "Formidable Speaker", "Mockingbird",
    ],
}
# Secondary roles: card -> extra role tags beyond its primary bucket above.
SECONDARY_ROLES = {
    "Gaea's Cradle": ["mana_acceleration"],
    "Kinnan, Bonder Prodigy": ["combo_core"],
    "Fierce Guardianship": ["proactive_protection"],
    "Silence": ["proactive_protection"],
    "Talion, the Kindly Lord": ["card_engine"],
    "Devoted Druid": ["combo_core"],
    "Grand Abolisher": ["mana_acceleration", "card_engine"],
    "Deathrite Shaman": ["card_engine"],  # -2/-2 removal role, real per-Oracle text
    "Birthing Ritual": ["mana_acceleration"],  # marginally, via the creature it finds
    "The Cabbage Merchant": ["mana_engine"],
    "Formidable Speaker": ["tutor_conversion"],
    "Seedborn Muse": ["combo_core"],
    "Orcish Bowmasters": ["interaction"],
}


def main():
    sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
    import deckbuild007_cards as d7
    from deckbuild007_variants import load_deckbuild007_cards
    d7.install_new_card_tables()
    _, rows = load_deckbuild007_cards()
    d7.uninstall_new_card_tables()

    all_role_cards = set()
    counts = {}
    for role, cards in ROLES.items():
        counts[role] = len(cards)
        all_role_cards.update(cards)
    missing = set(rows.keys()) - all_role_cards
    extra = all_role_cards - set(rows.keys())
    assert not missing, f"unclassified real deck cards: {missing}"
    assert not extra, f"classified names that aren't real deck cards: {extra}"
    dupes = [c for role_cards in ROLES.values() for c in role_cards
             if sum(c in v for v in ROLES.values()) > 1]
    assert not dupes, f"cards with more than one PRIMARY role: {set(dupes)}"

    out = {
        "phase": "SIM_DECKBUILD_007_WS4_ROLE_CLASSIFICATION",
        "primary_role_counts": counts,
        "primary_role_lists": ROLES,
        "secondary_roles": SECONDARY_ROLES,
        "role_saturation_note": (
            "mana_acceleration (35 primary, dominated by the mana base itself) and "
            "tutor_conversion (15) are the two deepest categories by raw count, but the mana "
            "base is load-bearing (lands aren't cut candidates in this analysis) - the "
            "MEANINGFULLY saturated, cuttable-without-a-coverage-hole categories are "
            "card_engine (10, six of which are 'passive value engines' with heavy overlap: "
            "Archivist/Esper Sentinel/Mystic Remora/Rhystic Study/Smothering Tithe/Sylvan "
            "Library all independently generate card advantage with no shared dependency) and "
            "tutor_conversion (15, several of which reach overlapping target sets)."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild007_ws4_role_classification.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(counts, indent=2))
    print("total cards classified:", len(all_role_cards))


if __name__ == "__main__":
    main()
