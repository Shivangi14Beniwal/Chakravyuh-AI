"""
Tests for the closure bucket classifier. Asserts the model beats its
baseline by roughly the audited margin -- not an exact match (CV has
minor run-to-run variance from sklearn internals on some platforms), but
enough to catch a real regression.
"""

import pandas as pd
import pytest

from src.models.train_classifier import train_and_evaluate

PROCESSED_PATH = "data/processed/model_df_full.csv"


@pytest.fixture(scope="module")
def metrics():
    model_df = pd.read_csv(PROCESSED_PATH)
    return train_and_evaluate(model_df, artifacts_dir="artifacts_test")


def test_classifier_beats_baseline_accuracy(metrics):
    assert metrics["cv_accuracy_mean"] > metrics["baseline_accuracy"]


def test_classifier_beats_baseline_macro_f1(metrics):
    assert metrics["cv_macro_f1_mean"] > metrics["baseline_macro_f1"]


def test_cv_accuracy_within_audited_range(metrics):
    # audited mean was 0.573; allow tolerance for environment variance
    assert 0.50 <= metrics["cv_accuracy_mean"] <= 0.65


def test_all_buckets_represented_in_confusion_matrix(metrics):
    assert len(metrics["confusion_matrix_labels"]) == 4
