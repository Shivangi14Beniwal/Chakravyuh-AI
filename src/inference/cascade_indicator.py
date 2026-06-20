"""
Cascade frequency indicator -- a statistical flag, not a trained model.

Audit finding: there is no cascade label in the dataset, and `junction` is
only 30.7% populated, so a trained cascade-prediction model is not
defensible. What IS defensible: real evidence of temporal clustering --
across junctions with >=5 events, 15.8% of consecutive same-junction event
gaps are <=2 hours (vs. a median gap of 68.3 hours). That is a population-
level statistic computed directly from historical timestamps, exposed
as-is with its coverage caveat, never dressed up as a prediction.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

MIN_EVENTS_FOR_JUNCTION_STAT = 5
CASCADE_WINDOW_HOURS = 2


def compute_junction_cascade_rates(raw_df: pd.DataFrame) -> dict:
    """For each junction with enough history, what fraction of consecutive
    events there occurred within CASCADE_WINDOW_HOURS of each other.

    raw_df must have 'junction' (str, 69.3% missing -- expected) and
    'start_datetime' (datetime, 0% missing) columns.
    """
    df = raw_df[raw_df["junction"].notna()].copy()
    df["start_datetime"] = pd.to_datetime(df["start_datetime"], errors="coerce", utc=True)

    rates = {}
    for junction, g in df.groupby("junction"):
        if len(g) < MIN_EVENTS_FOR_JUNCTION_STAT:
            continue
        g = g.sort_values("start_datetime")
        gap_hours = g["start_datetime"].diff().dt.total_seconds() / 3600
        gap_hours = gap_hours.dropna()
        if len(gap_hours) == 0:
            continue
        rates[junction] = {
            "n_events": int(len(g)),
            "cascade_rate_within_2hr": round(float((gap_hours <= CASCADE_WINDOW_HOURS).mean()), 4),
            "median_gap_hours": round(float(gap_hours.median()), 2),
        }

    # population-level fallback for junctions with <5 events or no junction data
    all_gaps = []
    for junction, g in df.groupby("junction"):
        if len(g) < MIN_EVENTS_FOR_JUNCTION_STAT:
            continue
        g = g.sort_values("start_datetime")
        gap_hours = g["start_datetime"].diff().dt.total_seconds() / 3600
        all_gaps.extend(gap_hours.dropna().tolist())
    all_gaps = np.array(all_gaps)

    rates["_population_fallback"] = {
        "n_events": int(len(all_gaps)) + len(rates),
        "cascade_rate_within_2hr": round(float((all_gaps <= CASCADE_WINDOW_HOURS).mean()), 4) if len(all_gaps) else 0.0,
        "median_gap_hours": round(float(np.median(all_gaps)), 2) if len(all_gaps) else None,
        "note": "Used when junction is missing or has <5 historical events (69.3% of rows have no junction).",
    }

    return rates


from typing import Optional

def cascade_flag(junction: Optional[str], rates: dict) -> dict:
    """Look up the cascade indicator for a given junction at inference
    time. Returns the population fallback if junction is missing or
    unseen -- this is disclosed, not silently substituted."""
    if junction and junction in rates:
        result = dict(rates[junction])
        result["source"] = "junction-specific"
    else:
        result = dict(rates["_population_fallback"])
        result["source"] = "population_fallback"
    return result


def build_and_save(raw_df: pd.DataFrame, artifacts_dir: str = "artifacts") -> dict:
    rates = compute_junction_cascade_rates(raw_df)
    Path(artifacts_dir).mkdir(parents=True, exist_ok=True)
    with open(f"{artifacts_dir}/cascade_rates.json", "w") as f:
        json.dump(rates, f, indent=2)
    return rates


if __name__ == "__main__":
    import sys

    raw_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/astram_event_data.csv"
    raw_df = pd.read_csv(raw_path)

    rates = build_and_save(raw_df)
    print(f"Computed cascade rates for {len(rates) - 1} junctions (>= {MIN_EVENTS_FOR_JUNCTION_STAT} events each).")
    print(f"Population fallback: {rates['_population_fallback']}")
