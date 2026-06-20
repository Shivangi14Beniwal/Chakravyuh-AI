"""
Encoder and scaler fitting/persistence for the closure classifier and
similarity index. Kept separate from build_features.py so the same fitted
encoder is reused identically by both the classifier and the kNN index --
this guarantees the two layers see the same feature space, which is what
makes the evidence layer's neighbor list trustworthy for explaining the
classifier's prediction.
"""

import pickle
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from src.features.build_features import PREDICTOR_CAT_COLS, PREDICTOR_NUM_COLS, ENGINEERED_TIME_COLS


def fit_ordinal_encoder(model_df: pd.DataFrame) -> OrdinalEncoder:
    """Fit an OrdinalEncoder on categorical predictors for tree-based models.
    unknown_value=-1 handles categories seen at inference time that were not
    present during training (e.g. a new police_station)."""
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    enc.fit(model_df[PREDICTOR_CAT_COLS].astype(str))
    return enc


def fit_numeric_scaler(model_df: pd.DataFrame) -> StandardScaler:
    """Fit a StandardScaler on numeric features (lat/lon + engineered time)
    for the similarity (kNN) index, which needs distance-comparable units."""
    num_cols = PREDICTOR_NUM_COLS + ENGINEERED_TIME_COLS
    scaler = StandardScaler()
    scaler.fit(model_df[num_cols])
    return scaler


def transform_for_classifier(df: pd.DataFrame, encoder: OrdinalEncoder) -> pd.DataFrame:
    """Encode categoricals for the RandomForest classifier. Numeric features
    pass through unscaled since tree models don't require scaling.

    Casts the categorical block to float64 (not pandas' default
    PyArrow-backed string/bool dtypes) immediately after encoding, since
    sklearn's array indexing in train_test_split / cross_val_score does
    not reliably support Arrow-backed extension arrays."""
    out = df.copy()
    out[PREDICTOR_CAT_COLS] = encoder.transform(out[PREDICTOR_CAT_COLS].astype(str)).astype("float64")
    result = out[PREDICTOR_CAT_COLS + PREDICTOR_NUM_COLS + ENGINEERED_TIME_COLS]
    return result.astype("float64")


KNN_CAT_COLS = ["event_cause", "requires_road_closure", "corridor"]
KNN_NUM_COLS = ["latitude", "longitude", "hour"]


def fit_knn_scaler(model_df: pd.DataFrame) -> StandardScaler:
    """Fit the scaler specifically over the kNN numeric feature subset
    (lat/lon/hour), validated in the audit's neighbor-bucket-match test.
    Kept separate from fit_numeric_scaler, which scales the full
    lat/lon + hour/dow/month set for other potential uses."""
    scaler = StandardScaler()
    scaler.fit(model_df[KNN_NUM_COLS])
    return scaler


def transform_for_similarity(df: pd.DataFrame, knn_scaler: StandardScaler) -> pd.DataFrame:
    """Build the one-hot + scaled feature space used by the similarity
    (kNN) index. One-hot is used here (not ordinal) because distance between
    ordinal-encoded categories is meaningless; one-hot makes category
    mismatch contribute a fixed, interpretable distance.

    knn_scaler must be fit via fit_knn_scaler on the training table and
    reused at inference time -- never refit on a single query row."""
    cat_part = pd.get_dummies(df[KNN_CAT_COLS].astype(str))
    num_scaled = pd.DataFrame(
        knn_scaler.transform(df[KNN_NUM_COLS]), columns=KNN_NUM_COLS, index=df.index
    )
    return pd.concat([cat_part, num_scaled], axis=1)


def save_artifact(obj, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_artifact(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)
