"""
train_all.py -- one command to build every frozen artifact from the raw
Astram CSV. Run this once after dropping the raw CSV into data/raw/.

    python -m src.models.train_all data/raw/astram_event_data.csv

This does not perform any validation, tuning, or parameter search beyond
what's already frozen in train_classifier.py, train_similarity.py,
impact_index.py, and cascade_indicator.py. It is purely an orchestration
script for build mode.
"""

import sys

import pandas as pd

from src.features.build_features import build_modeling_table
from src.models.train_classifier import train_and_evaluate
from src.models.train_similarity import build_index
from src.inference.impact_index import build_and_save as build_impact_weights
from src.inference.cascade_indicator import build_and_save as build_cascade_rates


def main(raw_csv_path: str, artifacts_dir: str = "artifacts", processed_path: str = "data/processed/model_df_full.csv"):
    print(f"[1/5] Building modeling table from {raw_csv_path} ...")
    model_df = build_modeling_table(raw_csv_path)
    model_df.to_csv(processed_path, index=False)
    print(f"      {len(model_df)} rows, bucket distribution:")
    print(model_df["duration_bucket"].value_counts().to_string())

    print("\n[2/5] Training closure bucket classifier (frozen hyperparameters) ...")
    metrics = train_and_evaluate(model_df, artifacts_dir=artifacts_dir)
    print(f"      CV accuracy: {metrics['cv_accuracy_mean']} (baseline {metrics['baseline_accuracy']})")
    print(f"      CV macro-F1: {metrics['cv_macro_f1_mean']} (baseline {metrics['baseline_macro_f1']})")

    print("\n[3/5] Building similarity (kNN) index ...")
    build_index(model_df, artifacts_dir=artifacts_dir)
    print(f"      Index built on {len(model_df)} historical events.")

    print("\n[4/5] Computing impact index cause weights (derived, not learned) ...")
    weights = build_impact_weights(model_df, artifacts_dir=artifacts_dir)
    print(f"      {len(weights) - 1} event causes weighted.")

    print("\n[5/5] Computing cascade frequency indicator (statistical, not learned) ...")
    raw_df = pd.read_csv(raw_csv_path)
    rates = build_cascade_rates(raw_df, artifacts_dir=artifacts_dir)
    print(f"      {len(rates) - 1} junctions with sufficient history.")

    print(f"\nAll artifacts written to {artifacts_dir}/. Ready for the Streamlit app.")


if __name__ == "__main__":
    raw_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/astram_event_data.csv"
    main(raw_path)
