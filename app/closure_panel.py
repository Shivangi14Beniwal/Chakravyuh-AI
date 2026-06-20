"""
Closure Outcome Intelligence panel.

This is a Streamlit component, not a standalone app -- it is designed to
be imported and called from the existing Chakravyuh AI app.py as one tab
or section, alongside the existing impact scoring / map / cascade
junction detection screens. It does not replace anything in the existing
app; see app.py in this repo for a minimal standalone host if you want to
demo this module in isolation before wiring it into the main app.

UI design choice driven directly by audit findings: the classifier's
prediction and the kNN evidence neighbors are shown side by side, not
merged into one number, because they can legitimately disagree (different
features dominate each) and hiding that disagreement would overstate
confidence the audit didn't earn.
"""

import streamlit as st
import pandas as pd

from src.inference.predict import ClosureIntelligenceEngine, EventInput
from app.components.widgets import outcome_badge, confidence_bar, severity_badge, divider


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
BUCKET_HEX = {
    "<=1hr": "#2EBF8C",
    "1-6hr": "#2DD4E8",
    "6-24hr": "#F2A623",
    ">24hr": "#FF4D4F",
}
BUCKET_RISK_WORD = {
    "<=1hr": "LOW RISK",
    "1-6hr": "LOW-MODERATE RISK",
    "6-24hr": "ELEVATED RISK",
    ">24hr": "HIGH RISK",
}


@st.cache_resource
def get_engine() -> ClosureIntelligenceEngine:
    return ClosureIntelligenceEngine()


@st.cache_data
def get_distinct_values(_engine: ClosureIntelligenceEngine) -> dict:
    """Pull distinct categorical values from the kNN lookup table to
    populate dropdowns with values the model actually saw in training."""
    lookup = _engine.nn_lookup
    return {
        "event_cause": sorted(lookup["event_cause"].dropna().unique().tolist()),
        "corridor": sorted(lookup["corridor"].dropna().unique().tolist()),
    }


def _cascade_risk_word(pct: float) -> tuple:
    if pct > 25:
        return "HIGH RISK", "#FF4D4F", "critical"
    elif pct > 15:
        return "MEDIUM RISK", "#F2A623", "elevated"
    else:
        return "LOW RISK", "#2EBF8C", "nominal"


def _impact_risk_word(score: float) -> tuple:
    if score > 0.65:
        return "HIGH IMPACT", "#FF4D4F", "critical"
    elif score > 0.35:
        return "MODERATE IMPACT", "#F2A623", "elevated"
    else:
        return "LOW IMPACT", "#2EBF8C", "nominal"


def _operational_response(impact_score: float, cascade_pct: float, predicted_bucket: str):
    """Pure presentation mapping over existing outputs -- no new logic,
    just a readable label derived from the same numbers already computed
    by impact_index and cascade_indicator."""
    high_signal_count = sum([
        impact_score > 0.65,
        cascade_pct > 25,
        predicted_bucket in ("6-24hr", ">24hr"),
    ])
    if high_signal_count >= 2:
        return "HIGH ATTENTION REQUIRED", "#FF4D4F", "critical", (
            "Multiple high-risk signals align: elevated impact index, cascade frequency, "
            "or a long predicted closure. Recommend immediate operational attention."
        )
    elif high_signal_count == 1:
        return "ESCALATE", "#F2A623", "elevated", (
            "One high-risk signal detected. Recommend escalating to a supervising officer "
            "for situational awareness."
        )
    else:
        return "MONITOR", "#2EBF8C", "nominal", (
            "No elevated signals detected across impact, cascade, or predicted closure length. "
            "Recommend standard monitoring."
        )


def render_closure_intelligence_panel():
    try:
        engine = get_engine()
    except FileNotFoundError as e:
        st.error(str(e))
        st.info(
            "Run the training pipeline first:\n\n"
            "```\npython src/features/build_features.py data/raw/astram_event_data.csv data/processed/model_df_full.csv\n"
            "python src/models/train_classifier.py\n"
            "python src/models/train_similarity.py\n"
            "python src/inference/impact_index.py\n"
            "python src/inference/cascade_indicator.py data/raw/astram_event_data.csv\n```"
        )
        return

    distinct = get_distinct_values(engine)

    st.markdown(
        '<div class="cc-panel"><div class="cc-eyebrow">Event Parameters</div></div>',
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown(
            """
            <style>
            div[data-testid="stForm"] {
                background-color: var(--cc-panel);
                backdrop-filter: blur(11px);
                -webkit-backdrop-filter: blur(11px);
                border: 1px solid var(--cc-border);
                border-radius: var(--cc-radius);
                padding: 4px 22px 20px 22px;
                margin-top: -54px;
                box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 10px 28px rgba(0,0,0,0.22);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        with st.form("closure_intel_form"):
            col1, col2 = st.columns(2)
            with col1:
                event_cause = st.selectbox("Event cause", distinct["event_cause"])
                requires_road_closure = st.checkbox("Requires road closure")
                priority = st.selectbox("Priority", ["High", "Low"])
                police_station = st.text_input("Police station", value="Whitefield")
            with col2:
                corridor = st.selectbox("Corridor", distinct["corridor"])
                latitude = st.number_input("Latitude", value=12.9698, format="%.4f")
                longitude = st.number_input("Longitude", value=77.7500, format="%.4f")
                junction = st.text_input("Junction (optional)", value="")

            col3, col4, col5 = st.columns(3)
            with col3:
                hour = st.slider("Hour of day", 0, 23, 12)
            with col4:
                dow = st.selectbox(
                    "Day of week",
                    options=list(range(7)),
                    format_func=lambda d: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d],
                )
            with col5:
                month = st.selectbox("Month", options=list(range(1, 13)))

            submitted = st.form_submit_button("Run closure intelligence", use_container_width=True)

    if not submitted:
        return

    event = EventInput(
        event_type="unplanned",
        event_cause=event_cause,
        requires_road_closure=requires_road_closure,
        corridor=corridor,
        priority=priority,
        police_station=police_station,
        latitude=latitude,
        longitude=longitude,
        hour=hour,
        dow=dow,
        month=month,
        junction=junction if junction.strip() else None,
    )

    result = engine.predict(event)

    pred_bucket = result.predicted_bucket
    pred_hex = BUCKET_HEX.get(pred_bucket, "#2DD4E8")
    pred_confidence = result.bucket_probabilities.get(pred_bucket, 0.0)
    pred_signal = BUCKET_SIGNAL.get(pred_bucket, "blue")

    impact_score = result.impact["impact_index"]
    impact_word, impact_hex, impact_level = _impact_risk_word(impact_score)

    cascade_pct = result.cascade["cascade_rate_within_2hr"] * 100
    cascade_word, cascade_hex, cascade_level = _cascade_risk_word(cascade_pct)

    response_word, response_hex, response_level, response_explainer = _operational_response(
        impact_score, cascade_pct, pred_bucket
    )

    # ============ HERO PREDICTION RESULT ============
    st.markdown(
        f"""
        <div class="cc-panel" style="padding:32px 36px; margin-top:18px; border-color:{pred_hex}55;
             background: radial-gradient(ellipse 90% 100% at 0% 0%, {pred_hex}1A, transparent 60%), var(--cc-panel);">
            <div class="cc-eyebrow" style="color:{pred_hex};">AI Closure Prediction</div>
            <div style="display:flex; align-items:flex-end; justify-content:space-between; flex-wrap:wrap; gap:18px; margin-top:6px;">
                <div>
                    <div style="font-family:var(--cc-font-display); font-size:46px; font-weight:700; color:{pred_hex}; line-height:1.0; text-transform:uppercase; letter-spacing:0.01em;">
                        {BUCKET_LABELS.get(pred_bucket, pred_bucket).upper()}
                    </div>
                    <div class="cc-mono" style="margin-top:8px; font-size:13px; color:var(--cc-text-secondary);">
                        Predicted closure bucket · {BUCKET_RISK_WORD.get(pred_bucket, "")}
                    </div>
                </div>
                <div style="text-align:right; min-width:200px;">
                    <div class="cc-mono" style="font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:var(--cc-text-tertiary);">Model Confidence</div>
                    <div style="font-family:var(--cc-font-display); font-size:38px; font-weight:700; color:var(--cc-text-primary); line-height:1.0;">
                        {pred_confidence*100:.1f}%
                    </div>
                </div>
            </div>
            <div class="cc-confidence-track" style="margin-top:18px; height:10px;">
                <div class="cc-confidence-fill" style="width:{pred_confidence*100:.1f}%; background:linear-gradient(90deg, {pred_hex}AA, {pred_hex});"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ============ AI ASSESSMENT / INTELLIGENCE BRIEFING ============
    st.markdown(
        f"""
        <div class="cc-panel-alt" style="padding:24px 28px; margin-top:14px;">
            <div class="cc-eyebrow">AI Assessment · Intelligence Briefing</div>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; margin-top:10px;">
                <div>
                    <div class="cc-mono" style="font-size:10.5px; letter-spacing:0.07em; text-transform:uppercase; color:var(--cc-text-tertiary);">Predicted Closure</div>
                    <div style="font-weight:700; font-size:15px; color:{pred_hex}; margin-top:5px;">{BUCKET_LABELS.get(pred_bucket, pred_bucket)}</div>
                </div>
                <div>
                    <div class="cc-mono" style="font-size:10.5px; letter-spacing:0.07em; text-transform:uppercase; color:var(--cc-text-tertiary);">Impact Level</div>
                    <div style="font-weight:700; font-size:15px; color:{impact_hex}; margin-top:5px;">{impact_word}</div>
                </div>
                <div>
                    <div class="cc-mono" style="font-size:10.5px; letter-spacing:0.07em; text-transform:uppercase; color:var(--cc-text-tertiary);">Cascade Risk</div>
                    <div style="font-weight:700; font-size:15px; color:{cascade_hex}; margin-top:5px;">{cascade_word}</div>
                </div>
                <div>
                    <div class="cc-mono" style="font-size:10.5px; letter-spacing:0.07em; text-transform:uppercase; color:var(--cc-text-tertiary);">Confidence Level</div>
                    <div style="font-weight:700; font-size:15px; color:var(--cc-text-primary); margin-top:5px;">{pred_confidence*100:.1f}%</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ============ DECISION SUPPORT: RECOMMENDED OPERATIONAL RESPONSE ============
    st.markdown(
        f"""
        <div class="cc-panel" style="padding:22px 26px; margin-top:14px; border-left:4px solid {response_hex}; border-color:{response_hex}44;">
            <div class="cc-eyebrow" style="color:{response_hex};">Recommended Operational Response</div>
            <div style="font-family:var(--cc-font-display); font-size:26px; font-weight:700; color:{response_hex}; margin-top:4px; letter-spacing:0.01em;">
                {response_word}
            </div>
            <div class="cc-mono" style="margin-top:8px; font-size:12.5px; color:var(--cc-text-secondary); line-height:1.6; max-width:760px;">
                {response_explainer}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ============ CLASSIFIER PROBABILITY + HISTORICAL EVIDENCE ============
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Prediction breakdown")
    pred_col, evidence_col = st.columns(2, gap="large")

    with pred_col:
        with st.container():
            st.markdown(
                '<div class="cc-panel"><div class="cc-eyebrow">Classifier Probability Distribution</div></div>',
                unsafe_allow_html=True,
            )
            prob_df = pd.DataFrame(
                {
                    "bucket": [BUCKET_LABELS[b] for b in BUCKET_ORDER if b in result.bucket_probabilities],
                    "probability": [result.bucket_probabilities[b] for b in BUCKET_ORDER if b in result.bucket_probabilities],
                }
            )
            st.bar_chart(prob_df.set_index("bucket"))

    with evidence_col:
        with st.container():
            top_neighbor_bucket = max(result.neighbor_bucket_distribution, key=result.neighbor_bucket_distribution.get)
            neighbor_total = sum(result.neighbor_bucket_distribution.values()) or 1
            neighbor_hex = BUCKET_HEX.get(top_neighbor_bucket, "#2DD4E8")
            neighbor_conf = result.neighbor_bucket_distribution[top_neighbor_bucket] / neighbor_total
            st.markdown(
                f"""
                <div class="cc-panel">
                    <div class="cc-eyebrow">Historical Neighbor Outcomes</div>
                    <div style="font-family:var(--cc-font-display); font-size:20px; font-weight:700; color:{neighbor_hex}; text-transform:uppercase;">
                        {BUCKET_LABELS.get(top_neighbor_bucket, "n/a").upper()}
                    </div>
                    <div class="cc-mono" style="margin-bottom:8px;">Most common outcome among similar past events</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            confidence_bar(neighbor_conf, signal=BUCKET_SIGNAL.get(top_neighbor_bucket, "blue"))
            neighbor_df = pd.DataFrame(
                {
                    "bucket": [BUCKET_LABELS[b] for b in result.neighbor_bucket_distribution],
                    "count of 10 nearest neighbors": list(result.neighbor_bucket_distribution.values()),
                }
            )
            st.bar_chart(neighbor_df.set_index("bucket"))

    if pred_bucket not in result.neighbor_bucket_distribution or (
        max(result.neighbor_bucket_distribution, key=result.neighbor_bucket_distribution.get) != pred_bucket
    ):
        st.markdown(
            f"""
            <div class="cc-alert" style="--cc-accent:#F2A623; --cc-accent-glow:rgba(242,166,35,0.28); border-left-color:#F2A623; margin-top:12px;">
                <div class="cc-alert-dot" style="background:#F2A623;"></div>
                <div>
                    <div class="cc-alert-title">{severity_badge("MODEL DISAGREEMENT", "elevated")}</div>
                    <div class="cc-alert-meta" style="margin-top:8px; line-height:1.6;">
                        The classifier's prediction and the nearest-neighbor evidence disagree on the
                        most likely bucket. This can happen because the two layers weight features
                        differently (the classifier leans on event_cause; the neighbor search also
                        weights location and corridor heavily). Treat this as a signal to apply human
                        judgment, not a system error.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============ EVIDENCE TABLE ============
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Evidence: nearest historical events")
    st.caption("Each row is a real past event with matching characteristics, supporting the prediction above.")
    neighbors_display = pd.DataFrame(result.nearest_neighbors)
    if not neighbors_display.empty:
        neighbors_display = neighbors_display.copy()
        neighbors_display["Outcome"] = neighbors_display["duration_bucket"].map(BUCKET_LABELS)
        neighbors_display["Match"] = neighbors_display["duration_bucket"].apply(
            lambda b: "● Matches prediction" if b == pred_bucket else ""
        )
        neighbors_display["Road closure"] = neighbors_display["requires_road_closure"].map({True: "Yes", False: "No"})
        neighbors_display = neighbors_display.rename(
            columns={"event_cause": "Event cause", "corridor": "Corridor"}
        )
        with st.container():
            st.markdown('<div class="cc-panel" style="padding:8px 8px 4px 8px;">', unsafe_allow_html=True)
            st.dataframe(
                neighbors_display[["Event cause", "Corridor", "Road closure", "Outcome", "Match"]],
                use_container_width=True,
                hide_index=True,
            )

    # ============ IMPACT INDEX ============
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Impact index")
    st.caption(result.impact["formula"] + " -- a transparent formula, not a learned model (no severity label exists in the source data).")
    with st.container():
        st.markdown('<div class="cc-panel">', unsafe_allow_html=True)
        impact_top1, impact_top2 = st.columns([1, 2])
        with impact_top1:
            st.markdown(
                f"""
                <div class="cc-severity cc-severity-{impact_level}" style="font-size:13px; padding:7px 16px;">{impact_word}</div>
                <div style="font-family:var(--cc-font-display); font-size:40px; font-weight:700; color:{impact_hex}; margin-top:10px; line-height:1;">
                    {impact_score:.2f}
                </div>
                <div class="cc-mono" style="color:var(--cc-text-tertiary);">composite impact score (0-1)</div>
                """,
                unsafe_allow_html=True,
            )
        with impact_top2:
            components = result.impact["components"]
            rows = [
                ("Road closure required", components["requires_road_closure"], "#FF8A3D"),
                ("Priority flagged high", components["priority_high"], "#F2A623"),
                ("Cause long-closure rate", components["cause_long_closure_rate"], "#2DD4E8"),
            ]
            for label, val, hexcolor in rows:
                pct = max(0.0, min(1.0, float(val))) * 100
                st.markdown(
                    f"""
                    <div style="margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px;">
                            <span class="cc-mono">{label}</span>
                            <span class="cc-mono" style="color:{hexcolor};">{val:.2f}</span>
                        </div>
                        <div class="cc-confidence-track">
                            <div class="cc-confidence-fill" style="width:{pct:.1f}%; background:{hexcolor};"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ============ CASCADE FREQUENCY INDICATOR ============
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Cascade frequency indicator")
    st.caption(f"Source: {result.cascade['source']} (statistical frequency lookup, not a trained model)")
    with st.container():
        st.markdown('<div class="cc-panel">', unsafe_allow_html=True)
        cascade_top1, cascade_top2 = st.columns([1, 2])
        with cascade_top1:
            st.markdown(
                f"""
                <div class="cc-severity cc-severity-{cascade_level}" style="font-size:13px; padding:7px 16px;">{cascade_word}</div>
                <div style="font-family:var(--cc-font-display); font-size:40px; font-weight:700; color:{cascade_hex}; margin-top:10px; line-height:1;">
                    {cascade_pct:.1f}%
                </div>
                <div class="cc-mono" style="color:var(--cc-text-tertiary);">cascade rate within 2hr</div>
                """,
                unsafe_allow_html=True,
            )
        with cascade_top2:
            st.markdown(
                f"""
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:6px;">
                    <div>
                        <div class="cc-mono" style="font-size:10.5px; letter-spacing:0.07em; text-transform:uppercase; color:var(--cc-text-tertiary);">Historical Events</div>
                        <div style="font-family:var(--cc-font-display); font-size:24px; font-weight:600; color:var(--cc-text-primary); margin-top:4px;">{result.cascade['n_events']}</div>
                    </div>
                    <div>
                        <div class="cc-mono" style="font-size:10.5px; letter-spacing:0.07em; text-transform:uppercase; color:var(--cc-text-tertiary);">Median Gap Between Events</div>
                        <div style="font-family:var(--cc-font-display); font-size:24px; font-weight:600; color:var(--cc-text-primary); margin-top:4px;">{result.cascade['median_gap_hours']:.1f} hr</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ============ EXPLAINABILITY + LIMITATIONS ============
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    exp_col1, exp_col2 = st.columns(2, gap="large")
    with exp_col1:
        with st.expander("Explainability: feature importances"):
            importances_df = pd.DataFrame(
                sorted(result.feature_importances.items(), key=lambda x: -x[1]),
                columns=["feature", "importance"],
            )
            st.dataframe(importances_df, use_container_width=True, hide_index=True)
    with exp_col2:
        with st.expander("Disclosed limitations (read before relying on this output)"):
            for limitation in result.disclosed_limitations:
                st.markdown(f"- {limitation}")