"""
Decision Support Panel.

Combines the four frozen modules' outputs into one operator-facing
summary view: the impact index formula and its cause-level weights, the
cascade frequency indicator and its junction-level rates, a historical
evidence summary table, and a ranked list of recommended attention areas
derived purely from the aggregates above (no new scoring logic -- this
page composes existing frozen numbers, it does not compute anything new).
"""

import pandas as pd
import streamlit as st

from app.components.widgets import divider, severity_badge, recommendation_card
from app.services.data_service import (
    get_cause_distribution,
    get_corridor_summary,
    get_top_cascade_junctions,
    get_cascade_rates,
    get_cause_tail_weights,
    get_historical_events,
)


def render():
    cause_dist = get_cause_distribution()
    corridor_summary = get_corridor_summary()
    top_junctions_all = get_top_cascade_junctions(n=10_000)

    n_high_impact_causes = int((cause_dist[cause_dist["event_count"] >= 15]["long_closure_rate"] > 0.6).sum())
    n_cascade_hotspots = int((top_junctions_all["cascade_rate_within_2hr"] > 0.25).sum()) if not top_junctions_all.empty else 0
    n_high_risk_corridors = int(
        (corridor_summary[corridor_summary["event_count"] >= 20]["long_closure_share"] > 0.4).sum()
    )
    total_attention_items = n_high_impact_causes + n_cascade_hotspots + n_high_risk_corridors

    st.markdown(
        f"""
        <div class="cc-hero" style="padding:30px 36px 26px 36px;">
            <div class="cc-hero-eyebrow">Executive View · Composed Intelligence</div>
            <div class="cc-hero-title" style="font-size:34px;">Decision support panel</div>
            <div class="cc-hero-subtitle" style="margin-bottom:14px;">
                A composed view of the impact index, cascade frequency indicator, and historical
                evidence, ending in a ranked list of operational attention areas. Every number here
                traces back to the audited dataset or a frozen, disclosed formula.
            </div>
            <div class="cc-hero-stats">
                <div class="cc-hero-stat" style="border-color:#FF4D4F44;">
                    <div class="cc-hero-stat-value" style="color:#FF4D4F;">{total_attention_items}</div>
                    <div class="cc-hero-stat-label">Total Attention Items</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_high_impact_causes}</div>
                    <div class="cc-hero-stat-label">High-Impact Causes</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_cascade_hotspots}</div>
                    <div class="cc-hero-stat-label">Cascade Hotspots</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_high_risk_corridors}</div>
                    <div class="cc-hero-stat-label">High-Risk Corridors</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section1, section2 = st.columns(2, gap="large")

    with section1:
        st.markdown("#### Impact index — cause weights")
        st.caption("0.4 × closure-required + 0.3 × priority-high + 0.3 × cause long-closure rate. The third term is shown below per cause.")
        weights = get_cause_tail_weights()
        weight_rows = [
            {"event_cause": k.replace("_", " ").title(), "long_closure_rate": v}
            for k, v in weights.items()
            if k != "_default"
        ]
        weight_df = pd.DataFrame(weight_rows).sort_values("long_closure_rate", ascending=False)
        weight_df["long_closure_rate"] = (weight_df["long_closure_rate"] * 100).round(1)
        weight_df.columns = ["Event cause", "Long-closure rate %"]
        st.markdown('<div class="cc-panel">', unsafe_allow_html=True)
        st.dataframe(weight_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with section2:
        st.markdown("#### Cascade frequency indicator — top junctions")
        st.caption("Share of consecutive same-junction events occurring within a 2-hour window.")
        cascade_rates = get_cascade_rates()
        top_junctions = get_top_cascade_junctions(n=10)
        st.markdown('<div class="cc-panel">', unsafe_allow_html=True)
        display = top_junctions.copy()
        if not display.empty:
            display["cascade_rate_within_2hr"] = (display["cascade_rate_within_2hr"] * 100).round(1)
            display = display[["junction", "n_events", "cascade_rate_within_2hr", "median_gap_hours"]]
            display.columns = ["Junction", "Events", "Cascade rate %", "Median gap (hr)"]
            st.dataframe(display, use_container_width=True, hide_index=True)
        st.markdown(
            f'<div class="cc-mono">Population fallback (used when junction unknown): '
            f'<strong style="color:#E9EDF1;">{cascade_rates["_population_fallback"]["cascade_rate_within_2hr"]*100:.1f}%</strong> cascade rate</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    divider()

    st.markdown("#### Historical evidence summary")
    st.caption("Aggregated counts by event cause, the basis for both the impact index and the alerts feed.")
    df = get_historical_events()
    bucket_mix = (
        df.groupby("event_cause")["duration_bucket"]
        .value_counts(normalize=True)
        .unstack(fill_value=0)
        .reindex(columns=["<=1hr", "1-6hr", "6-24hr", ">24hr"], fill_value=0)
        * 100
    ).round(1)
    bucket_mix = bucket_mix.reset_index()
    summary = cause_dist.merge(bucket_mix, on="event_cause", how="left")
    summary["event_cause"] = summary["event_cause"].str.replace("_", " ").str.title()
    summary["long_closure_rate"] = (summary["long_closure_rate"] * 100).round(1)
    summary.columns = [
        "Event cause", "Events", "Long-closure rate %",
        "≤1hr %", "1-6hr %", "6-24hr %", ">24hr %",
    ]
    st.markdown('<div class="cc-panel">', unsafe_allow_html=True)
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    divider()

    st.markdown("#### Recommended operational attention areas")
    st.caption(
        "Ranked by combining: (a) high long-closure rate causes, (b) high-cascade junctions, "
        "and (c) high extended-closure corridors. Pure composition of the tables above — no "
        "additional scoring."
    )

    rank = 1

    top_cause = cause_dist[cause_dist["event_count"] >= 15].sort_values(
        "long_closure_rate", ascending=False
    ).head(3)
    for _, row in top_cause.iterrows():
        rate = row["long_closure_rate"]
        level = "critical" if rate > 0.6 else "elevated" if rate > 0.3 else "watch"
        recommendation_card(
            rank=rank,
            title=f"{row['event_cause'].replace('_', ' ').title()} — dispatch protocol review",
            meta=f"{rate*100:.1f}% historical extended-closure rate across {int(row['event_count'])} events — consider faster initial dispatch protocols.",
            signal=level,
            badge_text="HIGH IMPACT CAUSE" if rate > 0.6 else "MODERATE IMPACT CAUSE",
        )
        rank += 1

    top_junc = get_top_cascade_junctions(n=3)
    for _, row in top_junc.iterrows():
        pct = row["cascade_rate_within_2hr"] * 100
        level = "critical" if pct > 25 else "elevated"
        recommendation_card(
            rank=rank,
            title=f"{row['junction']} — standing patrol consideration",
            meta=f"{pct:.1f}% historical cascade rate within 2 hours — consider standing patrol or pre-positioned response during peak hours.",
            signal=level,
            badge_text="CASCADE HOTSPOT",
        )
        rank += 1

    top_corridor = corridor_summary[corridor_summary["event_count"] >= 20].sort_values(
        "long_closure_share", ascending=False
    ).head(2)
    for _, row in top_corridor.iterrows():
        share = row["long_closure_share"]
        level = "critical" if share > 0.4 else "elevated"
        recommendation_card(
            rank=rank,
            title=f"{row['corridor']} — alternate-route signage",
            meta=f"{share*100:.1f}% of events historically resolve as extended closures — consider alternate-route signage pre-staged for this corridor.",
            signal=level,
            badge_text="HIGH-RISK CORRIDOR",
        )
        rank += 1

    divider()
    st.caption(
        "This panel composes existing frozen module outputs (impact index, cascade indicator, "
        "historical aggregates) into recommendations. It does not run any additional model or "
        "scoring beyond what is already computed in the backend."
    )