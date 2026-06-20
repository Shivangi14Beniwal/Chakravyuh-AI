"""
Active Alerts Feed.

All alerts here are derived from historical aggregates -- there is no live
incident stream in the available data, so this surfaces standing
operational risk patterns (which causes/corridors/junctions carry the
highest historical risk) rather than pretending to be a live 911-style
feed. That distinction is stated on the page rather than implied away.
"""

import streamlit as st

from app.components.widgets import alert_row, divider, severity_badge
from app.services.data_service import (
    get_cause_distribution,
    get_corridor_summary,
    get_top_cascade_junctions,
    get_cascade_rates,
)


def render():
    cause_dist = get_cause_distribution()
    corridor_summary = get_corridor_summary()
    cascade_rates = get_cascade_rates()
    all_junctions = get_top_cascade_junctions(n=10_000)

    n_critical_causes = int((cause_dist[cause_dist["event_count"] >= 15]["long_closure_rate"] > 0.6).sum())
    n_critical_junctions = int((all_junctions["cascade_rate_within_2hr"] > 0.25).sum()) if not all_junctions.empty else 0
    n_critical_corridors = int(
        (corridor_summary[corridor_summary["event_count"] >= 20]["long_closure_share"] > 0.4).sum()
    )
    total_critical = n_critical_causes + n_critical_junctions + n_critical_corridors

    st.markdown(
        f"""
        <div class="cc-hero" style="padding:30px 36px 26px 36px;">
            <div class="cc-hero-eyebrow">Monitoring Center · Standing Risk Patterns</div>
            <div class="cc-hero-title" style="font-size:34px;">Active alerts feed</div>
            <div class="cc-hero-subtitle" style="margin-bottom:14px;">
                Standing risk alerts derived from historical patterns in audited data. This is not
                a live incident stream — the source dataset has no real-time feed — these are the
                causes, corridors, and junctions that warrant attention based on history.
            </div>
            <div class="cc-hero-stats">
                <div class="cc-hero-stat" style="border-color:#FF4D4F44;">
                    <div class="cc-hero-stat-value" style="color:#FF4D4F;">{total_critical}</div>
                    <div class="cc-hero-stat-label">Critical Signals</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_critical_causes}</div>
                    <div class="cc-hero-stat-label">High-Impact Causes</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_critical_junctions}</div>
                    <div class="cc-hero-stat-label">Cascade Hotspots</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_critical_corridors}</div>
                    <div class="cc-hero-stat-label">High-Risk Corridors</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Impact alerts", "Cascade frequency alerts", "High-risk notifications"])

    with tab1:
        st.markdown("#### Impact alerts")
        st.caption("Event causes with the highest derived impact signal (closure-tendency + frequency).")
        significant = cause_dist[cause_dist["event_count"] >= 15].sort_values(
            "long_closure_rate", ascending=False
        )
        for _, row in significant.iterrows():
            rate = row["long_closure_rate"]
            signal = "coral" if rate > 0.6 else "amber" if rate > 0.3 else "green"
            level = "critical" if rate > 0.6 else "elevated" if rate > 0.3 else "nominal"
            badge = severity_badge(f"{'HIGH' if rate > 0.6 else 'MODERATE' if rate > 0.3 else 'LOW'} IMPACT", level)
            alert_row(
                title=f"{row['event_cause'].replace('_', ' ').title()} — {int(row['event_count'])} historical events &nbsp; {badge}",
                meta=f"Extended-closure rate: {rate*100:.1f}%",
                signal=signal,
                critical=(rate > 0.6),
            )

    with tab2:
        st.markdown("#### Cascade frequency alerts")
        st.caption("Junctions where repeat events within a 2-hour window occur most often historically.")
        top_junctions = get_top_cascade_junctions(n=12)
        pop_rate = cascade_rates["_population_fallback"]["cascade_rate_within_2hr"] * 100
        st.markdown(
            f'<div class="cc-panel-alt" style="padding:12px 16px;"><div class="cc-mono">Population baseline cascade rate: <strong style="color:#E9EDF1;">{pop_rate:.1f}%</strong> — junctions below are flagged where they exceed this baseline.</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        if top_junctions.empty:
            st.info("No junctions met the minimum history threshold (5+ events).")
        else:
            for _, row in top_junctions.iterrows():
                pct = row["cascade_rate_within_2hr"] * 100
                signal = "coral" if pct > 25 else "amber" if pct > pop_rate else "blue"
                level = "critical" if pct > 25 else "elevated" if pct > pop_rate else "watch"
                badge = severity_badge("CASCADE RISK" if pct > 25 else "ELEVATED" if pct > pop_rate else "WATCH", level)
                alert_row(
                    title=f"{row['junction']} &nbsp; {badge}",
                    meta=f"Cascade rate {pct:.1f}% · median gap between events {row['median_gap_hours']:.1f}hr · {int(row['n_events'])} events on record",
                    signal=signal,
                    critical=(pct > 25),
                )

    with tab3:
        st.markdown("#### High-risk notifications")
        st.caption("Corridors with the highest share of historically extended closures (6hr or longer).")
        high_risk = corridor_summary[corridor_summary["event_count"] >= 20].sort_values(
            "long_closure_share", ascending=False
        ).head(10)
        for _, row in high_risk.iterrows():
            share = row["long_closure_share"]
            signal = "coral" if share > 0.4 else "amber" if share > 0.2 else "green"
            level = "critical" if share > 0.4 else "elevated" if share > 0.2 else "nominal"
            badge = severity_badge("HIGH RISK" if share > 0.4 else "MODERATE RISK" if share > 0.2 else "LOW RISK", level)
            alert_row(
                title=f"{row['corridor']} &nbsp; {badge}",
                meta=f"{share*100:.1f}% of {int(row['event_count'])} events resolved as extended closures · {row['pct_requires_closure']*100:.1f}% required road closure",
                signal=signal,
                critical=(share > 0.4),
            )

    divider()
    st.caption(
        "All alert thresholds (>60% / >40% / >25%) are fixed display thresholds for this "
        "prototype, chosen for readability of the historical distribution — not statistically "
        "tuned cutoffs."
    )