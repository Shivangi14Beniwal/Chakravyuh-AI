"""
Build the similarity (kNN) index that backs the evidence layer.

This is deliberately NOT a duration regressor. The audit showed that
nearest neighbors in this exact feature space can have a 140x spread in
raw duration_min (1,241 min vs 177,510 min for near-identical events) --
so we never expose raw-minute neighbor durations. Instead we expose each
neighbor's duration_bucket, which the audit validated as informative: for
a sampled query event, 9 of 10 nearest neighbors matched the query's true
bucket.

This module only builds the index. See src/inference/predict.py for how
it's queried alongside the classifier at inference time.
"""

from pathlib import Path

import pandas as pd
from sklearn.neighbors import NearestNeighbors

from src.features.encoders import fit_knn_scaler, transform_for_similarity, save_artifact

N_NEIGHBORS = 11  # 10 neighbors + self, self is dropped at query time


def build_index(model_df: pd.DataFrame, artifacts_dir: str = "artifacts"):
    knn_scaler = fit_knn_scaler(model_df)
    X = transform_for_similarity(model_df, knn_scaler)

    index = NearestNeighbors(n_neighbors=N_NEIGHBORS)
    index.fit(X)

    Path(artifacts_dir).mkdir(parents=True, exist_ok=True)
    save_artifact(index, f"{artifacts_dir}/nn_index.pkl")
    save_artifact(knn_scaler, f"{artifacts_dir}/knn_scaler.pkl")
    save_artifact(X.columns.tolist(), f"{artifacts_dir}/nn_feature_columns.pkl")

    # also persist the lookup table (bucket + cause + corridor per row) so
    # inference can map neighbor indices back to human-readable evidence
    lookup_cols = ["event_cause", "corridor", "requires_road_closure", "duration_bucket", "duration_min"]
    model_df[lookup_cols].to_csv(f"{artifacts_dir}/nn_lookup.csv", index=False)

    return index, knn_scaler


if __name__ == "__main__":
    import sys

    data_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/model_df_full.csv"
    model_df = pd.read_csv(data_path)

    build_index(model_df)
    print(f"Similarity index built on {len(model_df)} historical events.")
    print("Artifacts saved to artifacts/nn_index.pkl, artifacts/knn_scaler.pkl, artifacts/nn_lookup.csv")
