"""
Train the closure bucket classifier -- the one validated ML pillar in the
frozen architecture.

Frozen hyperparameters and evaluation protocol below come directly from the
audit's validation run (Round 2 consistency check):
    RandomForest(n_estimators=300, max_depth=10, class_weight='balanced')
    5-fold stratified CV
    CV accuracy:  0.573 (mean) vs majority-class baseline 0.471
    CV macro-F1:  0.460 (mean) vs majority-class baseline 0.160

Do not change hyperparameters without re-running the full validation
protocol in evaluate.py and updating artifacts/metrics.json -- the
project's credibility rests on these numbers being reproducible exactly
as audited, not re-tuned after the fact to look better.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

from src.features.build_features import PREDICTOR_CAT_COLS, PREDICTOR_NUM_COLS, ENGINEERED_TIME_COLS
from src.features.encoders import fit_ordinal_encoder, transform_for_classifier, save_artifact

FEATURE_COLS = PREDICTOR_CAT_COLS + PREDICTOR_NUM_COLS + ENGINEERED_TIME_COLS
TARGET_COL = "duration_bucket"

# Frozen hyperparameters -- see module docstring.
RF_PARAMS = dict(
    n_estimators=300,
    max_depth=10,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced",
)


def train_and_evaluate(model_df: pd.DataFrame, artifacts_dir: str = "artifacts") -> dict:
    encoder = fit_ordinal_encoder(model_df)
    X = transform_for_classifier(model_df, encoder)
    # .astype(object) avoids PyArrow-backed string array indexing failures
    # in sklearn's train_test_split / cross_val_score on this pandas build
    y = model_df[TARGET_COL].astype(str).to_numpy(dtype=object)

    # Baseline: majority class on a held-out split (for the disclosed
    # baseline-vs-model comparison shown in the demo).
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    majority_class = pd.Series(y_train).value_counts().idxmax()
    baseline_preds = np.full_like(y_test, majority_class)
    baseline_acc = accuracy_score(y_test, baseline_preds)
    baseline_f1 = f1_score(y_test, baseline_preds, average="macro")

    # 5-fold stratified CV -- the headline, reproducible metric.
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    clf = RandomForestClassifier(**RF_PARAMS)
    cv_acc = cross_val_score(clf, X, y, cv=skf, scoring="accuracy")
    cv_f1 = cross_val_score(clf, X, y, cv=skf, scoring="f1_macro")

    # Fit final model on the train split for the persisted artifact + test report.
    clf.fit(X_train, y_train)
    test_preds = clf.predict(X_test)
    report = classification_report(y_test, test_preds, output_dict=True)
    cm = confusion_matrix(y_test, test_preds, labels=sorted(set(y)))

    # Refit on full data for the artifact that ships in the app (CV already
    # gives us the honest generalization estimate above).
    final_clf = RandomForestClassifier(**RF_PARAMS)
    final_clf.fit(X, y)

    metrics = {
        "baseline_majority_class": str(majority_class),
        "baseline_accuracy": round(float(baseline_acc), 4),
        "baseline_macro_f1": round(float(baseline_f1), 4),
        "cv_accuracy_mean": round(float(cv_acc.mean()), 4),
        "cv_accuracy_folds": [round(float(s), 4) for s in cv_acc],
        "cv_macro_f1_mean": round(float(cv_f1.mean()), 4),
        "cv_macro_f1_folds": [round(float(s), 4) for s in cv_f1],
        "test_set_classification_report": report,
        "test_set_confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": sorted(set(y)),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_importances": dict(
            zip(FEATURE_COLS, [round(float(v), 4) for v in final_clf.feature_importances_])
        ),
        "known_weak_class": "1-6hr (test recall ~0.16-0.28, smallest reliably-sized class)",
        "disclosed_limitation": (
            "Label coverage is 39.1% of all events (3,182 of 8,173 after "
            "cleaning); this classifier is trained and evaluated only on "
            "events with a usable duration label."
        ),
    }

    Path(artifacts_dir).mkdir(parents=True, exist_ok=True)
    save_artifact(final_clf, f"{artifacts_dir}/classifier.pkl")
    save_artifact(encoder, f"{artifacts_dir}/encoder.pkl")
    with open(f"{artifacts_dir}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    import sys

    data_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/model_df_full.csv"
    model_df = pd.read_csv(data_path)

    metrics = train_and_evaluate(model_df)

    print("=== Closure bucket classifier: training complete ===")
    print(f"Baseline (majority class) accuracy: {metrics['baseline_accuracy']}")
    print(f"CV accuracy (mean of 5 folds):       {metrics['cv_accuracy_mean']}")
    print(f"Baseline macro-F1:                   {metrics['baseline_macro_f1']}")
    print(f"CV macro-F1 (mean of 5 folds):        {metrics['cv_macro_f1_mean']}")
    print(f"Disclosed limitation: {metrics['disclosed_limitation']}")
    print("Artifacts saved to artifacts/classifier.pkl, artifacts/encoder.pkl, artifacts/metrics.json")
