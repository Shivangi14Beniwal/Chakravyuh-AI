"""
Event Intelligence Panel.

Thin page wrapper around app/closure_panel.py, which already implements
event details input, closure outcome prediction, similar historical
events, and explainability -- built and tested in the backend phase.
This file adds only command-center framing around it; the panel's
internal logic is untouched.
"""

import streamlit as st

from app.closure_panel import render_closure_intelligence_panel


def render():
    st.markdown(
        """
        <div class="cc-hero" style="padding:28px 36px 24px 36px;">
            <div class="cc-hero-eyebrow">Operational Intelligence · Per-Event Analysis</div>
            <div class="cc-hero-title" style="font-size:32px;">Event intelligence panel</div>
            <div class="cc-hero-subtitle" style="margin-bottom:0;">
                Enter a new or in-progress event's known fields to retrieve a closure outcome
                estimate, the historical evidence behind it, and the derived impact and cascade
                indicators for the same event.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_closure_intelligence_panel()