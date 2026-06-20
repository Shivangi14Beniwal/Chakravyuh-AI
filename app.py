"""
Chakravyuh AI -- Traffic Command Center.

Main application shell. Provides the persistent navigation rail and
routes to the five command center screens:
    1. Command Center Homepage     (app/pages/home.py)
    2. Bengaluru Map View          (app/pages/map_view.py)
    3. Event Intelligence Panel    (app/pages/event_intelligence.py)
    4. Active Alerts Feed          (app/pages/alerts.py)
    5. Decision Support Panel      (app/pages/decision_support.py)

This file and everything under app/ is the product layer. It consumes
the frozen backend (src/, artifacts/, data/) exclusively through
app/services/data_service.py and src/inference/predict.py -- nothing
here modifies model logic, feature engineering, or training code.
"""

import streamlit as st

from app.theme import inject_theme
from app.pages import home, map_view, event_intelligence, alerts, decision_support

st.set_page_config(
    page_title="Chakravyuh AI — Traffic Command Center",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

PAGES = {
    "Command center": ("🛰", home),
    "Map view": ("🗺", map_view),
    "Event intelligence": ("🔍", event_intelligence),
    "Active alerts": ("🔔", alerts),
    "Decision support": ("📊", decision_support),
}

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 6px 4px 20px 4px;">
            <div style="display:flex; align-items:center; gap:9px;">
                <div style="width:8px; height:8px; border-radius:50%; background:#4DA3F0; box-shadow:0 0 10px #4DA3F0;"></div>
                <div style="font-family:'Roboto Condensed',sans-serif; font-size:20px; font-weight:700; color:#E9EDF1; letter-spacing:0.03em;">
                    CHAKRAVYUH AI
                </div>
            </div>
            <div style="font-family:'Roboto Mono',monospace; font-size:10.5px; color:#586677; letter-spacing:0.07em; margin-top:5px; padding-left:17px;">
                BENGALURU TRAFFIC POLICE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="cc-divider" style="margin:4px 0 16px 0;"></div>', unsafe_allow_html=True)

    nav_labels = [f"{icon}  {name}" for name, (icon, _) in PAGES.items()]
    label_to_key = dict(zip(nav_labels, PAGES.keys()))

    selection_label = st.radio(
        "Navigate",
        nav_labels,
        label_visibility="collapsed",
    )
    selection = label_to_key[selection_label]

    st.markdown('<div class="cc-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="cc-panel-alt" style="padding:14px 16px; backdrop-filter:none;">
            <div class="cc-eyebrow" style="margin-bottom:6px;">System status</div>
            <div class="cc-mono" style="font-size:11px; line-height:1.8;">
                <span class="cc-live-dot"></span>Closure outcome intelligence<br/>
                <span style="padding-left:14px; color:#586677;">Built on audited historical data</span><br/>
                <span style="padding-left:14px; color:#586677;">3,182 events · 8,173 total records</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

PAGES[selection][1].render()