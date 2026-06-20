"""
Single-event inference: the decision layer's entry point.

Given a new event's raw fields, returns:
  1. predicted closure bucket + class probabilities (classifier)
  2. top-N nearest historical events + their actual outcome buckets (kNN evidence)
  3. impact index (derived formula)
  4. cascade frequency indicator (statistical, junction-keyed)
  5. feature importances (for the explainability requirement)

This function is the only integration point the Streamlit app calls --
it owns the order of operations (load artifacts once, transform once,
combine once) so the app layer stays thin.
"""

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from src.features.build_features import PREDICTOR_CAT_COLS, PREDICTOR_NUM_COLS, ENGINEERED_TIME_COLS
from src.features.encoders import transform_for_classifier, transform_for_similarity
from src.inference.impact_index import impact_index
from src.inference.cascade_indicator import cascade_flag
from src.utils.io import load_pickle_artifact, load_json_artifact, DEFAULT_ARTIFACTS_DIR

FEATURE_COLS = PREDICTOR_CAT_COLS + PREDICTOR_NUM_COLS + ENGINEERED_TIME_COLS
N_EVIDENCE_NEIGHBORS = 10


@dataclass
class EventInput:
    """Raw fields for a single new event, matching the columns the
    pipeline was trained on. junction is optional and only used by the
    cascade indicator (69.3% missing in training data, so it is expected
    to be absent often)."""

    event_type: str
    event_cause: str
    requires_road_closure: bool
    corridor: str
    priority: str
    police_station: str
    latitude: float
    longitude: float
    hour: int
    dow: int
    month: int
    junction: Optional[str] = None


@dataclass
class ClosureIntelligenceResult:
    predicted_bucket: str
    bucket_probabilities: dict
    nearest_neighbors: list
    neighbor_bucket_distribution: dict
    impact: dict
    cascade: dict
    feature_importances: dict
    disclosed_limitations: list = field(default_factory=list)


class ClosureIntelligenceEngine:
    """Loads all frozen artifacts once and serves inference calls. Instantiate
    once per Streamlit session (st.cache_resource), not per request."""

    def __init__(self, artifacts_dir: str = DEFAULT_ARTIFACTS_DIR):
        self.artifacts_dir = artifacts_dir
        self.classifier = load_pickle_artifact("classifier", artifacts_dir)
        self.encoder = load_pickle_artifact("encoder", artifacts_dir)
        self.nn_index = load_pickle_artifact("nn_index", artifacts_dir)
        self.knn_scaler = load_pickle_artifact("knn_scaler", artifacts_dir)
        # persisted at training time: exact column order the index was fit on,
        # needed to align a single new row's one-hot columns at inference time
        self.nn_feature_columns = load_pickle_artifact("nn_feature_columns", artifacts_dir)
        self.nn_lookup = pd.read_csv(f"{artifacts_dir}/nn_lookup.csv")
        self.metrics = load_json_artifact("metrics", artifacts_dir)
        self.cause_tail_weights = load_json_artifact("cause_tail_weights", artifacts_dir)
        self.cascade_rates = load_json_artifact("cascade_rates", artifacts_dir)

    def predict(self, event: EventInput) -> ClosureIntelligenceResult:
        row = pd.DataFrame([event.__dict__])

        # 1. Classifier
        X_clf = transform_for_classifier(row, self.encoder)
        pred_bucket = self.classifier.predict(X_clf)[0]
        proba = self.classifier.predict_proba(X_clf)[0]
        bucket_probs = dict(zip(self.classifier.classes_, [round(float(p), 3) for p in proba]))

        # 2. Similarity evidence -- align one-hot columns to the fitted
        # index's training-time columns (categories absent from this single
        # row's one-hot encoding must be filled with 0, never dropped silently)
        X_knn = transform_for_similarity(row, self.knn_scaler)
        X_knn = X_knn.reindex(columns=self.nn_feature_columns, fill_value=0)
        distances, indices = self.nn_index.kneighbors(X_knn, n_neighbors=N_EVIDENCE_NEIGHBORS)
        neighbor_rows = self.nn_lookup.iloc[indices[0]]
        nearest_neighbors = neighbor_rows.to_dict(orient="records")
        neighbor_bucket_distribution = (
            neighbor_rows["duration_bucket"].value_counts().to_dict()
        )

        # 3. Impact index (derived formula, frozen)
        impact = impact_index(
            requires_road_closure=event.requires_road_closure,
            priority=event.priority,
            event_cause=event.event_cause,
            cause_tail_weights=self.cause_tail_weights,
        )

        # 4. Cascade frequency indicator (statistical, frozen)
        cascade = cascade_flag(event.junction, self.cascade_rates)

        # 5. Explainability: feature importances from the trained classifier
        feature_importances = dict(
            zip(FEATURE_COLS, [round(float(v), 4) for v in self.classifier.feature_importances_])
        )

        disclosed_limitations = [
            self.metrics.get("disclosed_limitation", ""),
            f"Known weak class: {self.metrics.get('known_weak_class', '')}",
            cascade.get("note", "") if cascade.get("source") == "population_fallback" else "",
        ]
        disclosed_limitations = [d for d in disclosed_limitations if d]

        return ClosureIntelligenceResult(
            predicted_bucket=pred_bucket,
            bucket_probabilities=bucket_probs,
            nearest_neighbors=nearest_neighbors,
            neighbor_bucket_distribution=neighbor_bucket_distribution,
            impact=impact,
            cascade=cascade,
            feature_importances=feature_importances,
            disclosed_limitations=disclosed_limitations,
        )
