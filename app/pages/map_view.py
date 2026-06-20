"""
Bengaluru Map View.

Plots real event-level latitude/longitude from the audited historical
table (model_df_full.csv) -- 3,182 real events, no synthetic points.

Junction-level cascade rates exist in cascade_rates.json but have no
associated coordinates in any frozen artifact, so junctions are NOT
plotted on the map (that would require inventing coordinates). They are
shown instead as a ranked list below the map, by name and real rate.
"""

import pandas as pd
import pydeck as pdk
import streamlit as st

from app.services.data_service import (
    get_historical_events,
    bucket_signal_color,
    get_top_cascade_junctions,
    get_corridor_summary,
)

BENGALURU_CENTER = {"lat": 12.9716, "lon": 77.5946}


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]


def render():
    df = get_historical_events()

    st.markdown(
        """
        <div class="cc-hero" style="padding:30px 36px 26px 36px;">
            <div class="cc-hero-eyebrow">Geospatial Intelligence · Live Map</div>
            <div class="cc-hero-title" style="font-size:34px;">Bengaluru map view</div>
            <div class="cc-hero-subtitle" style="margin-bottom:14px;">
                Event markers plotted from real, audited event coordinates (3,182 events) over a
                live Bengaluru basemap. Color encodes the closure bucket each event actually resolved to.
            </div>
            <div class="cc-hero-stats">
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_events}</div>
                    <div class="cc-hero-stat-label">Events Plotted</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_corridors}</div>
                    <div class="cc-hero-stat-label">Corridors Tracked</div>
                </div>
                <div class="cc-hero-stat">
                    <div class="cc-hero-stat-value">{n_junctions}</div>
                    <div class="cc-hero-stat-label">Junctions Monitored</div>
                </div>
            </div>
        </div>
        """.format(
            n_events=f"{len(df):,}",
            n_corridors=df["corridor"].nunique(),
            n_junctions=len(get_top_cascade_junctions(n=10_000)),
        ),
        unsafe_allow_html=True,
    )

    filter_cols = st.columns(4)
    with filter_cols[0]:
        causes = ["All"] + sorted(df["event_cause"].unique().tolist())
        cause_filter = st.selectbox("Event cause", causes)
    with filter_cols[1]:
        buckets = ["All", "<=1hr", "1-6hr", "6-24hr", ">24hr"]
        bucket_filter = st.selectbox("Closure bucket", buckets)
    with filter_cols[2]:
        closure_filter = st.selectbox("Road closure required", ["All", "Yes", "No"])
    with filter_cols[3]:
        priority_filter = st.selectbox("Priority", ["All", "High", "Low"])

    filtered = df.copy()
    if cause_filter != "All":
        filtered = filtered[filtered["event_cause"] == cause_filter]
    if bucket_filter != "All":
        filtered = filtered[filtered["duration_bucket"] == bucket_filter]
    if closure_filter != "All":
        filtered = filtered[filtered["requires_road_closure"] == (closure_filter == "Yes")]
    if priority_filter != "All":
        filtered = filtered[filtered["priority"] == priority_filter]

    filtered = filtered.copy()
    filtered["color"] = filtered["duration_bucket"].apply(lambda b: _hex_to_rgb(bucket_signal_color(b)))
    filtered["radius"] = filtered["requires_road_closure"].apply(lambda c: 160 if c else 95)
    filtered["glow_color"] = filtered["duration_bucket"].apply(
        lambda b: _hex_to_rgb(bucket_signal_color(b)) + [60]
    )
    filtered["glow_radius"] = filtered["requires_road_closure"].apply(lambda c: 420 if c else 260)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    if filtered.empty:
        st.info("No events match the current filters.")
    else:
        glow_layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered,
            get_position=["longitude", "latitude"],
            get_fill_color="glow_color",
            get_radius="glow_radius",
            pickable=False,
            opacity=0.35,
            stroked=False,
            radius_min_pixels=6,
            radius_max_pixels=40,
        )
        marker_layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered,
            get_position=["longitude", "latitude"],
            get_fill_color="color",
            get_radius="radius",
            pickable=True,
            opacity=0.88,
            stroked=True,
            get_line_color=[233, 237, 241, 130],
            line_width_min_pixels=0.7,
            radius_min_pixels=2.8,
            radius_max_pixels=22,
        )
        view_state = pdk.ViewState(
            latitude=BENGALURU_CENTER["lat"],
            longitude=BENGALURU_CENTER["lon"],
            zoom=10.8,
            pitch=0,
        )
        deck = pdk.Deck(
            layers=[glow_layer, marker_layer],
            initial_view_state=view_state,
            map_provider="carto",
        )
        st.pydeck_chart(deck, height=680, use_container_width=True)

    st.markdown(
        f"""
        <div class="cc-mono" style="margin-top:10px; padding:11px 16px; background:rgba(255,255,255,0.025); border-radius:10px; border:1px solid var(--cc-border); display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
            <span><span style="color:#2EBF8C;">●</span> within 1hr &nbsp;
            <span style="color:#2DD4E8;">●</span> 1-6hr &nbsp;
            <span style="color:#F2A623;">●</span> 6-24hr &nbsp;
            <span style="color:#FF4D4F;">●</span> over 24hr</span>
            <span style="color:#8FA0B3;">larger marker = required road closure &nbsp;·&nbsp; showing <strong style="color:#E9EDF1;">{len(filtered):,}</strong> of {len(df):,} events</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    st.markdown("#### Historical hotspots")
    st.caption("Junctions ranked by historical cascade rate (repeat events within 2hr). Not plotted on the map — no coordinates exist for junctions in the audited dataset.")
    top_junctions = get_top_cascade_junctions(n=8)
    signal_hex = {"coral": "FF4D4F", "amber": "F2A623", "blue": "2DD4E8"}
    if not top_junctions.empty:
        hotspot_cols = st.columns(4, gap="medium")
        for i, (_, row) in enumerate(top_junctions.iterrows()):
            pct = row["cascade_rate_within_2hr"] * 100
            signal = "coral" if pct > 25 else "amber" if pct > 15 else "blue"
            with hotspot_cols[i % 4]:
                st.markdown(
                    f"""
                    <div class="cc-hotspot" style="border-left:3px solid #{signal_hex[signal]};">
                        <div style="font-weight:600; font-size:13.5px;">{row['junction']}</div>
                        <div class="cc-mono" style="color:#{signal_hex[signal]}; margin-top:3px; font-size:14px; font-weight:600;">{pct:.1f}% cascade rate</div>
                        <div class="cc-mono" style="color:#586677;">{int(row['n_events'])} historical events</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    st.markdown("#### Corridor risk overlay")
    st.caption("Share of events per corridor that resolved as extended closures (6hr+).")
    corridor_summary = get_corridor_summary().head(8)
    display = corridor_summary[["corridor", "event_count", "long_closure_share"]].copy()
    display["long_closure_share"] = (display["long_closure_share"] * 100).round(1)
    display.columns = ["Corridor", "Events", "Extended closure %"]
    st.dataframe(display, use_container_width=True, hide_index=True)