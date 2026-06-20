"""
Integration tests for the full inference pipeline -- the path the
Streamlit app actually calls. These run against the real trained
artifacts in artifacts/, so they must run after the training scripts.
"""

import pytest

from src.inference.predict import ClosureIntelligenceEngine, EventInput


@pytest.fixture(scope="module")
def engine():
    return ClosureIntelligenceEngine()


@pytest.fixture
def sample_event():
    return EventInput(
        event_type="unplanned",
        event_cause="vehicle_breakdown",
        requires_road_closure=False,
        corridor="Non-corridor",
        priority="Low",
        police_station="Whitefield",
        latitude=12.9698,
        longitude=77.7500,
        hour=9,
        dow=1,
        month=3,
        junction=None,
    )


def test_predict_returns_valid_bucket(engine, sample_event):
    result = engine.predict(sample_event)
    assert result.predicted_bucket in {"<=1hr", "1-6hr", "6-24hr", ">24hr"}


def test_predict_probabilities_sum_to_one(engine, sample_event):
    result = engine.predict(sample_event)
    assert abs(sum(result.bucket_probabilities.values()) - 1.0) < 0.01


def test_predict_returns_ten_neighbors(engine, sample_event):
    result = engine.predict(sample_event)
    assert len(result.nearest_neighbors) == 10


def test_impact_index_in_valid_range(engine, sample_event):
    result = engine.predict(sample_event)
    assert 0.0 <= result.impact["impact_index"] <= 1.0


def test_cascade_uses_population_fallback_when_junction_missing(engine, sample_event):
    result = engine.predict(sample_event)
    assert result.cascade["source"] == "population_fallback"


def test_disclosed_limitations_nonempty(engine, sample_event):
    result = engine.predict(sample_event)
    assert len(result.disclosed_limitations) > 0
