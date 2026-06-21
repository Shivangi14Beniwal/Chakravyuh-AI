"""
Command Center Homepage.

Reads only: historical events table, metrics.json, cause_tail_weights.json,
cascade_rates.json -- all pre-built frozen artifacts. No model calls happen
here (the classifier is only invoked per-event in the Event Intelligence
Panel); this page summarizes what's already known from history.
"""

import datetime as dt

import streamlit as st

from app.components.widgets import summary_card, alert_row, junction_ticker, divider, live_status_line
from app.services.data_service import (
    get_historical_events,
    get_metrics,
    get_top_cascade_junctions,
    get_cause_distribution,
    get_cascade_rates,
)


def render():
    df = get_historical_events()
    metrics = get_metrics()
    cascade_rates = get_cascade_rates()
    top_junctions = get_top_cascade_junctions(n=10)
    cause_dist = get_cause_distribution()

    total_events = len(df)
    closure_events = int(df["requires_road_closure"].sum())
    long_closure_events = int(df["duration_bucket"].isin(["6-24hr", ">24hr"]).sum())
    high_priority_events = int((df["priority"] == "High").sum())
    n_junctions = len(cascade_rates) - 1
    cv_accuracy_pct = metrics['cv_accuracy_mean'] * 100
    baseline_accuracy_pct = metrics['baseline_accuracy'] * 100

    st.markdown(
        f"""
        <div class="cc-hero">
            <div class="cc-hero-eyebrow">Bengaluru Traffic Police · Operational Intelligence</div>
            <div class="cc-hero-title">CHAKRAVYUH AI</div>
            <div class="cc-hero-subtitle">Traffic Intelligence Platform</div>
            <div class="cc-hero-tagline">Predict <span>•</span> Analyze <span>•</span> Prevent <span>•</span> Respond</div>
            <div class="cc-hero-stats">
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{total_events:,}</div>
                    <div class="cc-hero-stat-label">Historical Events Analyzed</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{cv_accuracy_pct:.1f}%</div>
                    <div class="cc-hero-stat-label">Classifier Accuracy (vs {baseline_accuracy_pct:.1f}% baseline)</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_junctions}</div>
                    <div class="cc-hero-stat-label">Junctions Monitored</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    live_status_line(
        f"Operational — last refreshed {dt.datetime.now().strftime('%d %b %Y, %H:%M')} IST · "
        f"{len(df):,} historical events indexed"
    )

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    junction_ticker(top_junctions.to_dict(orient="records"))

    card_cols = st.columns(4, gap="medium")
    with card_cols[0]:
        summary_card(
            "Events indexed",
            f"{total_events:,}",
            "Historical events with usable closure outcome",
            accent="#2DD4E8",
        )
    with card_cols[1]:
        summary_card(
            "Required road closure",
            f"{closure_events:,}",
            f"{closure_events / total_events * 100:.1f}% of indexed events",
            accent="#FF8A3D",
        )
    with card_cols[2]:
        summary_card(
            "Extended closures",
            f"{long_closure_events:,}",
            "Historically closed 6hr or longer",
            accent="#FF4D4F",
        )
    with card_cols[3]:
        summary_card(
            "High priority",
            f"{high_priority_events:,}",
            f"{high_priority_events / total_events * 100:.1f}% flagged high priority",
            accent="#2EBF8C",
        )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.3, 1], gap="large")

    with left:
        st.markdown("#### Critical attention areas")
        st.caption("Causes with the highest historical rate of extended closure (6hr+), ranked by frequency.")
        top_causes = cause_dist[cause_dist["event_count"] >= 20].sort_values(
            "long_closure_rate", ascending=False
        ).head(5)
        for _, row in top_causes.iterrows():
            signal = "coral" if row["long_closure_rate"] > 0.6 else "amber" if row["long_closure_rate"] > 0.3 else "blue"
            alert_row(
                title=f"{row['event_cause'].replace('_', ' ').title()}",
                meta=f"{row['long_closure_rate']*100:.1f}% historical extended-closure rate · {int(row['event_count'])} events on record",
                signal=signal,
                critical=(row["long_closure_rate"] > 0.6),
            )

    with right:
        st.markdown("#### City operational status")
        st.caption("Closure bucket classifier performance, disclosed plainly.")
        st.markdown(
            f"""
            <div class="cc-panel">
                <div class="cc-eyebrow">Classifier reliability</div>
                <div class="cc-mono">CV accuracy: {metrics['cv_accuracy_mean']*100:.1f}% (baseline {metrics['baseline_accuracy']*100:.1f}%)</div>
                <div class="cc-mono">CV macro-F1: {metrics['cv_macro_f1_mean']*100:.1f}% (baseline {metrics['baseline_macro_f1']*100:.1f}%)</div>
                <div class="cc-divider"></div>
                <div class="cc-eyebrow">Coverage</div>
                <div class="cc-mono">{metrics['n_train'] + metrics['n_test']:,} events with usable duration label</div>
                <div class="cc-divider"></div>
                <div class="cc-eyebrow">Known limitation</div>
                <div class="cc-mono" style="color:#8FA0B3;">{metrics['known_weak_class']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="cc-panel">
                <div class="cc-eyebrow">Cascade monitoring coverage</div>
                <div class="cc-mono">{n_junctions} junctions with sufficient history (5+ events)</div>
                <div class="cc-mono">Population baseline cascade rate: {cascade_rates['_population_fallback']['cascade_rate_within_2hr']*100:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    divider()
    st.caption(
        "All figures on this page are computed directly from the audited historical dataset "
        "(3,182 events with usable closure outcomes) and the frozen classifier evaluation. "
        "Nothing on this screen is a live feed of new incidents — this is a historical "
        "intelligence summary."
    )