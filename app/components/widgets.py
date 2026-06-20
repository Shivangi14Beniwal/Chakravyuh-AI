"""
Reusable command center UI components, built as small HTML-emitting
functions rather than custom widgets, kept deliberately simple so they
render consistently inside Streamlit's markdown sandbox.
"""

import streamlit as st

_SIGNAL_HEX = {
    "coral": "#E8593C",
    "amber": "#F2A623",
    "blue": "#4DA3F0",
    "green": "#2EBF8C",
}

_SIGNAL_GLOW = {
    "coral": "rgba(232,89,60,0.30)",
    "amber": "rgba(242,166,35,0.28)",
    "blue": "rgba(77,163,240,0.28)",
    "green": "rgba(46,191,140,0.28)",
}

_BUCKET_BADGE_CLASS = {
    "<=1hr": "cc-badge-green",
    "1-6hr": "cc-badge-blue",
    "6-24hr": "cc-badge-amber",
    ">24hr": "cc-badge-coral",
}

_BUCKET_LABEL_TEXT = {
    "<=1hr": "WITHIN 1 HOUR",
    "1-6hr": "1–6 HOURS",
    "6-24hr": "6–24 HOURS",
    ">24hr": "OVER 24 HOURS",
}

_SEVERITY_CLASS = {
    "critical": "cc-severity-critical",
    "elevated": "cc-severity-elevated",
    "watch": "cc-severity-watch",
    "nominal": "cc-severity-nominal",
}


def summary_card(label: str, value: str, sub: str = "", accent: str = "#4DA3F0"):
    glow = accent.replace("#", "")
    try:
        r, g, b = int(glow[0:2], 16), int(glow[2:4], 16), int(glow[4:6], 16)
        accent_glow = f"rgba({r},{g},{b},0.22)"
    except Exception:
        accent_glow = "rgba(77,163,240,0.22)"
    st.markdown(
        f"""
        <div class="cc-card" style="--cc-accent: {accent}; --cc-accent-glow: {accent_glow};">
            <div class="cc-card-label">{label}</div>
            <div class="cc-card-value">{value}</div>
            <div class="cc-card-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(text: str, signal: str = "blue") -> str:
    """Returns the HTML string for a pill -- caller embeds it inline."""
    return f'<span class="cc-pill cc-pill-{signal}">{text}</span>'


def severity_badge(text: str, level: str = "watch") -> str:
    """Returns the HTML string for a severity/priority badge -- caller
    embeds it inline. level in {critical, elevated, watch, nominal}."""
    css_class = _SEVERITY_CLASS.get(level, "cc-severity-watch")
    dot = "● " if level == "critical" else ""
    return f'<span class="cc-severity {css_class}">{dot}{text}</span>'


def outcome_badge(bucket: str, label_override: str = None):
    """Renders a large decision-grade outcome badge for a closure bucket
    (e.g. WITHIN 1 HOUR / 1-6 HOURS / 6-24 HOURS / OVER 24 HOURS)."""
    css_class = _BUCKET_BADGE_CLASS.get(bucket, "cc-badge-blue")
    text = label_override or _BUCKET_LABEL_TEXT.get(bucket, str(bucket).upper())
    st.markdown(
        f"""
        <div class="cc-badge {css_class}">
            <span class="cc-badge-dot"></span>{text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_bar(probability: float, signal: str = "blue"):
    """Renders a thin confidence-meter strip beneath a badge or metric.
    probability is a 0-1 float; caller controls signal/color."""
    pct = max(0.0, min(1.0, probability)) * 100
    color = _SIGNAL_HEX.get(signal, "#4DA3F0")
    st.markdown(
        f"""
        <div class="cc-confidence-track">
            <div class="cc-confidence-fill" style="width:{pct:.1f}%; background:{color};"></div>
        </div>
        <div class="cc-mono" style="margin-top:5px;">{pct:.1f}% confidence</div>
        """,
        unsafe_allow_html=True,
    )


def alert_row(title: str, meta: str, signal: str = "coral", critical: bool = False):
    dot_class = "cc-alert-dot-critical" if critical else ""
    dot_color = _SIGNAL_HEX.get(signal, "#4DA3F0")
    accent_glow = _SIGNAL_GLOW.get(signal, "rgba(77,163,240,0.28)")
    st.markdown(
        f"""
        <div class="cc-alert" style="--cc-accent: {dot_color}; --cc-accent-glow: {accent_glow};">
            <div class="cc-alert-dot {dot_class}" style="background:{dot_color};"></div>
            <div>
                <div class="cc-alert-title">{title}</div>
                <div class="cc-alert-meta">{meta}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_card(rank: int, title: str, meta: str, signal: str = "blue", badge_text: str = None):
    """Executive-style recommendation card for the Decision Support panel."""
    badge_html = f'<span class="cc-severity {_SEVERITY_CLASS.get(signal, "cc-severity-watch")}">{badge_text}</span>' if badge_text else ""
    st.markdown(
        f"""
        <div class="cc-rec-card">
            <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:4px;">
                <div style="font-weight:600; font-size:15px;">{title}</div>
                <div class="cc-rec-rank">RANK {rank}</div>
            </div>
            <div class="cc-mono" style="margin-bottom:6px;">{meta}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_start(eyebrow: str = ""):
    if eyebrow:
        st.markdown(f'<div class="cc-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)


def divider():
    st.markdown('<div class="cc-divider"></div>', unsafe_allow_html=True)


def live_status_line(text: str):
    st.markdown(
        f'<div class="cc-mono"><span class="cc-live-dot"></span>{text}</div>',
        unsafe_allow_html=True,
    )


def junction_ticker(junction_rows):
    """Signature element: scrolling marquee of highest cascade-rate
    junctions, styled like a real traffic-ops dispatch ticker. junction_rows
    is a list of dicts with 'junction', 'cascade_rate_within_2hr', 'n_events'."""
    items = []
    for row in junction_rows:
        pct = row["cascade_rate_within_2hr"] * 100
        items.append(
            f"{row['junction']} — cascade rate {pct:.1f}% ({row['n_events']} historical events)"
        )
    ticker_text = "     ///     ".join(items) if items else "No junction data available"

    st.markdown(
        f"""
        <div class="cc-ticker-wrap">
            <span class="cc-ticker-label">JUNCTION WATCH</span>
            <span class="cc-ticker">{ticker_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )