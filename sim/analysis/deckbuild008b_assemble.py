"""SIM-DECKBUILD-008b — assemble machine-readable artifacts from deckbuild008b_work/*.json."""
from __future__ import annotations

import csv
import json
import math

import build_deckbuild008b_experiments as bx
import deckbuild008b_analysis as an

OUT = bx.OUT
PKG_CARDS = [bx.ORACLE, bx.CONSULT, bx.PACT, bx.SEEKER]
COMPARATORS = [an.HAZEL, an.OBORO, an.SWIFT, an.EFFIGY, an.DRUID, an.BOWMASTERS, an.MASTERMIND,
               "Gilded Drake", bx.STORM, bx.SKY, "Imperial Seal", "Demonic Tutor", "Enlightened Tutor",
               "Crop Rotation", "Birthing Pod"]


def _load(name):
    try:
        return bx.load(name)
    except FileNotFoundError:
        return {}


def pool_reps(per_rep):
    """Pool replicate summaries: value = mean of reps; paired delta = mean of rep deltas with
    SE = sqrt(sum se^2)/R; consistency z = (rep0 - rep1) / sqrt(se0^2 + se1^2)."""
    reps = [per_rep[k] for k in sorted(per_rep)]
    out = {"replicates": len(reps), "n_total": sum(r["n"] for r in reps), "n_by_replicate": [r["n"] for r in reps]}
    for m, row in reps[0].items():
        if not isinstance(row, dict) or "value" not in row:
            continue
        ns = [r["n"] for r in reps]
        N = sum(ns)
        vals = [r[m]["value"] for r in reps]
        o = {"value": round(sum(n * v for n, v in zip(ns, vals)) / N, 5), "by_replicate": vals}
        if "delta_vs_ref" in row:
            ds = [r[m]["delta_vs_ref"] for r in reps]
            ses = [r[m]["delta_se"] for r in reps]
            pooled = sum(n * d for n, d in zip(ns, ds)) / N
            o["delta_vs_ref"] = round(pooled, 5)
            o["delta_se"] = round(math.sqrt(sum((n * s) ** 2 for n, s in zip(ns, ses))) / N, 5)
            o["delta_by_replicate"] = ds
            # heterogeneity across replicates: chi-square of replicate deltas around the pooled delta
            if len(ds) >= 2 and all(ses):
                q = sum(((d - pooled) / s) ** 2 for d, s in zip(ds, ses))
                o["replicate_heterogeneity_Q"] = round(q, 2)
                o["replicate_df"] = len(ds) - 1
        out[m] = o
    out["first_win_family_counts"] = {}
    for r in reps:
        for f, c in r.get("first_win_family_counts", {}).items():
            out["first_win_family_counts"][f] = out["first_win_family_counts"].get(f, 0) + c
    out["focus_card_quality_rep0"] = reps[0].get("focus_card_quality")
    out["dead_opening_draw_rep0"] = reps[0].get("dead_opening_draw")
    # pool the per-card quality across replicates by weighted average of rates
    fq = {}
    for r in reps:
        for card, turns in (r.get("focus_card_quality") or {}).items():
            for t, d in turns.items():
                acc = fq.setdefault(card, {}).setdefault(t, {"n_held": 0, "material": 0.0, "secondary_only": 0.0,
                                                              "stranded": 0.0, "roles": {}})
                n = d["n_held"]
                acc["n_held"] += n
                for k in ("material", "secondary_only", "stranded"):
                    acc[k] += d[k] * n
                for rk, rv in d["roles"].items():
                    acc["roles"][rk] = acc["roles"].get(rk, 0.0) + rv * n
    for card, turns in fq.items():
        for t, acc in turns.items():
            n = acc["n_held"] or 1
            for k in ("material", "secondary_only", "stranded"):
                acc[k] = round(acc[k] / n, 4)
            acc["roles"] = {k: round(v / n, 4) for k, v in sorted(acc["roles"].items())}
    out["focus_card_quality"] = fq
    dd = {}
    for r in reps:
        for card, rows in (r.get("dead_opening_draw") or {}).items():
            for lab, d in rows.items():
                acc = dd.setdefault(card, {}).setdefault(lab, {"n": 0, "dead": 0.0, "early": 0.0})
                acc["n"] += d["n"]
                acc["dead"] += d["p_dead"] * d["n"]
                acc["early"] += d.get("p_early_dead", 0) * d["n"]
    for card, rows in dd.items():
        for lab, acc in rows.items():
            n = acc["n"] or 1
            k = int(round(acc["dead"]))
            rows[lab] = {"n": acc["n"], "p_dead": round(acc["dead"] / n, 4), "ci95": bx.ex.wilson(k, acc["n"]),
                         "p_early_dead": round(acc["early"] / n, 4)}
    out["dead_opening_draw"] = dd
    return out


def package_tax(fq, dd, deck_cards):
    """Dedicated low-floor vs strong standalone vs dual-role, from MEASURED rates (T2-T4 pooled)."""
    rows = {}
    for card in PKG_CARDS + COMPARATORS:
        if card not in deck_cards or card not in fq:
            continue
        held = sum(fq[card][t]["n_held"] for t in fq[card] if t != "t1")
        if not held:
            continue
        mat = sum(fq[card][t]["material"] * fq[card][t]["n_held"] for t in fq[card] if t != "t1") / held
        roles = {}
        for t in fq[card]:
            if t == "t1":
                continue
            for rk, rv in fq[card][t]["roles"].items():
                roles[rk] = roles.get(rk, 0) + rv * fq[card][t]["n_held"]
        roles = {k: round(v / held, 4) for k, v in roles.items()}
        combo = roles.get("combo_live", 0) + roles.get("combo_pair", 0)
        fair = max(roles.get(k, 0) for k in ("fair_tutor", "development", "interaction_held", "land_drop")) \
            if any(k in roles for k in ("fair_tutor", "development", "interaction_held", "land_drop")) else 0
        if mat >= 0.6:
            cls = "dual_role" if combo >= 0.05 and fair >= 0.4 else "strong_standalone"
        elif mat >= 0.35:
            cls = "dual_role" if combo >= 0.05 else "moderate_floor"
        else:
            cls = "dedicated_low_floor"
        rows[card] = {"p_material_given_in_hand_t2_t4": round(mat, 4), "roles_t2_t4": roles,
                      "measured_class": cls,
                      "p_dead_in_kept_hand": dd.get(card, {}).get("all_kept_hands", {}).get("p_dead")}
    return rows


def assemble():
    head = _load("variants_headline")
    sec = _load("variants_secondary")
    abl = _load("ablations")
    audit = _load("audit_main")
    for k, v in _load("audit_local").items():  # local hedge run of the same phase (identical seeds)
        if k not in audit:
            audit[k] = v
    scen = _load("scenarios_main")
    for part in ("scenarios_s1", "scenarios_s2"):  # worker-session splits by config (identical seeds)
        for k, v in _load(part).items():
            if not k.startswith("_") or k not in scen:
                scen[k] = v
    cov = json.loads((OUT / "deckbuild008b_interaction_coverage.json").read_text()) \
        if (OUT / "deckbuild008b_interaction_coverage.json").exists() else {}
    for k, v in _load("variants_rep2").items():  # extra independent replicate for decision-critical builds
        if k.startswith("_"):
            continue
        tgt = head if k in head else sec
        tgt.setdefault(k, {}).update(v)
    variants = {}
    for src in (head, sec):
        for k, v in src.items():
            if k.startswith("_"):
                continue
            variants[k] = pool_reps(v)
            variants[k]["adds_cuts_vs_v8_plus_pilgrim"] = bx.CONFIGS.get(bx.LEGACY.get(k, k))
    prov = {"task": "SIM-DECKBUILD-008b", "run_class": "DECK_BACKED_GOLDFISH (Monte Carlo) + STATIC_ANALYSIS",
            "subject_deck_hash": bx.ex.baseline()[1], "base_seed": bx.BASE_SEED_B,
            "headline_design": head.get("_design"), "secondary_design": sec.get("_design"),
            "rules": "008 rules + fair Tainted Pact tutor (exile-above exposure => nondeterministic) + Colossal "
                     "Skyturtle channel regrowth; *_legacy_model = exact 008 rules",
            "dork_swap": "Deathrite Shaman -> Avacyn's Pilgrim in every config except V8_frozen"}
    vm = {"provenance": prov, "variants": variants, "ablations": abl}
    (OUT / "deckbuild008b_variant_metrics.json").write_text(json.dumps(vm, indent=1, default=list) + "\n")

    brick = {"provenance": prov,
             "definitions": {
                 "material": list(an.MATERIAL), "secondary": list(an.SECONDARY),
                 "stranded": "no role at all at that main phase",
                 "brick": "a card in the KEPT hand with no material role at any main phase T1-T4 while in hand",
                 "early_dead": "a kept card with no material role at T1 or T2",
                 "priors_applied": "Oracle / Consultation / Swift / Hazel castability is not development; Consultation's "
                                   "fair mode is 'fair_risky' (secondary); Tainted Pact castable = fair tutor "
                                   "(material); Spellseeker castable with a target = fair tutor; Oboro without "
                                   "Cradle = body only"},
             "configs": {}}
    for k, v in variants.items():
        deck_cards = set(bx.build(k)) if k in bx.CONFIGS or k in bx.LEGACY or k == "V8_frozen" else set()
        brick["configs"][k] = {
            m: v[m] for m in v if m.startswith(("bricks_", "kept_hand_", "early_dead", "stranded_", "secondary_only_"))}
        brick["configs"][k]["package_tax"] = package_tax(v["focus_card_quality"], v["dead_opening_draw"], deck_cards)
        brick["configs"][k]["dead_opening_draw"] = {c: v["dead_opening_draw"][c] for c in v["dead_opening_draw"]
                                                    if c in PKG_CARDS + COMPARATORS}
        brick["configs"][k]["focus_card_quality"] = {c: v["focus_card_quality"][c] for c in v["focus_card_quality"]
                                                     if c in PKG_CARDS + COMPARATORS}
    (OUT / "deckbuild008b_brick_burden.json").write_text(json.dumps(brick, indent=1) + "\n")

    fair = {"provenance": prov, "method": "per-state audit on goldfish states (real library order); closed form "
            "E[exiled] = (N-k)/(k+1), P(specific card exiled) = 1/(k+1)",
            "state_audit": {k: v.get("fair_pact_audit") for k, v in audit.items() if not k.startswith("_")},
            "spent_pact_ablations": {k: abl[k] for k in abl if k.startswith(("B_pact", "B_forced", "B_lose", "C_"))}}
    (OUT / "deckbuild008b_fair_pact_analysis.json").write_text(json.dumps(fair, indent=1) + "\n")

    csa = {"provenance": prov, "goldfish_states": {k: {kk: v[kk] for kk in v if kk.startswith("t")}
                                                   for k, v in audit.items() if not k.startswith("_")},
           "synthetic_windows": {k: {n: d for n, d in v.items() if "|" in n} for k, v in scen.items()
                                 if not k.startswith("_")},
           "spellseeker_audit": {k: v.get("spellseeker_audit") for k, v in audit.items() if not k.startswith("_")},
           "tutor_leverage": {k: v.get("tutor_leverage_t3_t4") for k, v in audit.items() if not k.startswith("_")},
           "resilience": {k: v.get("resilience_given_det_win") for k, v in audit.items() if not k.startswith("_")}}
    (OUT / "deckbuild008b_conversion_surface.json").write_text(json.dumps(csa, indent=1) + "\n")
    (OUT / "deckbuild008b_scenarios.json").write_text(json.dumps({"provenance": prov, **scen}, indent=1) + "\n")

    rows = []
    for k in ["V8_frozen"] + bx.HEADLINE + [x for x in variants if x not in bx.HEADLINE and x != "V8_frozen"]:
        if k not in variants:
            continue
        v = variants[k]
        pt = brick["configs"][k]["package_tax"]
        a = audit.get(k, {})
        post = scen.get(k, {}).get("post_fight|none|main", {})
        post_en = scen.get(k, {}).get("post_fight|enabler|instant", {})
        cv = cov.get("configs", {}).get(k, {}).get("coverage", {})
        rows.append({
            "build": k,
            "det_t2": v["det_win_by_t2"]["value"], "det_t3": v["det_win_by_t3"]["value"],
            "det_t4": v["det_win_by_t4"]["value"], "det_t4_delta_vs_A": v["det_win_by_t4"].get("delta_vs_ref"),
            "det_t4_delta_se": v["det_win_by_t4"].get("delta_se"),
            "protected_t4": v["det_protected_by_t4"]["value"], "instant_t4": v["det_instant_window_by_t4"]["value"],
            "oracle_any_t4": v["oracle_any_by_t4"]["value"], "non_oracle_det_t4": v["non_oracle_det_by_t4"]["value"],
            "keep7": v["keep7"]["value"], "mean_mulligans": v["mean_mulligans"]["value"],
            "t2_mana_ge3": v["t2_mana_ge3"]["value"], "premium_engine_t3": v["premium_engine_by_t3"]["value"],
            "bricks_per_kept_hand": v["bricks_in_kept_hand_mean"]["value"],
            "bricks_delta_vs_A": v["bricks_in_kept_hand_mean"].get("delta_vs_ref"),
            "bricks_delta_se": v["bricks_in_kept_hand_mean"].get("delta_se"),
            "kept_hand_2plus_bricks": v["kept_hand_2plus_bricks"]["value"],
            "dedicated_low_floor_package_cards": sum(1 for c in PKG_CARDS if pt.get(c, {}).get("measured_class") == "dedicated_low_floor"),
            "post_fight_csa_main": post.get("csa_mean_win_draws_if_not_winning"),
            "post_fight_p_det_main": post.get("p_det_now"),
            "post_fight_csa_instant_enabler": post_en.get("csa_mean_win_draws_if_not_winning"),
            "t4_main_csa": (a.get("t4_main") or {}).get("csa_win_draws_mean"),
            "theft_cards": (cv.get("creature_theft") or {}).get("n_cards"),
            "resolved_creature_answers": (cv.get("resolved_creature_answer") or {}).get("n_cards"),
            "regrowth_cards": (cv.get("regrowth_of_spent_resources") or {}).get("n_cards"),
            "access_theft_hand_or_tutor_t3": v.get("access_creature_theft_hand_or_tutor_t3", {}).get("value"),
            "access_resolved_creature_answer_hand_t4": v.get("access_resolved_creature_answer_in_hand_t4", {}).get("value"),
        })
    with (OUT / "deckbuild008b_final_comparison.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("assembled", len(rows), "rows")
