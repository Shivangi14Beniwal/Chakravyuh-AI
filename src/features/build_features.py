"""
Feature engineering pipeline for Chakravyuh AI Closure Outcome Intelligence.

This pipeline reproduces exactly the audited transformation chain:
raw Astram event CSV -> cleaned, labeled modeling table.

Every step here is traceable to a specific audit finding. No field is used
that was not explicitly verified for completeness and signal during the
dataset audit. See README.md "Audit evidence" section for the underlying
numbers.

Frozen decisions encoded in this file (do not change without a new audit):
  - end_datetime is NOT used to compute duration (94% missing, and where
    present belongs almost entirely to planned events as a scheduled
    window, not an actual outcome timestamp).
  - duration = end_time - start_datetime, where end_time = resolved_datetime
    if present, else closed_datetime. This covers 39.1% of all rows.
  - Negative durations (3 rows, timestamp logging errors) are dropped.
  - Only low-missingness, start-of-event-available features are used as
    predictors: event_type, event_cause, requires_road_closure, corridor,
    priority, police_station, latitude, longitude, plus engineered
    hour / day-of-week / month from start_datetime.
  - cargo_material, reason_breakdown, age_of_truck, route_path, direction,
    assigned_to_police_id are excluded entirely (96-99.5% missing).
  - junction and zone are NOT used as primary predictors (66.8% / 57.0%
    missing respectively); junction is used only downstream, in the
    cascade frequency indicator, on the subset where it exists.
"""

import pandas as pd
import numpy as np

DATETIME_COLS = ["start_datetime", "resolved_datetime", "closed_datetime"]

PREDICTOR_CAT_COLS = [
    "event_type",
    "event_cause",
    "requires_road_closure",
    "corridor",
    "priority",
    "police_station",
]

PREDICTOR_NUM_COLS = ["latitude", "longitude"]

ENGINEERED_TIME_COLS = ["hour", "dow", "month"]

ALL_FEATURE_COLS = PREDICTOR_CAT_COLS + PREDICTOR_NUM_COLS + ENGINEERED_TIME_COLS


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in DATETIME_COLS:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df


def compute_duration(df: pd.DataFrame) -> pd.DataFrame:
    """Derive duration_min from start_datetime and the best available end
    timestamp. resolved_datetime takes priority over closed_datetime since
    it is the more direct resolution signal where both exist (6 rows)."""
    df = df.copy()
    df["end_time"] = df["resolved_datetime"].combine_first(df["closed_datetime"])
    df["duration_min"] = (df["end_time"] - df["start_datetime"]).dt.total_seconds() / 60
    return df


def bucket_duration(duration_min: float) -> str:
    """Closure bucket boundaries, frozen from the audit's classifier
    validation (Round 2 consistency check). <=1hr and >24hr are the
    well-separated classes (test recall 0.72 / 0.94); 1-6hr and 6-24hr
    are harder and disclosed as such in the demo."""
    if duration_min <= 60:
        return "<=1hr"
    elif duration_min <= 360:
        return "1-6hr"
    elif duration_min <= 1440:
        return "6-24hr"
    else:
        return ">24hr"


def engineer_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["start_datetime"].dt.hour
    df["dow"] = df["start_datetime"].dt.dayofweek
    df["month"] = df["start_datetime"].dt.month
    return df


def build_modeling_table(raw_csv_path: str) -> pd.DataFrame:
    """Full pipeline: raw CSV -> cleaned table ready for classifier training.

    Returns a DataFrame with ALL_FEATURE_COLS, duration_min, and
    duration_bucket. Rows without a usable duration label, with negative
    duration, or with missing values in the chosen low-missingness
    predictors are dropped (audited counts: 8173 -> 3195 -> 3192 -> 3182).
    """
    df = load_raw(raw_csv_path)
    df = compute_duration(df)

    # keep only rows with a usable duration label
    df = df[df["duration_min"].notna()].copy()

    # drop the 3 negative-duration rows (timestamp logging errors)
    df = df[df["duration_min"] >= 0].copy()

    df = engineer_time_features(df)

    model_df = df[ALL_FEATURE_COLS + ["duration_min"]].copy()

    # drop rows missing any chosen predictor (audited: 10 rows)
    model_df = model_df.dropna(subset=ALL_FEATURE_COLS)

    model_df["duration_bucket"] = model_df["duration_min"].apply(bucket_duration)

    return model_df.reset_index(drop=True)


if __name__ == "__main__":
    import sys

    raw_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/astram_event_data.csv"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "data/processed/model_df_full.csv"

    table = build_modeling_table(raw_path)
    table.to_csv(out_path, index=False)

    print(f"Built modeling table: {len(table)} rows, {len(ALL_FEATURE_COLS)} features")
    print(table["duration_bucket"].value_counts())
    print(f"Saved to {out_path}")
