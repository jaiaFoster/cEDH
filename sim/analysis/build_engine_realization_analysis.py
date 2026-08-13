"""SIM-001 MULL-005R section (assignment 2A / t1_t3_trajectory_audit.json REALIZE-001, REALIZE-002)
— engine realization timing analysis.

"Engine quality must account for when value is actually REALIZED, not merely when the permanent
enters." This module answers, PER ENGINE (and per ability, for multi-ability cards), four separate
questions that MULL-005 conflated into a single "engine active" flag:

  1. realization_mechanism  - what Oracle-text condition actually produces the value.
  2. can_trigger_on_opponent_turn - is that condition, by Oracle text alone, something that can
     occur during an OPPONENT's turn (independent of whether opponent behavior is simulated) -
     REALIZE-001's structural flag, e.g. Faerie Mastermind's passive vs its own {3}{U} ability.
  3. can_simulate_realization - can THIS solo/no-opponent Level 1-2 model ever literally confirm
     the value fired, or is it structurally unmeasurable (opponent action required, or a mechanic
     - graveyard abilities, combat - this project doesn't model at all)?
  4. deployment_credited_as_proxy - does the CURRENT grading model (trajectory_grading.py /
     trajectory_metrics.py) credit this ability's tier on deployment/board-presence alone, as a
     disclosed PROXY for real-game value, or does it require an explicit, simulatable support
     condition before any credit at all?

The key finding this module documents (TITHE-001's consistency correction, generalized here): (3)
is False for every opponent-cast/opponent-draw-triggered Tier-A engine (Rhystic/Remora/Tithe/
Sentinel) - none of their triggers can be literally confirmed by a solo model - and yet (4) is True
for all of them, uniformly, as a disclosed proxy (this deck's real value from these cards in an
actual opponent-populated game is not in serious question; the model just cannot literally witness
it turn-by-turn). Tier-C conditional engines get NO such proxy: their tier credit requires an
explicit _tier_c_supported()/_tier_b_supported() check (Faerie Mastermind's {3}{U} ability being
castable NOW, not merely Mastermind being on the battlefield), and TIER_C_STRUCTURALLY_INERT
members (Archivist of Oghma, Runic Armasaur, Heartwood Storyteller, Delney) get NO credit at all,
ever, regardless of board state - their conditions are rare enough (opponent tutors, opponent
activates a non-mana ability, any player casts a noncreature spell, a triggered ability doubling
that also needs combat) that MULL-005's decision to zero them out entirely (rather than proxy-credit
them like Tier A) is preserved unchanged by this phase; this module only makes that asymmetry
EXPLICIT and auditable rather than an implicit consequence of which literal Python branch a card's
name happened to hit.

Every trigger/ability description below is the exact Oracle text pulled from
data/cards_cache/oracle-2026-08-12 for this deck (verified against source, not recalled from
general MTG knowledge) - see oracle_text field on each entry.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ENTRIES = [
    # ---- Tier A: proxy-credited on deployment alone (TITHE-001 consistency correction) --------
    {
        "card": "Rhystic Study", "ability": "primary", "engine_tier": "A",
        "oracle_text": "Whenever an opponent casts a spell, you may draw a card unless that player pays {1}.",
        "realization_mechanism": "opponent_casts_spell",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": True,
        "structurally_inert_in_solo_model": False,
        "notes": "No opponents exist in this solo/goldfish model, so this trigger can never literally fire here. Credited on battlefield presence alone by T2/T3 (grade_trajectory's PREMIUM_DESTINATIONS check) as a disclosed proxy for real-game value - this project's central, honestly-labeled compromise for the deck's whole card-draw-engine suite.",
    },
    {
        "card": "Mystic Remora", "ability": "primary", "engine_tier": "A",
        "oracle_text": "Cumulative upkeep {1}. Whenever an opponent casts a noncreature spell, you may draw a card unless that player pays {4}.",
        "realization_mechanism": "opponent_casts_spell",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": True,
        "structurally_inert_in_solo_model": False,
        "notes": "Also a PREMIUM_ONE_DROP_ENGINE (Tier S if cast T1) - the {4} tax and cumulative upkeep are real long-game costs this T1-T3 model does not track, but the draw trigger itself is proxy-credited identically to Rhystic Study for consistency (TITHE-001).",
    },
    {
        "card": "Esper Sentinel", "ability": "primary", "engine_tier": "A",
        "oracle_text": "Whenever an opponent casts their first noncreature spell each turn, draw a card unless that player pays {X}, where X is this creature's power.",
        "realization_mechanism": "opponent_casts_spell",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": True,
        "structurally_inert_in_solo_model": False,
        "notes": "Also a PREMIUM_ONE_DROP_ENGINE. Unlike Rhystic/Remora the draw is unconditional unless the opponent pays (no 'you may') - a stronger real trigger, not reflected as a magnitude difference anywhere in this model (all Tier-A engines are credited as a flat proxy, not weighted by expected value).",
    },
    {
        "card": "Smothering Tithe", "ability": "primary", "engine_tier": "A",
        "oracle_text": "Whenever an opponent draws a card, that player may pay {2}. If the player doesn't, you create a Treasure token.",
        "realization_mechanism": "opponent_draws_card",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": True,
        "structurally_inert_in_solo_model": False,
        "notes": "MULL-005R TITHE-001 correction: previously zeroed out via TIER_C_STRUCTURALLY_INERT-equivalent treatment (excluded from ENGINE_TIER_A) despite being MECHANICALLY IDENTICAL in opponent-dependence to Rhystic Study. Promoted into ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE so it is now proxy-credited on the same basis as Rhystic/Remora/Sentinel instead of the previous inconsistent zero-credit treatment.",
    },
    {
        "card": "Sylvan Library", "ability": "primary", "engine_tier": "A",
        "oracle_text": "At the beginning of your draw step, you may draw two additional cards. If you do, choose two cards in your hand drawn this turn. For each of those cards, pay 4 life or put the card on top of your library.",
        "realization_mechanism": "controller_draw_step",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": True,
        "deployment_credited_as_proxy": True,
        "structurally_inert_in_solo_model": False,
        "notes": "The ONE Tier-A engine whose trigger is fully self-contained (controller's own draw step, no opponent action required) - can_simulate_realization is True here specifically because nothing about an opponent needs to be known. Ranked above the TIER_C_STRUCTURALLY_INERT cards for exactly this reason (REALIZE-002) even though this model does not currently distinguish Library's higher reliability from Rhystic/Remora/Tithe/Sentinel's proxy-credited-but-unmeasurable status in the tier score itself - both end up Tier A, a known, disclosed granularity limit, not an oversight.",
    },
    # ---- Faerie Mastermind: two abilities, two different realization profiles (REALIZE-001) ---
    {
        "card": "Faerie Mastermind", "ability": "passive_opponent_trigger", "engine_tier": "C",
        "oracle_text": "Whenever an opponent draws their second card each turn, you draw a card.",
        "realization_mechanism": "opponent_draws_second_card_each_turn",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "Structurally identical opponent-dependence to Rhystic/Remora/Tithe, BUT NOT proxy-credited the way those Tier-A engines are: Mastermind is Tier C, and Tier-C credit is gated entirely on _tier_c_supported() finding an explicit, simulatable support condition. This passive ability is not what _tier_c_supported checks for Mastermind (see next entry) - mere battlefield presence never earns Mastermind any tier credit under this ability alone.",
    },
    {
        "card": "Faerie Mastermind", "ability": "activated_ability", "engine_tier": "C",
        "oracle_text": "{3}{U}: Each player draws a card.",
        "realization_mechanism": "controller_activated_instant_speed",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": True,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "This is the ability trajectory_metrics._tier_c_supported actually checks for Mastermind ('its own {3}{U} ability is the only solo-usable line') - fully simulatable (mana payable now), but credit still requires the SUPPORT CHECK to pass (mana available), not mere deployment; a Mastermind on the battlefield with no spare {3}{U} gets zero Tier-C credit, correctly.",
    },
    # ---- TIER_C_STRUCTURALLY_INERT: never credited, any board state, disclosed and unchanged --
    {
        "card": "Archivist of Oghma", "ability": "primary", "engine_tier": "C",
        "oracle_text": "Whenever an opponent searches their library, you gain 1 life and draw a card.",
        "realization_mechanism": "opponent_searches_library",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": True,
        "notes": "'Opponent tutors' is rare enough in a T1-T3 window, and entirely opponent-decision-dependent, that MULL-005's decision to zero it out completely (rather than proxy-credit it like Tier A) is preserved unchanged (REALIZE-002) - not promoted, not demoted, just made explicit.",
    },
    {
        "card": "Runic Armasaur", "ability": "primary", "engine_tier": "C",
        "oracle_text": "Whenever an opponent activates an ability of a creature or land that isn't a mana ability, you may draw a card.",
        "realization_mechanism": "opponent_activates_nonmana_ability",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": True,
        "notes": "Same disclosed-zero treatment as Archivist - genuinely more niche than a spell-cast trigger in most metas, per the assignment's own instruction not to promote these.",
    },
    {
        "card": "Heartwood Storyteller", "ability": "primary", "engine_tier": "C",
        "oracle_text": "Whenever a player casts a noncreature spell, each of that player's opponents may draw a card.",
        "realization_mechanism": "any_player_casts_noncreature_spell",
        "can_trigger_on_opponent_turn": True,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": True,
        "notes": "Symmetric wording ('a player'/'that player's opponents'), but only benefits Heartwood's controller when an OPPONENT casts a noncreature spell - when the controller casts one, it is the OPPONENTS who may draw. Net-negative-leaning for a proactive controller in practice; zeroed out, not modeled as a downside either (disclosed simplification, not a claim of neutrality).",
    },
    {
        "card": "Delney, Streetwise Lookout", "ability": "primary", "engine_tier": "C",
        "oracle_text": "Creatures you control with power 2 or less can't be blocked by creatures with power 3 or greater. If a triggered ability of a creature you control with power 2 or less triggers, that ability triggers an additional time.",
        "realization_mechanism": "combat_and_triggered_ability_dependent_not_modeled",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": True,
        "notes": "Not opponent-dependent at all, unlike the other three TIER_C_STRUCTURALLY_INERT members - it is COMBAT-dependent (evasion clause) and requires a second creature with an actually-relevant triggered ability to double, neither of which this no-combat, no-stack solo model represents. Grouped here because the practical effect (never credited) is identical, even though the structural reason differs from the opponent-action cards above.",
    },
    # ---- Deathrite Shaman: never credited, for a THIRD, distinct reason (not modeled at all) --
    {
        "card": "Deathrite Shaman", "ability": "land_graveyard_mana", "engine_tier": "C",
        "oracle_text": "{T}: Exile target land card from a graveyard. Add one mana of any color. (Activate only as an instant.)",
        "realization_mechanism": "graveyard_activated_ability_not_modeled",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "Not in TIER_C_STRUCTURALLY_INERT (that set is specifically for opponent/combat-dependent conditions) - Deathrite is a THIRD, distinct never-credited case: _tier_c_supported() returns False for it unconditionally, for the documented SOLO-002R reason that graveyard-mana abilities are not modeled in this engine at all (no representation of either player's graveyard contents as a mana source), independent of any opponent or combat dependency.",
    },
    {
        "card": "Deathrite Shaman", "ability": "instant_sorcery_graveyard_drain", "engine_tier": "C",
        "oracle_text": "{B}, {T}: Exile target instant or sorcery card from a graveyard. Each opponent loses 2 life.",
        "realization_mechanism": "graveyard_activated_ability_not_modeled",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "Same not-modeled reason as the land-exile ability above; life-loss also isn't tracked by this engine at all (no life total state).",
    },
    {
        "card": "Deathrite Shaman", "ability": "creature_graveyard_lifegain", "engine_tier": "C",
        "oracle_text": "{G}, {T}: Exile target creature card from a graveyard. You gain 2 life.",
        "realization_mechanism": "graveyard_activated_ability_not_modeled",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": False,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "Same not-modeled reason as the other two Deathrite abilities.",
    },
    # ---- Tier B: state-aware infrastructure, credited only when the support check passes ------
    {
        "card": "Birthing Pod", "ability": "primary", "engine_tier": "B",
        "oracle_text": "{1}{G/P}, {T}, Sacrifice a creature: Search your library for a creature card with mana value equal to 1 plus the sacrificed creature's mana value, put that card onto the battlefield, then shuffle. Activate only as a sorcery.",
        "realization_mechanism": "controller_activated_sorcery_speed",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": True,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "Fully self-contained and fully simulatable (pod_and_battlefield_tutors.try_activate_pod verifies real legality: mana, a sacrificeable creature, sorcery timing). Credited only when _tier_b_supported() finds an actual legal sacrifice body (state.creature_count()>=1), never on mere board presence - Pod with no creature to sacrifice earns zero Tier-B credit, correctly.",
    },
    {
        "card": "Survival of the Fittest", "ability": "primary", "engine_tier": "B",
        "oracle_text": "{G}, Discard a creature card: Search your library for a creature card, reveal that card, put it into your hand, then shuffle.",
        "realization_mechanism": "controller_activated_instant_speed",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": True,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "No sorcery-speed restriction in the real Oracle text (unlike Pod) - activatable on an opponent's turn too, though that distinction doesn't matter for THIS model's T1-T3-on-controller's-turns structure. Credited only when a discardable creature card is actually in hand (state-aware, per SURV-*/assignment section 2D - never scored as 'present = online').",
    },
    {
        "card": "Gaea's Cradle", "ability": "primary", "engine_tier": "B",
        "oracle_text": "{T}: Add {G} for each creature you control.",
        "realization_mechanism": "controller_activated_mana_ability",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": True,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "Fully simulatable and exactly quantifiable (creature_count() at time of tap). Credited only when creature_count()>=2 (a meaningful output), not merely being on the battlefield with 0-1 creatures.",
    },
    {
        "card": "Training Grounds", "ability": "primary", "engine_tier": "B",
        "oracle_text": "Activated abilities of creatures you control cost {2} less to activate. This effect can't reduce the mana in that cost to less than one mana.",
        "realization_mechanism": "static_continuous_cost_reduction",
        "can_trigger_on_opponent_turn": False,
        "can_simulate_realization": True,
        "deployment_credited_as_proxy": False,
        "structurally_inert_in_solo_model": False,
        "notes": "Not a trigger at all - a static, always-on cost reduction, so 'realization timing' doesn't apply the same way; it only has an observable EFFECT in this deck when Thrasios (the only modeled creature with an activated mana cost) is also on the battlefield. Credited only in that co-presence, never on Training Grounds alone (see thrasios_activation_cost_generic).",
    },
]

_ABILITY_LABELS_PER_CARD = {}
for _e in ENTRIES:
    _ABILITY_LABELS_PER_CARD.setdefault(_e["card"], []).append(_e["ability"])


def main():
    counts_by_tier = {}
    for e in ENTRIES:
        counts_by_tier[e["engine_tier"]] = counts_by_tier.get(e["engine_tier"], 0) + 1
    proxy_credited = sum(1 for e in ENTRIES if e["deployment_credited_as_proxy"])
    simulatable = sum(1 for e in ENTRIES if e["can_simulate_realization"])
    opponent_turn_dependent = sum(1 for e in ENTRIES if e["can_trigger_on_opponent_turn"])
    structurally_inert = sum(1 for e in ENTRIES if e["structurally_inert_in_solo_model"])

    md_lines = [
        "# SIM-001 MULL-005R — Engine Realization Timing Analysis",
        "",
        f"{len(ENTRIES)} ability entries across {len(_ABILITY_LABELS_PER_CARD)} cards. "
        f"{proxy_credited} proxy-credited on deployment alone, {simulatable} fully simulatable, "
        f"{opponent_turn_dependent} can trigger on an opponent's turn per Oracle text, "
        f"{structurally_inert} structurally inert in this solo model (never credited, any board state).",
        "",
        "Central finding (TITHE-001 generalized): opponent-dependence alone does NOT predict "
        "whether a card is credited. Every Tier-A engine (Rhystic/Remora/Tithe/Sentinel) is "
        "opponent-cast/opponent-draw triggered, unmeasurable by this solo model, and yet proxy-"
        "credited on deployment alone - deliberately and disclosed, not an oversight. Tier-C "
        "engines with the SAME opponent-dependence (Faerie Mastermind's passive, Archivist, "
        "Armasaur, Heartwood) get NO such proxy; their credit (if any) requires an explicit, "
        "currently-simulatable support condition instead, and four of them "
        "(TIER_C_STRUCTURALLY_INERT) get none at all, ever.",
        "",
        "| Card | Ability | Tier | Mechanism | Opp-turn? | Simulatable? | Proxy-credited? | Inert? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in ENTRIES:
        md_lines.append(
            f"| {e['card']} | {e['ability']} | {e['engine_tier']} | {e['realization_mechanism']} | "
            f"{e['can_trigger_on_opponent_turn']} | {e['can_simulate_realization']} | "
            f"{e['deployment_credited_as_proxy']} | {e['structurally_inert_in_solo_model']} |"
        )
    md_lines.append("")
    for e in ENTRIES:
        md_lines.append(f"## {e['card']} — {e['ability']}")
        md_lines.append(f"**Oracle text:** {e['oracle_text']}")
        md_lines.append(f"**Notes:** {e['notes']}")
        md_lines.append("")

    out_json = REPO_ROOT / "results" / "solo_baseline" / "engine_realization_analysis.json"
    out_md = REPO_ROOT / "results" / "solo_baseline" / "engine_realization_analysis.md"
    out_json.write_text(json.dumps({
        "subject_deck_hash": "4edee0fc60768fcd759a2e9fd3c34277d9d37c0d6a27a663ea7beff76b05e20a",
        "subject_deck_version": "tymna-thrasios-treefarm-v1",
        "entry_count": len(ENTRIES),
        "counts_by_tier": counts_by_tier,
        "proxy_credited_count": proxy_credited,
        "simulatable_count": simulatable,
        "opponent_turn_dependent_count": opponent_turn_dependent,
        "structurally_inert_count": structurally_inert,
        "entries": ENTRIES,
    }, indent=2) + "\n", encoding="utf-8")
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(counts_by_tier)


if __name__ == "__main__":
    main()
