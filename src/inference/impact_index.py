"""
Impact index -- a DERIVED score, not a learned model.

Audit finding: there is no severity/impact/scale column anywhere in the
46-column Astram dataset. Any module claiming to "predict impact" would be
inventing a label the data never provided. Instead, this index is a
transparent, auditable formula over three real columns:

    requires_road_closure (bool, 0% missing)
    priority              ("High"/"Low", 0.02% missing)
    event_cause closure-tail weight (derived from duration_bucket
        distribution per cause, computed once at build time below)

The closure-tail weight encodes the audit's finding that certain causes
(construction, road_conditions, water_logging) have much heavier >24hr
tails than others (vehicle_breakdown, accident). It is just the empirical
P(duration_bucket in {6-24hr, >24hr} | event_cause) from the training
table -- a frequency, not a prediction.
"""

import json
from pathlib import Path

import pandas as pd

LONG_BUCKETS = {"6-24hr", ">24hr"}


def compute_cause_tail_weights(model_df: pd.DataFrame) -> dict:
    """P(long closure | event_cause), from real historical frequency."""
    weights = {}
    for cause, g in model_df.groupby("event_cause"):
        if len(g) < 5:
            continue  # too few historical events to trust a per-cause rate
        long_frac = g["duration_bucket"].isin(LONG_BUCKETS).mean()
        weights[cause] = round(float(long_frac), 4)
    # fallback for causes with too few samples: overall long-closure rate
    weights["_default"] = round(float(model_df["duration_bucket"].isin(LONG_BUCKETS).mean()), 4)
    return weights


def impact_index(
    requires_road_closure: bool,
    priority: str,
    event_cause: str,
    cause_tail_weights: dict,
) -> dict:
    """Combine the three real signals into a 0-1 transparent score.

    Weights (0.4 / 0.3 / 0.3) are a stated design choice, not learned --
    closure has the largest single-event traffic effect, priority reflects
    the police department's own triage judgment, and cause tail weight
    reflects historical evidence of how disruptive that cause tends to be.
    """
    closure_component = 1.0 if requires_road_closure else 0.0
    priority_component = 1.0 if priority == "High" else 0.0
    tail_component = cause_tail_weights.get(event_cause, cause_tail_weights["_default"])

    score = 0.4 * closure_component + 0.3 * priority_component + 0.3 * tail_component

    return {
        "impact_index": round(score, 3),
        "components": {
            "requires_road_closure": closure_component,
            "priority_high": priority_component,
            "cause_long_closure_rate": tail_component,
        },
        "formula": "0.4*closure + 0.3*priority_high + 0.3*cause_long_closure_rate",
    }


def build_and_save(model_df: pd.DataFrame, artifacts_dir: str = "artifacts") -> dict:
    weights = compute_cause_tail_weights(model_df)
    Path(artifacts_dir).mkdir(parents=True, exist_ok=True)
    with open(f"{artifacts_dir}/cause_tail_weights.json", "w") as f:
        json.dump(weights, f, indent=2)
    return weights


if __name__ == "__main__":
    import sys

    data_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/model_df_full.csv"
    model_df = pd.read_csv(data_path)

    weights = build_and_save(model_df)
    print("Cause long-closure rates (historical frequency, not predicted):")
    for cause, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {cause:20s} {w}")
