"""SIM-001 SOLO-004 section 5 — interpretable opening-hand value model(s).

Fits models estimating expected hand quality from OPENER-VISIBLE features only (never future
draws, RNG seed identity, or post-mulligan information - the feature set is exactly
opening_hand_features.py's output, already audited for that in the dataset generator). Primary
target: `out_t3__t3_any_strong_state` (SOLO-003R's already-validated broad compounding-state
flag) - used here as ONE convenient binary label for a predictive model, not as SOLO-004's final
multi-objective value function (that's section 6, built on the full outcome vector separately).

Three models, in increasing order of trust for the FINAL human heuristic:
  1. Logistic regression - interpretable coefficients (standardized, so magnitude is comparable
     across features), cross-validated.
  2. A shallow decision tree (max_depth=4) - human-readable rule structure, and its split
     structure is read off directly for "which feature interactions materially matter" (section
     5's other requirement) rather than a separate interaction-term search.
  3. A gradient-boosted model - fit ONLY as a black-box upper-bound benchmark (how much
     predictive power is left on the table by insisting on interpretability). Per the spec: "must
     not become the final human heuristic."

Leakage check: every feature column comes from the `opener__` namespace in the SOLO-004 dataset,
which is built exclusively from opening_hand_features.py (raw hand inspection + one turn of
simulation on the ORIGINAL 7 cards) - no `out_*`/`achv_*` column is ever used as an input.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, accuracy_score

from analyze_land_populations import load_rows

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = "out_t3__t3_any_strong_state"
RANDOM_STATE = 42

# Every opener__* boolean/numeric field is fair game; list-valued and mixed-type columns are
# excluded (land_count_bucket mixes int and the string "5+"; the *_names/*_cast list columns
# aren't scalar features - their boolean presence is already captured separately, e.g.
# has_tutor_card / t1_any_engine_cast).
EXCLUDE_SUFFIXES = (
    "_names", "_cast", "_direct_from_lands", "_potential_with_fetches", "_bottleneck_direct",
    "t1_live_interaction",
)
EXCLUDE_EXACT = {"opener__land_count_bucket", "opening_hand_land_count"}  # land_count kept via opener__land_count instead


def build_feature_frame(rows):
    df = pd.DataFrame(rows)
    opener_cols = [c for c in df.columns if c.startswith("opener__")]
    feature_cols = [
        c for c in opener_cols
        if c not in EXCLUDE_EXACT and not any(c.endswith(suf) for suf in EXCLUDE_SUFFIXES)
    ]
    X = df[feature_cols].copy()
    for c in X.columns:
        if X[c].dtype == bool:
            X[c] = X[c].astype(int)
    y = df[TARGET].astype(int)
    return X, y, feature_cols


def fit_logistic(X, y):
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    model = LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)
    auc_scores = cross_val_score(model, Xs, y, cv=cv, scoring="roc_auc")
    acc_scores = cross_val_score(model, Xs, y, cv=cv, scoring="accuracy")
    model.fit(Xs, y)
    coefs = sorted(
        zip(X.columns, model.coef_[0]), key=lambda t: -abs(t[1])
    )
    return {
        "cv_auc_mean": float(auc_scores.mean()), "cv_auc_std": float(auc_scores.std()),
        "cv_accuracy_mean": float(acc_scores.mean()), "cv_accuracy_std": float(acc_scores.std()),
        "standardized_coefficients": [{"feature": f, "coef": float(c)} for f, c in coefs],
    }


def fit_tree(X, y, max_depth=4):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    model = DecisionTreeClassifier(max_depth=max_depth, random_state=RANDOM_STATE, min_samples_leaf=200)
    auc_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
    acc_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    model.fit(X, y)
    rules = export_text(model, feature_names=list(X.columns))
    importances = sorted(
        zip(X.columns, model.feature_importances_), key=lambda t: -t[1]
    )
    return {
        "cv_auc_mean": float(auc_scores.mean()), "cv_auc_std": float(auc_scores.std()),
        "cv_accuracy_mean": float(acc_scores.mean()), "cv_accuracy_std": float(acc_scores.std()),
        "rules_text": rules,
        "feature_importances": [{"feature": f, "importance": float(i)} for f, i in importances if i > 0],
    }, model


def fit_gbm_benchmark(X, y):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    model = GradientBoostingClassifier(random_state=RANDOM_STATE, n_estimators=150, max_depth=3)
    auc_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
    acc_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    model.fit(X, y)
    importances = sorted(zip(X.columns, model.feature_importances_), key=lambda t: -t[1])
    return {
        "cv_auc_mean": float(auc_scores.mean()), "cv_auc_std": float(auc_scores.std()),
        "cv_accuracy_mean": float(acc_scores.mean()), "cv_accuracy_std": float(acc_scores.std()),
        "feature_importances": [{"feature": f, "importance": float(i)} for f, i in importances if i > 0.001][:20],
        "note": "UPPER-BOUND BENCHMARK ONLY - not used as the final human heuristic, per spec.",
    }


def holdout_check(X, y, model_fn):
    """Section 21's holdout validation: fit on a train split, evaluate ONLY on the held-out test
    split (never touched during fitting/CV), so the reported number reflects genuinely unseen
    hands, not the same data used to derive the rules."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    model = model_fn()
    if isinstance(model, LogisticRegression):
        scaler = StandardScaler().fit(X_train)
        model.fit(scaler.transform(X_train), y_train)
        proba = model.predict_proba(scaler.transform(X_test))[:, 1]
    else:
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {
        "holdout_n": len(y_test), "holdout_auc": float(roc_auc_score(y_test, proba)),
        "holdout_accuracy": float(accuracy_score(y_test, pred)),
    }


def tree_depth_sweep(X, y, gbm_auc):
    """SOLO-004 section 11's simplification tradeoff, quantified: how much of the achievable AUC
    gain (over a random AUC=0.5 baseline, up to the GBM benchmark's ceiling) does a tree of each
    depth capture? Informs how small a human-usable rule count can be before it starts leaving
    real predictive value on the table."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    out = []
    for depth in [2, 3, 4, 5, 6, 7, 8]:
        m = DecisionTreeClassifier(max_depth=depth, random_state=RANDOM_STATE, min_samples_leaf=100)
        auc = cross_val_score(m, X, y, cv=cv, scoring="roc_auc").mean()
        leaves = DecisionTreeClassifier(max_depth=depth, random_state=RANDOM_STATE, min_samples_leaf=100).fit(X, y).get_n_leaves()
        pct_of_gbm_gain = (auc - 0.5) / (gbm_auc - 0.5) if gbm_auc > 0.5 else None
        out.append({
            "max_depth": depth, "cv_auc": float(auc), "n_leaves": int(leaves),
            "pct_of_gbm_auc_gain_captured": float(pct_of_gbm_gain) if pct_of_gbm_gain is not None else None,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_play.jsonl.gz"))
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_hand_value_models.json"))
    args = ap.parse_args()

    rows = load_rows(args.play)
    X, y, feature_cols = build_feature_frame(rows)
    print(f"n={len(X)}, features={len(feature_cols)}, positive_rate={y.mean():.3f}")

    logistic = fit_logistic(X, y)
    tree, tree_model = fit_tree(X, y)
    gbm = fit_gbm_benchmark(X, y)
    depth_sweep = tree_depth_sweep(X, y, gbm["cv_auc_mean"])

    logistic_holdout = holdout_check(X, y, lambda: LogisticRegression(max_iter=2000, random_state=RANDOM_STATE))
    tree_holdout = holdout_check(X, y, lambda: DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE, min_samples_leaf=200))

    result = {
        "target": TARGET,
        "n_hands": len(X),
        "n_features": len(feature_cols),
        "feature_columns": feature_cols,
        "positive_rate": float(y.mean()),
        "tree_depth_sweep_vs_gbm_ceiling": depth_sweep,
        "logistic_regression": {**logistic, "holdout": logistic_holdout},
        "decision_tree_depth4": {**tree, "holdout": tree_holdout},
        "gbm_upper_bound_benchmark": gbm,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")

    print("\n=== Logistic regression (5-fold CV) ===")
    print(f"AUC={logistic['cv_auc_mean']:.4f}+-{logistic['cv_auc_std']:.4f}  "
          f"Acc={logistic['cv_accuracy_mean']:.4f}  Holdout AUC={logistic_holdout['holdout_auc']:.4f}")
    print("Top 15 standardized coefficients:")
    for c in logistic["standardized_coefficients"][:15]:
        print(f"  {c['feature']:45s} {c['coef']:+.3f}")

    print("\n=== Decision tree (depth<=4, 5-fold CV) ===")
    print(f"AUC={tree['cv_auc_mean']:.4f}+-{tree['cv_auc_std']:.4f}  "
          f"Acc={tree['cv_accuracy_mean']:.4f}  Holdout AUC={tree_holdout['holdout_auc']:.4f}")
    print(tree["rules_text"])

    print("\n=== GBM upper-bound benchmark (5-fold CV) ===")
    print(f"AUC={gbm['cv_auc_mean']:.4f}+-{gbm['cv_auc_std']:.4f}  Acc={gbm['cv_accuracy_mean']:.4f}")
    print("Top feature importances:")
    for f in gbm["feature_importances"][:12]:
        print(f"  {f['feature']:45s} {f['importance']:.4f}")

    gap = gbm["cv_auc_mean"] - tree["cv_auc_mean"]
    print(f"\nAUC gap (GBM - depth-4 tree): {gap:+.4f} "
          f"({'small' if gap < 0.02 else 'moderate' if gap < 0.05 else 'notable'} - "
          f"a small gap means the interpretable tree is already capturing most of the learnable signal)")

    print("\n=== Simplification tradeoff: tree depth vs. % of GBM's achievable AUC gain captured ===")
    for d in depth_sweep:
        print(f"  depth={d['max_depth']}  leaves={d['n_leaves']:4d}  AUC={d['cv_auc']:.4f}  "
              f"pct_of_gbm_gain={d['pct_of_gbm_auc_gain_captured']:.1%}")


if __name__ == "__main__":
    main()
