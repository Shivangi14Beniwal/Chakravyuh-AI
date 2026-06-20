"""
Tests for the feature engineering pipeline. These assert against the
audited numbers directly -- if the pipeline drifts from these counts,
the audit's findings no longer apply and the frozen architecture's
evidence base is broken.
"""

import pandas as pd
import pytest

from src.features.build_features import build_modeling_table, bucket_duration, ALL_FEATURE_COLS


RAW_PATH = "data/raw/astram_event_data.csv"


@pytest.fixture(scope="module")
def model_df():
    return build_modeling_table(RAW_PATH)


def test_row_count_matches_audit(model_df):
    assert len(model_df) == 3182


def test_no_negative_duration(model_df):
    assert (model_df["duration_min"] >= 0).all()


def test_no_missing_features(model_df):
    assert model_df[ALL_FEATURE_COLS].isna().sum().sum() == 0


def test_bucket_distribution_matches_audit(model_df):
    counts = model_df["duration_bucket"].value_counts().to_dict()
    assert counts["<=1hr"] == 1498
    assert counts["1-6hr"] == 896
    assert counts[">24hr"] == 662
    assert counts["6-24hr"] == 126


@pytest.mark.parametrize(
    "minutes,expected_bucket",
    [
        (0.5, "<=1hr"),
        (60, "<=1hr"),
        (61, "1-6hr"),
        (360, "1-6hr"),
        (361, "6-24hr"),
        (1440, "6-24hr"),
        (1441, ">24hr"),
    ],
)
def test_bucket_boundaries(minutes, expected_bucket):
    assert bucket_duration(minutes) == expected_bucket
