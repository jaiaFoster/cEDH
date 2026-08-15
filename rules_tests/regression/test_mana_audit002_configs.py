"""MANA-AUDIT-002 sections E+F — config table integrity checks (cheap, no simulation)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_mana_audit002_configs import CONFIGS, PROXY_LAND, _install_proxy_land  # noqa: E402
from mana_audit002_variants import all_cards_dict, build_variant  # noqa: E402
from build_mana_audit002_baseline import load_manaaudit_deck_cards  # noqa: E402

_PAYLOAD, BASE_CARDS = load_manaaudit_deck_cards()
CARDS_POOL = all_cards_dict(BASE_CARDS)
_install_proxy_land(CARDS_POOL)
BASE_NAMES = list(BASE_CARDS.keys())


def test_every_config_hits_its_declared_deck_size_and_land_count():
    for name, spec in CONFIGS.items():
        variant = build_variant(BASE_NAMES, CARDS_POOL, add=spec["add"], remove=spec["remove"])
        assert len(variant) == spec["deck_size"], name
        land_ct = sum(1 for n in variant if "Land" in CARDS_POOL[n]["type"])
        assert land_ct == spec["land_count"], name


def test_baseline_config_is_the_real_unmodified_98():
    variant = build_variant(BASE_NAMES, CARDS_POOL, add=[], remove=[])
    assert sorted(variant) == sorted(BASE_NAMES)


def test_only_land_count_configs_change_deck_size():
    for name, spec in CONFIGS.items():
        if spec["deck_size"] != 98:
            assert name[0] in ("J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"), name


def test_run_config_mulligan_sim_actually_uses_the_variant_card_pool_not_the_full_shared_pool():
    """Regression for a real bug this task found: run_policy() derives its own draw pool via
    list(cards.keys()) internally, so passing the full shared cards_pool (rather than a dict
    restricted to the variant's own card names) made every config's mulligan sim silently draw
    from every variant's cards at once - every config came back byte-identical on the first run.
    """
    import random
    from build_mana_audit002_configs import run_config

    seed = 999
    baseline = run_config("A_CURRENT_27", CONFIGS["A_CURRENT_27"], BASE_NAMES, CARDS_POOL, 60, 40, seed)
    ablated = run_config("O_FASTMANA_NEITHER", CONFIGS["O_FASTMANA_NEITHER"], BASE_NAMES, CARDS_POOL, 60, 40, seed)
    # Different card pools drawing from the SAME seed must not collapse to identical mulligan
    # stats - if they do, the draw pool isn't actually varying by config again.
    assert (
        baseline["mulligan_gated_model"]["mulligan_distribution"]
        != ablated["mulligan_gated_model"]["mulligan_distribution"]
        or baseline["mulligan_gated_model"]["tier_distribution"]
        != ablated["mulligan_gated_model"]["tier_distribution"]
    )
