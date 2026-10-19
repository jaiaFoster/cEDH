"""Reproduce additive research benchmarks without changing the baseline database."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import unicodedata

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "commander-league-card-point-calibration"


def key(name):
    return unicodedata.normalize("NFC", name).casefold().strip()


def main():
    original_argv = sys.argv[:]
    inputs = json.loads((ROOT / "data/benchmark_inputs.json").read_text())
    sys.argv = ["benchmark_original.py", json.dumps(inputs)]
    namespace = {"__name__": "benchmark_reproduction"}
    previous_cwd = Path.cwd()
    try:
        os.chdir(BASE)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile((ROOT / "benchmark_original.py").read_text(), "benchmark_original.py", "exec"), namespace)
    finally:
        os.chdir(previous_cwd)
        sys.argv = original_argv
    cards, decks, weights = [namespace[k] for k in ("cards", "decks", "weights")]
    cache = json.loads((ROOT / "data/zarzak_cache.json").read_text())
    normalized = {}
    for name, entry in cache.items():
        k = key(name)
        assert k not in normalized or normalized[k]["p"] == entry["p"], "Conflicting aliases"
        normalized[k] = entry
    front_aliases = {}
    for name in cache:
        front_aliases.setdefault(key(name.split(" // ")[0]), []).append(name)
    old = pd.read_csv(BASE / "commander_card_scores.csv").set_index("oracle_id")
    candidates = []
    for oid, card in cards.items():
        entry = normalized.get(key(card["name"]))
        match_type = "exact canonical name" if entry else "missing"
        possible = front_aliases.get(key(card["name"]), [])
        if entry is None and len(possible) == 1:
            entry = cache[possible[0]]
            match_type = "unique first-face alias"
        score = entry["p"] if entry else None
        assert score is None or float(score).is_integer(), "Integer ratings required"
        weights[oid]["zarzak_cached_llm"] = int(score) if score is not None else None
        # A priori color-neutral basic-land control, never fitted to reviewer rankings.
        # All ordinary/snow basics keep a flat 30; this is an assumption, not a measured effect.
        weights[oid]["zarzak_basic_equalized"] = (30 if "Basic" in card.get("type_line", "") and "Land" in card.get("type_line", "")
            else int(score)) if score is not None else None
        weights[oid]["baseline_v02"] = int(old.loc[oid, "base_points"]) if oid in old.index else None
        candidates.append({"oracle_id": oid, "name": card["name"], **weights[oid],
            "commander_legality": card.get("legalities", {}).get("commander", "unknown"),
            "game_changer": bool(card.get("game_changer")),
            "source_model": "claude-sonnet-4-6" if entry else "",
            "source_text_hash": entry["h"] if entry else "",
            "name_match_type": match_type,
            "oracle_text_freshness": "not verified against upstream formatter" if entry else "missing rating",
            "evidence_quality": "LLM prior; no outcome validation" if entry else "no external LLM rating",
            "manual_reviewed": False})
    candidate_df = pd.DataFrame(candidates)
    candidate_df.to_csv(ROOT / "card_scoring_candidates.csv", index=False)
    methods = list(weights[next(iter(weights))])
    rows = []
    long_rows = []
    for deck in decks:
        row = {"deck": deck["name"], "year": deck["release_year"]}
        for method in methods:
            values = [(weights[oid][method], qty) for oid, qty in deck["counts"].items()]
            covered = sum(qty for value, qty in values if value is not None)
            subtotal = sum(value * qty for value, qty in values if value is not None)
            row[method] = subtotal
            row[method + "_covered_cards"] = covered
            long_rows.append({"deck": deck["name"], "release_year": deck["release_year"],
                "method": method, "score": subtotal if covered == 100 else None,
                "known_card_subtotal": subtotal, "covered_cards": covered,
                "missing_cards": 100 - covered, "complete": covered == 100,
                "score_type": "complete additive score" if covered == 100 else "partial diagnostic only"})
        rows.append(row)
    frame = pd.DataFrame(rows).set_index("deck")
    pd.DataFrame(long_rows).to_csv(ROOT / "benchmark_results.csv", index=False)
    namespace["df"] = frame
    metrics = {}
    ed = pd.read_csv(BASE / "data/clean/validation.csv")
    red = pd.read_csv(BASE / "data/clean/reddit_validation.csv")
    def complete_rankmetrics(labels, rank_column, method):
        names = labels.loc[frame.loc[labels.name, method + "_covered_cards"].to_numpy() == 100]
        if len(names) < 3:
            return {"spearman": None, "kendall": None, "pairwise_accuracy": None,
                    "n_requested": len(labels), "n_complete": len(names), "reason": "fewer than three fully covered decks"}
        result = namespace["rankmetrics"](names.name.tolist(), -names[rank_column].to_numpy(), method)
        result.update(n_requested=len(labels), n_complete=len(names))
        return result
    for method in methods:
        pair_results = []
        for a, b in inputs["pairs"]:
            delta = float(frame.loc[a, method] - frame.loc[b, method])
            pair_results.append({"stronger": a, "weaker": b, "difference": delta,
                                 "credit": float(delta > 0) + .5 * float(delta == 0),
                                 "complete": bool(frame.loc[a, method+"_covered_cards"] == 100 and
                                                  frame.loc[b, method+"_covered_cards"] == 100)})
        metrics[method] = {
            "edhrec6": complete_rankmetrics(ed, "community_rank", method),
            "reddit5": complete_rankmetrics(red, "author_rank", method),
            "new_pair_accuracy": float(np.mean([p["credit"] for p in pair_results if p["complete"]]))
                if any(p["complete"] for p in pair_results) else None,
            "new_pairs_complete": sum(p["complete"] for p in pair_results),
            "new_year_matched_pairs": pair_results,
            "complete_decks": int((frame[method + "_covered_cards"] == 100).sum()),
            "covered_precon_oracle_ids": sum(weights[oid][method] is not None for oid in namespace["oidlist"]),
            "median_known_subtotal": float(frame[method].median()),
            "median_complete_decks": float(frame.loc[frame[method + "_covered_cards"] == 100, method].median())
                if any(frame[method + "_covered_cards"] == 100) else None,
            "validation_complete": all(frame.loc[list(ed.name) + list(red.name), method + "_covered_cards"] == 100),
        }
    # Cohorts are explanatory groups. Never normalize scores within release year.
    annual = []
    for method in methods:
        for year, group in frame.groupby("year"):
            values = group.loc[group[method + "_covered_cards"] == 100, method].to_numpy()
            if len(values) == 0:
                annual.append({"method": method, "year": int(year), "n": len(group), "complete_decks": 0})
                continue
            annual.append({"method": method, "year": int(year), "n": len(group),
                "mean": float(np.mean(values)), "median": float(np.median(values)),
                "sd": float(np.std(values, ddof=1)) if len(group) > 1 else None,
                "p10": float(np.quantile(values, .1)), "p25": float(np.quantile(values, .25)),
                "p75": float(np.quantile(values, .75)), "p90": float(np.quantile(values, .9)),
                "iqr": float(np.quantile(values, .75)-np.quantile(values, .25)),
                "complete_decks": int((group[method + "_covered_cards"] == 100).sum())})
    pd.DataFrame(annual).to_csv(ROOT / "data/annual_distributions.csv", index=False)
    result = {k: v for k, v in namespace["result"].items()
              if k not in ("methods", "benchmark_rows", "difficult_cases")}
    result.update({"cached_names": len(cache), "cached_names_matched_oracle": int(candidate_df.zarzak_cached_llm.notna().sum()),
                   "methods": metrics})
    difficult = frame.loc[["Mutant Menace", "Science!", "Explorers of the Deep",
                           "Necron Dynasties", "From Cute to Brute"]].reset_index()
    difficult.to_csv(ROOT / "data/difficult_cases.csv", index=False)
    (ROOT / "data/benchmark_metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    # One-card price edits: exact additive rank sensitivity, no refitting on opinions.
    sensitive = []
    complete = frame.zarzak_cached_llm_covered_cards.to_numpy() == 100
    base_values = frame.zarzak_cached_llm.to_numpy()
    sensitivity_values = base_values[complete]
    for name in ("Sol Ring", "Command Tower", "Temple of the False God", "Arcane Signet"):
        matched = [o for o in namespace["oidlist"] if cards[o]["name"] == name]
        if not matched:
            continue
        counts = namespace["X"][complete, namespace["oi"][matched[0]]]
        for delta in (-20, 20):
            changed = sensitivity_values + counts * delta
            i, j = np.triu_indices(sum(complete), 1)
            old_sign, new_sign = np.sign(sensitivity_values[i]-sensitivity_values[j]), np.sign(changed[i]-changed[j])
            sensitive.append({"card": name, "price_delta": delta,
                "affected_decks": int(sum(counts > 0)),
                "maximum_deck_delta": float(max(abs(counts*delta))),
                "complete_decks": int(sum(complete)),
                "spearman_to_original": float(stats.spearmanr(sensitivity_values, changed).statistic),
                "strict_pair_reversals": int(sum(old_sign*new_sign < 0))})
    pd.DataFrame(sensitive).to_csv(ROOT / "data/price_sensitivity.csv", index=False)
    # Known additive-label emulation experiment: NOT independent deck-strength evidence.
    X = namespace["X"]
    years = frame.year.to_numpy()
    y = base_values
    train = (years <= 2023) & complete
    test = (years > 2023) & complete
    inference = []
    coefs = []
    for alpha in (.1, 10., 1000.):
        xt = X[train]
        beta = xt.T @ np.linalg.solve(xt @ xt.T + alpha*np.eye(sum(train)), y[train])
        prediction = X[test] @ beta
        coefs.append(beta)
        inference.append({"method": "ridge_zero_prior", "alpha": alpha,
            "training_decks": int(sum(train)), "held_out_decks": int(sum(test)),
            "held_out_mae": float(np.mean(abs(prediction-y[test]))),
            "held_out_spearman": float(stats.spearmanr(prediction, y[test]).statistic),
            "negative_coefficients": int(sum(beta < 0)),
            "purpose": "emulation identifiability diagnostic; labels are known card-score sums"})
    pd.DataFrame(inference).to_csv(ROOT / "data/inverse_emulation.csv", index=False)
    missing = candidate_df[candidate_df.oracle_id.isin(namespace["oidlist"]) & candidate_df.zarzak_cached_llm.isna()]
    missing[["oracle_id", "name", "commander_legality"]].to_csv(ROOT / "data/missing_precon_ratings.csv", index=False)
    quality = []
    for deck in decks:
        if frame.loc[deck["name"], "zarzak_cached_llm_covered_cards"] != 100:
            continue
        land_points = sum(weights[oid]["zarzak_cached_llm"]*qty for oid, qty in deck["counts"].items()
                          if "Land" in cards[oid].get("type_line", ""))
        total = frame.loc[deck["name"], "zarzak_cached_llm"]
        quality.append({"deck": deck["name"], "year": deck["release_year"], "land_points": land_points,
                        "nonland_points": total-land_points, "total": total, "land_fraction": land_points/total})
    pd.DataFrame(quality).to_csv(ROOT / "data/land_contributions.csv", index=False)
    composition = []
    for method in methods:
        for label, labels, column in (("edhrec6", ed, "community_rank"), ("reddit5", red, "author_rank")):
            labels = labels.loc[frame.loc[labels.name, method+"_covered_cards"].to_numpy() == 100]
            values = []
            for index in labels.index:
                subset = labels.drop(index)
                if len(subset) >= 3 and frame.loc[subset.name, method].nunique() > 1:
                    values.append(float(stats.spearmanr(-subset[column].to_numpy(), frame.loc[subset.name,method].to_numpy()).statistic))
            composition.append({"method": method, "sample": label, "n_complete": len(labels),
                "leave_one_out_min_rho": min(values) if values else None,
                "leave_one_out_max_rho": max(values) if values else None})
    pd.DataFrame(composition).to_csv(ROOT / "data/sample_sensitivity.csv", index=False)
    # Card names and source checksums make an auditable, immutable run signature.
    baseline_files = [BASE / "commander_card_scores.csv", BASE / "scoring_config.json",
                      BASE / "data/clean/precons.json"]
    (ROOT / "data/baseline_checksums.json").write_text(json.dumps({
        str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in baseline_files}, indent=2))
    print(json.dumps({"decks": len(decks), "methods": len(methods),
        "cached_names": len(cache), "llm_metrics": metrics["zarzak_cached_llm"]}, indent=2))


if __name__ == "__main__":
    main()
