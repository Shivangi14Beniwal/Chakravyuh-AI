"""Shared load/save helpers. Thin wrappers kept in one place so paths are
defined once instead of scattered as string literals across the codebase."""

import json
import pickle
from pathlib import Path

import pandas as pd

DEFAULT_ARTIFACTS_DIR = "artifacts"
DEFAULT_PROCESSED_DATA = "data/processed/model_df_full.csv"
DEFAULT_RAW_DATA = "data/raw/astram_event_data.csv"

ARTIFACT_FILES = {
    "classifier": "classifier.pkl",
    "encoder": "encoder.pkl",
    "nn_index": "nn_index.pkl",
    "knn_scaler": "knn_scaler.pkl",
    "nn_feature_columns": "nn_feature_columns.pkl",
    "nn_lookup": "nn_lookup.csv",
    "metrics": "metrics.json",
    "cause_tail_weights": "cause_tail_weights.json",
    "cascade_rates": "cascade_rates.json",
}


def artifact_path(key: str, artifacts_dir: str = DEFAULT_ARTIFACTS_DIR) -> Path:
    return Path(artifacts_dir) / ARTIFACT_FILES[key]


def load_pickle_artifact(key: str, artifacts_dir: str = DEFAULT_ARTIFACTS_DIR):
    path = artifact_path(key, artifacts_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"Artifact '{key}' not found at {path}. Run the training scripts "
            f"(src/models/train_classifier.py, src/models/train_similarity.py, "
            f"src/inference/impact_index.py, src/inference/cascade_indicator.py) first."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pickle_artifact(obj, key: str, artifacts_dir: str = DEFAULT_ARTIFACTS_DIR) -> None:
    path = artifact_path(key, artifacts_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_json_artifact(key: str, artifacts_dir: str = DEFAULT_ARTIFACTS_DIR) -> dict:
    path = artifact_path(key, artifacts_dir)
    if not path.exists():
        raise FileNotFoundError(f"Artifact '{key}' not found at {path}.")
    with open(path) as f:
        return json.load(f)


def load_processed_table(path: str = DEFAULT_PROCESSED_DATA) -> pd.DataFrame:
    return pd.read_csv(path)


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def save_json(obj: dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def artifacts_exist(artifacts_dir: str = DEFAULT_ARTIFACTS_DIR) -> bool:
    required = [
        "classifier.pkl",
        "encoder.pkl",
        "nn_index.pkl",
        "knn_scaler.pkl",
        "nn_feature_columns.pkl",
        "nn_lookup.csv",
        "metrics.json",
        "cause_tail_weights.json",
        "cascade_rates.json",
    ]
    return all((Path(artifacts_dir) / f).exists() for f in required)
