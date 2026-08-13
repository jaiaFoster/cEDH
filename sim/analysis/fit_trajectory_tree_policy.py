"""SIM-001 MULL-005 — TRAJECTORY_TREE: shallow decision tree fit to TRAJECTORY_MACHINE's label.

Fits a depth<=4 decision tree on OPENER-VISIBLE features only (same exclusion discipline as
SOLO-004's fit_hand_value_model.py - no out_*/trajectory_*/achv_* column is ever an input) to
predict the keep/mulligan label TRAJECTORY_MACHINE would give a 7-card hand: best-known trajectory
tier (already computed per-hand in mull005_trajectory_dataset_*.jsonl.gz as trajectory_best__tier)
at or above the hand-size-7 threshold from mull005_hand_size_thresholds.json (assumed mulligan-
card-cost=1.0). Reuses the existing dataset rather than re-running the bounded search.
"""
import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import cross_val_score, train_test_split, StratifiedKFold
from sklearn.metrics import roc_auc_score, accuracy_score

from analyze_land_populations import load_rows
from trajectory_policies import CHEAP_TUTORS_WITH_REAL_T2_CONVERSION, TIER_RANK, _load_thresholds

REPO_ROOT = Path(__file__).resolve().parents[2]
RANDOM_STATE = 42

EXCLUDE_SUFFIXES = (
    "_names", "_cast", "_direct_from_lands", "_potential_with_fetches", "_bottleneck_direct",
    "t1_live_interaction",
)
EXCLUDE_EXACT = {"opener__land_count_bucket", "opening_hand_land_count"}


def build_feature_frame(rows):
    df = pd.DataFrame(rows)
    df["opener__has_cheap_tutor_cmc1"] = df["opener__tutor_names"].apply(
        lambda names: any(n in CHEAP_TUTORS_WITH_REAL_T2_CONVERSION for n in names)
    )
    opener_cols = [c for c in df.columns if c.startswith("opener__")]
    feature_cols = [
        c for c in opener_cols
        if c not in EXCLUDE_EXACT and not any(c.endswith(suf) for suf in EXCLUDE_SUFFIXES)
    ]
    X = df[feature_cols].copy()
    for c in X.columns:
        if X[c].dtype == bool:
            X[c] = X[c].astype(int)

    keep_tier = _load_thresholds()[7]
    y = (df["trajectory_best__tier"].map(TIER_RANK) <= TIER_RANK[keep_tier]).astype(int)
    return X, y, feature_cols


def fit_tree(X, y, max_depth=4):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    model = DecisionTreeClassifier(max_depth=max_depth, random_state=RANDOM_STATE, min_samples_leaf=150)
    auc_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
    acc_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    model.fit(X, y)
    rules = export_text(model, feature_names=list(X.columns))
    importances = sorted(zip(X.columns, model.feature_importances_), key=lambda t: -t[1])
    return {
        "cv_auc_mean": float(auc_scores.mean()), "cv_auc_std": float(auc_scores.std()),
        "cv_accuracy_mean": float(acc_scores.mean()), "cv_accuracy_std": float(acc_scores.std()),
        "rules_text": rules,
        "feature_importances": [{"feature": f, "importance": float(i)} for f, i in importances if i > 0],
    }


def holdout_check(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    model = DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE, min_samples_leaf=150)
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {
        "holdout_n": len(y_test), "holdout_auc": float(roc_auc_score(y_test, proba)),
        "holdout_accuracy": float(accuracy_score(y_test, pred)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", default=str(REPO_ROOT / "results/solo_baseline/mull005_trajectory_dataset_play.jsonl.gz"))
    ap.add_argument("--out", default=str(REPO_ROOT / "results/solo_baseline/mull005_trajectory_tree_policy.json"))
    args = ap.parse_args()

    rows = load_rows(args.play)
    X, y, feature_cols = build_feature_frame(rows)
    print(f"n={len(X)}, features={len(feature_cols)}, keep_rate={y.mean():.3f}")

    tree = fit_tree(X, y)
    holdout = holdout_check(X, y)

    result = {
        "n_hands": len(X), "n_features": len(feature_cols), "feature_columns": feature_cols,
        "keep_rate": float(y.mean()),
        "target_definition": "trajectory_best__tier at hand size 7 clears mull005_hand_size_thresholds.json's cost=1.0 keep threshold",
        "decision_tree_depth4": {**tree, "holdout": holdout},
    }
    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"\nAUC={tree['cv_auc_mean']:.4f}+-{tree['cv_auc_std']:.4f}  Acc={tree['cv_accuracy_mean']:.4f}  "
          f"Holdout AUC={holdout['holdout_auc']:.4f}  Holdout Acc={holdout['holdout_accuracy']:.4f}")
    print(tree["rules_text"])


if __name__ == "__main__":
    main()
