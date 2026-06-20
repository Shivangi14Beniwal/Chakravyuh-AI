"""
Services layer.

This module is the ONLY place the product layer touches the frozen
backend. It wraps src/ modules and artifacts/ files for UI consumption --
caching, aggregation, and formatting only. No model logic, feature
engineering, or training code lives here. Nothing in src/, artifacts/,
or data/ is modified by this file or anything that imports it.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.inference.predict import ClosureIntelligenceEngine
from src.utils.io import load_json_artifact, DEFAULT_PROCESSED_DATA

BUCKET_ORDER = ["<=1hr", "1-6hr", "6-24hr", ">24hr"]
BUCKET_LABELS = {
    "<=1hr": "Within 1 hour",
    "1-6hr": "1 to 6 hours",
    "6-24hr": "6 to 24 hours",
    ">24hr": "Over 24 hours",
}
BUCKET_SIGNAL = {
    "<=1hr": "green",
    "1-6hr": "blue",
    "6-24hr": "amber",
    ">24hr": "coral",
}


@st.cache_resource
def get_engine() -> ClosureIntelligenceEngine:
    return ClosureIntelligenceEngine()


@st.cache_data
def get_historical_events() -> pd.DataFrame:
    """The cleaned, audited modeling table (3,182 events) -- used for map
    plotting and homepage aggregates. Read-only consumption of the frozen
    artifact built by src/features/build_features.py."""
    return pd.read_csv(DEFAULT_PROCESSED_DATA)


@st.cache_data
def get_metrics() -> dict:
    return load_json_artifact("metrics")


@st.cache_data
def get_cause_tail_weights() -> dict:
    return load_json_artifact("cause_tail_weights")


@st.cache_data
def get_cascade_rates() -> dict:
    return load_json_artifact("cascade_rates")


@st.cache_data
def get_top_cascade_junctions(n: int = 8) -> pd.DataFrame:
    """Junctions ranked by cascade_rate_within_2hr, excluding the
    population fallback entry. Used by the homepage ticker and decision
    support panel."""
    rates = get_cascade_rates()
    rows = []
    for junction, stats in rates.items():
        if junction == "_population_fallback":
            continue
        rows.append({"junction": junction, **stats})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("cascade_rate_within_2hr", ascending=False).head(n).reset_index(drop=True)


@st.cache_data
def get_cause_distribution() -> pd.DataFrame:
    """Event count and long-closure rate per cause, for city operational
    status and decision support. Sourced directly from the audited table
    and the frozen impact-index weights -- no new computation beyond
    grouping/counting."""
    df = get_historical_events()
    weights = get_cause_tail_weights()
    counts = df["event_cause"].value_counts().reset_index()
    counts.columns = ["event_cause", "event_count"]
    counts["long_closure_rate"] = counts["event_cause"].map(
        lambda c: weights.get(c, weights.get("_default", 0.0))
    )
    return counts.sort_values("event_count", ascending=False).reset_index(drop=True)


@st.cache_data
def get_corridor_summary() -> pd.DataFrame:
    """Event count and bucket mix per corridor, for the map view's
    corridor-level overlay and decision support's attention-area ranking."""
    df = get_historical_events()
    summary = (
        df.groupby("corridor")
        .agg(
            event_count=("event_cause", "count"),
            pct_requires_closure=("requires_road_closure", "mean"),
        )
        .reset_index()
    )
    long_bucket_share = (
        df.assign(is_long=df["duration_bucket"].isin(["6-24hr", ">24hr"]))
        .groupby("corridor")["is_long"]
        .mean()
        .reset_index()
        .rename(columns={"is_long": "long_closure_share"})
    )
    summary = summary.merge(long_bucket_share, on="corridor", how="left")
    return summary.sort_values("event_count", ascending=False).reset_index(drop=True)


def bucket_signal_color(bucket: str) -> str:
    """Hex color for a given closure bucket, matching the theme tokens."""
    mapping = {
        "<=1hr": "#2EBF8C",
        "1-6hr": "#4DA3F0",
        "6-24hr": "#F2A623",
        ">24hr": "#E8593C",
    }
    return mapping.get(bucket, "#8FA0B3")