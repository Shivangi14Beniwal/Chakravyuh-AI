"""
Command center visual theme -- design system v3 (premium control-room upgrade).

UI/UX ONLY. This module emits CSS and a background SVG composite; it
contains no business logic, no data access, and no model code. All
existing class names used by pages/components are preserved so no
calling code needs to change -- only the rules behind those classes
were upgraded.

Design tokens:
  Background base:      #07090D  (near-black, blue undertone, lower noise)
  Background gradient:   radial vignette toward #0B121A
  Panel surface (glass): rgba(18, 26, 35, 0.58), backdrop-blur
  Panel surface (alt):   rgba(22, 31, 42, 0.58), backdrop-blur
  Hairline border:       #1F2B38 / brighter on hover #3D5570

  Traffic-operations accent palette (intelligent, not all-blue):
    Red    #FF4D4F  -- critical
    Orange #FF8A3D  -- congestion
    Amber  #F2A623  -- warning
    Cyan   #2DD4E8  -- normal operations

  Legacy semantic tokens retained (coral/amber/green/blue) for backend
  bucket mapping continuity; cyan/orange/red layered in as the dominant
  traffic-ops voice for chrome, hero, ticker, KPI accents.
"""

COMMAND_CENTER_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;500;700&family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
    --cc-bg: #07090D;
    --cc-bg-2: #0B121A;
    --cc-panel: rgba(18, 26, 35, 0.58);
    --cc-panel-solid: #121A23;
    --cc-panel-alt: rgba(22, 31, 42, 0.58);
    --cc-panel-alt-solid: #161F2A;
    --cc-border: #1F2B38;
    --cc-border-bright: #3D5570;
    --cc-text-primary: #E9EDF1;
    --cc-text-secondary: #8FA0B3;
    --cc-text-tertiary: #586677;

    --cc-coral: #FF4D4F;
    --cc-coral-dim: #6B2024;
    --cc-coral-glow: rgba(255, 77, 79, 0.28);
    --cc-amber: #F2A623;
    --cc-amber-dim: #6B4D11;
    --cc-amber-glow: rgba(242, 166, 35, 0.26);
    --cc-green: #2EBF8C;
    --cc-green-dim: #15523F;
    --cc-green-glow: rgba(46, 191, 140, 0.26);
    --cc-blue: #2DD4E8;
    --cc-blue-dim: #134652;
    --cc-blue-glow: rgba(45, 212, 232, 0.24);
    --cc-orange: #FF8A3D;
    --cc-orange-dim: #6B3B14;
    --cc-orange-glow: rgba(255, 138, 61, 0.26);
    --cc-red: #FF4D4F;
    --cc-red-dim: #6B2024;
    --cc-red-glow: rgba(255, 77, 79, 0.28);
    --cc-cyan: #2DD4E8;
    --cc-cyan-dim: #134652;
    --cc-cyan-glow: rgba(45, 212, 232, 0.24);

    --cc-font-display: 'Roboto Condensed', sans-serif;
    --cc-font-heading: 'Inter', sans-serif;
    --cc-font-body: 'Inter', sans-serif;
    --cc-font-mono: 'Roboto Mono', monospace;

    --cc-radius: 14px;
    --cc-radius-sm: 9px;
    --cc-ease: cubic-bezier(0.22, 1, 0.36, 1);
}

/* ============ BASE SURFACE + LAYERED BACKGROUND (reduced noise) ============ */
.stApp {
    background-color: var(--cc-bg) !important;
    font-family: var(--cc-font-body);
}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: transparent !important;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }

[data-testid="stAppViewContainer"] {
    background-image:
        radial-gradient(ellipse 80% 50% at 50% 0%, rgba(45,212,232,0.035), transparent 60%),
        radial-gradient(ellipse 60% 45% at 100% 100%, rgba(46,191,140,0.025), transparent 60%),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='460' height='460' viewBox='0 0 460 460'%3E%3Cg stroke='%232A3848' stroke-width='0.5' fill='none' opacity='0.06'%3E%3Cpath d='M0 70 L460 100 M0 210 L460 175 M0 350 L460 390'/%3E%3C/g%3E%3C/svg%3E"),
        linear-gradient(180deg, var(--cc-bg) 0%, var(--cc-bg-2) 100%);
    background-size: auto, auto, 460px 460px, cover;
    background-position: top, bottom right, center, center;
    background-repeat: no-repeat, no-repeat, repeat, no-repeat;
    background-attachment: fixed, fixed, fixed, fixed;
}

/* ============ TYPOGRAPHY HIERARCHY ============ */
h1 {
    font-family: var(--cc-font-display) !important;
    color: var(--cc-text-primary) !important;
    font-weight: 500 !important;
    font-size: 28px !important;
    letter-spacing: 0.01em;
    margin-bottom: 4px !important;
}
h2, h3 {
    font-family: var(--cc-font-heading) !important;
    color: var(--cc-text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.005em;
}
h4 {
    font-family: var(--cc-font-heading) !important;
    color: var(--cc-text-primary) !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    letter-spacing: 0.01em;
    margin-top: 28px !important;
    margin-bottom: 10px !important;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--cc-border);
}
p, span, div, label { color: var(--cc-text-primary); }
[data-testid="stCaptionContainer"], .stCaption, small {
    color: var(--cc-text-secondary) !important;
    font-size: 13px !important;
    line-height: 1.55 !important;
}

[data-testid="stVerticalBlock"] > div { margin-bottom: 0; }
.block-container { padding-top: 2.2rem !important; max-width: 1360px; }

/* Kill empty/placeholder Streamlit blocks that render as blank boxes
   (markdown calls that resolve to whitespace-only content) */
[data-testid="stMarkdownContainer"]:empty,
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stMarkdownContainer"]:empty) {
    display: none !important;
}
.element-container:has(> div > div[data-testid="stMarkdownContainer"] > p:empty) {
    display: none !important;
}

/* ============ HERO SECTION ============ */
.cc-hero {
    position: relative;
    border-radius: 18px;
    padding: 36px 40px 30px 40px;
    margin-bottom: 26px;
    background:
        radial-gradient(ellipse 120% 100% at 0% 0%, rgba(45,212,232,0.12), transparent 55%),
        radial-gradient(ellipse 100% 100% at 100% 100%, rgba(255,138,61,0.08), transparent 60%),
        linear-gradient(135deg, #0E151C 0%, #0A1116 100%);
    border: 1px solid var(--cc-border-bright);
    box-shadow: 0 20px 50px rgba(0,0,0,0.35), 0 1px 0 rgba(255,255,255,0.03) inset;
    overflow: hidden;
}
.cc-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='240' viewBox='0 0 500 240'%3E%3Cg stroke='%232DD4E8' stroke-width='0.6' fill='none' opacity='0.06'%3E%3Cpath d='M-20 40 L520 90 M-20 140 L520 110 M-20 220 L520 200'/%3E%3C/g%3E%3C/svg%3E");
    background-size: cover;
    pointer-events: none;
}
.cc-hero-eyebrow {
    font-family: var(--cc-font-mono);
    font-size: 11.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--cc-cyan);
    margin-bottom: 10px;
    position: relative;
    z-index: 1;
}
.cc-hero-title {
    font-family: var(--cc-font-display);
    font-size: 42px;
    font-weight: 700;
    color: var(--cc-text-primary);
    line-height: 1.05;
    letter-spacing: 0.005em;
    margin: 0 0 6px 0;
    position: relative;
    z-index: 1;
}
.cc-hero-subtitle {
    font-family: var(--cc-font-heading);
    font-size: 15.5px;
    font-weight: 500;
    color: var(--cc-text-secondary);
    margin-bottom: 16px;
    position: relative;
    z-index: 1;
    max-width: 920px;
    line-height: 1.55;
}
.cc-hero-tagline {
    font-family: var(--cc-font-mono);
    font-size: 12.5px;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: var(--cc-text-tertiary);
    margin-bottom: 22px;
    position: relative;
    z-index: 1;
}
.cc-hero-tagline span { color: var(--cc-cyan); }
.cc-hero-stats {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    position: relative;
    z-index: 1;
}
.cc-hero-stat {
    background: rgba(255,255,255,0.025);
    border: 1px solid var(--cc-border);
    border-radius: 10px;
    padding: 12px 18px;
    min-width: 160px;
    backdrop-filter: blur(6px);
    transition: border-color 0.25s var(--cc-ease), transform 0.25s var(--cc-ease);
}
.cc-hero-stat:hover { border-color: var(--cc-border-bright); transform: translateY(-2px); }
.cc-hero-stat-value {
    font-family: var(--cc-font-display);
    font-size: 24px;
    font-weight: 600;
    color: var(--cc-text-primary);
    line-height: 1.1;
}
.cc-hero-stat-label {
    font-family: var(--cc-font-mono);
    font-size: 10.5px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--cc-text-tertiary);
    margin-top: 3px;
}

/* ============ GLASSMORPHISM PANELS + CARDS ============ */
.cc-panel, .cc-panel-alt {
    background-color: var(--cc-panel);
    backdrop-filter: blur(11px);
    -webkit-backdrop-filter: blur(11px);
    border: 1px solid var(--cc-border);
    border-radius: var(--cc-radius);
    padding: 20px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 10px 28px rgba(0,0,0,0.22);
    transition: border-color 0.25s var(--cc-ease), box-shadow 0.25s var(--cc-ease), transform 0.25s var(--cc-ease);
}
.cc-panel-alt { background-color: var(--cc-panel-alt); }
.cc-panel:hover, .cc-panel-alt:hover {
    border-color: var(--cc-border-bright);
    box-shadow: 0 1px 0 rgba(255,255,255,0.04) inset, 0 14px 36px rgba(0,0,0,0.30);
    transform: translateY(-1px);
}

.cc-eyebrow {
    font-family: var(--cc-font-mono);
    font-size: 10.5px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--cc-text-tertiary);
    margin-bottom: 8px;
}

.cc-card {
    position: relative;
    background: linear-gradient(160deg, rgba(255,255,255,0.045), rgba(255,255,255,0.005)),
                var(--cc-panel);
    backdrop-filter: blur(13px);
    -webkit-backdrop-filter: blur(13px);
    border: 1px solid var(--cc-border);
    border-radius: var(--cc-radius);
    padding: 18px 20px;
    overflow: hidden;
    transition: transform 0.28s var(--cc-ease), box-shadow 0.28s var(--cc-ease), border-color 0.28s var(--cc-ease);
    box-shadow: 0 10px 26px rgba(0,0,0,0.24);
}
.cc-card::before {
    content: "";
    position: absolute;
    top: -40%; left: -20%;
    width: 70%; height: 180%;
    background: radial-gradient(circle, var(--cc-accent-glow, rgba(45,212,232,0.18)), transparent 70%);
    opacity: 0.85;
    pointer-events: none;
    transition: opacity 0.3s var(--cc-ease);
}
.cc-card::after {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--cc-accent, var(--cc-cyan));
    box-shadow: 0 0 14px var(--cc-accent-glow, rgba(45,212,232,0.55));
}
.cc-card:hover {
    transform: translateY(-4px);
    border-color: var(--cc-border-bright);
    box-shadow: 0 20px 40px rgba(0,0,0,0.36), 0 0 0 1px rgba(255,255,255,0.03) inset;
}
.cc-card:hover::before { opacity: 1; }

.cc-card-label {
    font-family: var(--cc-font-mono);
    font-size: 10.5px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--cc-text-secondary);
    position: relative;
    z-index: 1;
}
.cc-card-value {
    font-family: var(--cc-font-display);
    font-size: 36px;
    font-weight: 600;
    color: var(--cc-text-primary);
    line-height: 1.1;
    margin: 7px 0 4px 0;
    position: relative;
    z-index: 1;
    font-variant-numeric: tabular-nums;
}
.cc-card-sub {
    font-size: 12px;
    color: var(--cc-text-tertiary);
    position: relative;
    z-index: 1;
}

/* Count-up animation keyframe used by JS-driven KPI values */
@keyframes cc-count-fade-in {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}
.cc-count-target { animation: cc-count-fade-in 0.4s var(--cc-ease); }

/* ============ STATUS PILLS + OUTCOME BADGES ============ */
.cc-pill {
    display: inline-block;
    font-family: var(--cc-font-mono);
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.03em;
}
.cc-pill-coral  { background: var(--cc-red-dim); color: #FFC2C3; }
.cc-pill-amber  { background: var(--cc-amber-dim); color: #FBDA9E; }
.cc-pill-green  { background: var(--cc-green-dim); color: #A6EFD8; }
.cc-pill-blue   { background: var(--cc-cyan-dim); color: #B6F0F7; }

.cc-badge {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    font-family: var(--cc-font-display);
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 11px 20px;
    border-radius: 11px;
    border: 1px solid transparent;
}
.cc-badge-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.cc-badge-green { background: linear-gradient(135deg, rgba(46,191,140,0.18), rgba(46,191,140,0.05)); color: #A6EFD8; border-color: rgba(46,191,140,0.35); box-shadow: 0 0 22px rgba(46,191,140,0.10); }
.cc-badge-green .cc-badge-dot { background: var(--cc-green); box-shadow: 0 0 8px var(--cc-green); }
.cc-badge-blue { background: linear-gradient(135deg, rgba(45,212,232,0.18), rgba(45,212,232,0.05)); color: #B6F0F7; border-color: rgba(45,212,232,0.35); box-shadow: 0 0 22px rgba(45,212,232,0.10); }
.cc-badge-blue .cc-badge-dot { background: var(--cc-cyan); box-shadow: 0 0 8px var(--cc-cyan); }
.cc-badge-amber { background: linear-gradient(135deg, rgba(242,166,35,0.20), rgba(242,166,35,0.05)); color: #FBDA9E; border-color: rgba(242,166,35,0.38); box-shadow: 0 0 22px rgba(242,166,35,0.12); }
.cc-badge-amber .cc-badge-dot { background: var(--cc-amber); box-shadow: 0 0 8px var(--cc-amber); }
.cc-badge-coral { background: linear-gradient(135deg, rgba(255,77,79,0.20), rgba(255,77,79,0.05)); color: #FFC2C3; border-color: rgba(255,77,79,0.38); box-shadow: 0 0 22px rgba(255,77,79,0.12); }
.cc-badge-coral .cc-badge-dot { background: var(--cc-red); box-shadow: 0 0 8px var(--cc-red); animation: cc-pulse 1.8s infinite; }

.cc-confidence-track {
    width: 100%;
    height: 6px;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    overflow: hidden;
    margin-top: 10px;
}
.cc-confidence-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.5s var(--cc-ease);
}

.cc-severity {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--cc-font-mono);
    font-size: 10.5px;
    font-weight: 500;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 4px 11px;
    border-radius: 7px;
    border: 1px solid transparent;
}
.cc-severity-critical { background: rgba(255,77,79,0.14); color: #FF9496; border-color: rgba(255,77,79,0.4); }
.cc-severity-elevated { background: rgba(255,138,61,0.14); color: #FFB07F; border-color: rgba(255,138,61,0.4); }
.cc-severity-watch    { background: rgba(45,212,232,0.14); color: #84E7F2; border-color: rgba(45,212,232,0.4); }
.cc-severity-nominal  { background: rgba(46,191,140,0.14); color: #5FE0B5; border-color: rgba(46,191,140,0.4); }

/* ============ ALERT ROWS ============ */
.cc-alert {
    display: flex;
    align-items: flex-start;
    gap: 13px;
    padding: 14px 16px;
    border-radius: 11px;
    border: 1px solid var(--cc-border);
    border-left: 3px solid var(--cc-accent, var(--cc-cyan));
    background: var(--cc-panel-alt);
    backdrop-filter: blur(8px);
    margin-bottom: 9px;
    transition: border-color 0.22s var(--cc-ease), transform 0.22s var(--cc-ease), box-shadow 0.22s var(--cc-ease);
}
.cc-alert:hover {
    border-color: var(--cc-border-bright);
    transform: translateX(3px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.26);
}
.cc-alert-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
}
.cc-alert-dot-critical {
    background: var(--cc-red);
    box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.6);
    animation: cc-pulse 1.8s infinite;
}
@media (prefers-reduced-motion: reduce) { .cc-alert-dot-critical { animation: none; } }
@keyframes cc-pulse {
    0% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.5); }
    70% { box-shadow: 0 0 0 6px rgba(255, 77, 79, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0); }
}
.cc-alert-title { font-family: var(--cc-font-body); font-weight: 600; font-size: 14px; color: var(--cc-text-primary); }
.cc-alert-meta { font-family: var(--cc-font-mono); font-size: 11px; color: var(--cc-text-tertiary); margin-top: 3px; }

/* ============ MONO DATA + TICKER ============ */
.cc-mono { font-family: var(--cc-font-mono); color: var(--cc-text-secondary); font-size: 12.5px; }

.cc-ticker-wrap {
    background: var(--cc-panel-alt);
    backdrop-filter: blur(8px);
    border: 1px solid var(--cc-border);
    border-radius: var(--cc-radius-sm);
    padding: 9px 0;
    overflow: hidden;
    white-space: nowrap;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    box-shadow: 0 6px 18px rgba(0,0,0,0.18);
}
.cc-ticker {
    display: inline-block;
    font-family: var(--cc-font-mono);
    font-size: 12px;
    color: var(--cc-orange);
    padding-left: 100%;
    animation: cc-scroll 38s linear infinite;
}
@media (prefers-reduced-motion: reduce) { .cc-ticker { animation: none; padding-left: 16px; } }
@keyframes cc-scroll { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
.cc-ticker-label {
    font-family: var(--cc-font-mono);
    font-size: 10px;
    letter-spacing: 0.08em;
    color: var(--cc-text-tertiary);
    padding: 0 14px;
    flex-shrink: 0;
    border-right: 1px solid var(--cc-border);
}

/* ============ MISC ============ */
.cc-divider { border-top: 1px solid var(--cc-border); margin: 22px 0; }

.cc-live-dot {
    width: 7px; height: 7px; border-radius: 50%; background: var(--cc-cyan);
    display: inline-block; margin-right: 7px;
    box-shadow: 0 0 0 0 rgba(45, 212, 232, 0.6);
    animation: cc-pulse-green 2.2s infinite;
}
@media (prefers-reduced-motion: reduce) { .cc-live-dot { animation: none; } }
@keyframes cc-pulse-green {
    0% { box-shadow: 0 0 0 0 rgba(45, 212, 232, 0.5); }
    70% { box-shadow: 0 0 0 5px rgba(45, 212, 232, 0); }
    100% { box-shadow: 0 0 0 0 rgba(45, 212, 232, 0); }
}

.cc-rec-card {
    position: relative;
    background: var(--cc-panel-alt);
    backdrop-filter: blur(10px);
    border: 1px solid var(--cc-border);
    border-radius: var(--cc-radius);
    padding: 16px 18px;
    margin-bottom: 10px;
    transition: border-color 0.22s var(--cc-ease), transform 0.22s var(--cc-ease), box-shadow 0.22s var(--cc-ease);
}
.cc-rec-card:hover { border-color: var(--cc-border-bright); transform: translateY(-3px); box-shadow: 0 14px 30px rgba(0,0,0,0.28); }
.cc-rec-rank {
    font-family: var(--cc-font-mono);
    font-size: 10.5px;
    color: var(--cc-text-tertiary);
    letter-spacing: 0.05em;
}

/* Hotspot panel hover (map view) */
.cc-hotspot {
    position: relative;
    background: var(--cc-panel-alt);
    backdrop-filter: blur(10px);
    border: 1px solid var(--cc-border);
    border-radius: 11px;
    padding: 13px 16px;
    margin-bottom: 10px;
    transition: border-color 0.22s var(--cc-ease), transform 0.22s var(--cc-ease), box-shadow 0.22s var(--cc-ease);
}
.cc-hotspot:hover {
    border-color: var(--cc-border-bright);
    transform: translateX(3px) translateY(-1px);
    box-shadow: 0 12px 28px rgba(0,0,0,0.3);
}

/* ============ STREAMLIT WIDGET OVERRIDES ============ */
[data-testid="stSidebar"] {
    background-color: #08090D !important;
    border-right: 1px solid var(--cc-border);
}
[data-testid="stSidebar"] * { color: var(--cc-text-primary); }

.stButton button {
    background-color: var(--cc-panel-alt-solid) !important;
    color: var(--cc-text-primary) !important;
    border: 1px solid var(--cc-border-bright) !important;
    border-radius: var(--cc-radius-sm) !important;
    font-family: var(--cc-font-body) !important;
    font-weight: 500 !important;
    transition: border-color 0.2s var(--cc-ease), box-shadow 0.2s var(--cc-ease), transform 0.15s var(--cc-ease) !important;
}
.stButton button:hover {
    border-color: var(--cc-cyan) !important;
    color: #B6F0F7 !important;
    box-shadow: 0 0 0 1px rgba(45,212,232,0.3), 0 6px 18px rgba(45,212,232,0.12) !important;
    transform: translateY(-1px) !important;
}
.stButton button:active { transform: translateY(0) !important; }

[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, rgba(45,212,232,0.16), rgba(45,212,232,0.04)) !important;
    border-color: rgba(45,212,232,0.4) !important;
}

[data-testid="stMetricValue"] { font-family: var(--cc-font-display) !important; color: var(--cc-text-primary) !important; font-variant-numeric: tabular-nums; }
[data-testid="stMetricLabel"] {
    font-family: var(--cc-font-mono) !important;
    color: var(--cc-text-secondary) !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stDataFrame"] {
    background-color: var(--cc-panel-solid) !important;
    border-radius: var(--cc-radius-sm) !important;
    border: 1px solid var(--cc-border) !important;
}
[data-testid="stDataFrame"]:hover {
    border-color: var(--cc-border-bright) !important;
}

.stSelectbox label, .stSlider label, .stCheckbox label, .stNumberInput label, .stTextInput label {
    font-family: var(--cc-font-mono) !important;
    font-size: 11.5px !important;
    color: var(--cc-text-secondary) !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

[data-baseweb="select"] > div, .stNumberInput input, .stTextInput input {
    background-color: rgba(255,255,255,0.03) !important;
    border-color: var(--cc-border) !important;
    border-radius: var(--cc-radius-sm) !important;
    transition: border-color 0.2s var(--cc-ease) !important;
}
[data-baseweb="select"] > div:hover, .stNumberInput input:hover, .stTextInput input:hover {
    border-color: var(--cc-border-bright) !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid var(--cc-border);
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--cc-font-heading) !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: var(--cc-text-secondary) !important;
    background: transparent !important;
    border-radius: var(--cc-radius-sm) var(--cc-radius-sm) 0 0 !important;
    padding: 10px 18px !important;
    transition: color 0.2s var(--cc-ease), background 0.2s var(--cc-ease) !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--cc-text-primary) !important; background: rgba(255,255,255,0.03) !important; }
.stTabs [aria-selected="true"] {
    color: var(--cc-cyan) !important;
    border-bottom: 2px solid var(--cc-cyan) !important;
}

[data-testid="stExpander"] {
    background-color: var(--cc-panel) !important;
    backdrop-filter: blur(8px);
    border: 1px solid var(--cc-border) !important;
    border-radius: var(--cc-radius-sm) !important;
    transition: border-color 0.2s var(--cc-ease), box-shadow 0.2s var(--cc-ease) !important;
}
[data-testid="stExpander"]:hover { border-color: var(--cc-border-bright) !important; box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important; }
[data-testid="stExpander"] summary { font-family: var(--cc-font-heading) !important; font-weight: 500 !important; }

[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 9px 12px !important;
    border-radius: var(--cc-radius-sm) !important;
    transition: background 0.18s var(--cc-ease) !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,0.04) !important; }

[data-testid="stVegaLiteChart"], .stPlotlyChart {
    background-color: var(--cc-panel-solid) !important;
    border: 1px solid var(--cc-border) !important;
    border-radius: var(--cc-radius-sm) !important;
    padding: 10px !important;
    transition: border-color 0.2s var(--cc-ease) !important;
}
[data-testid="stVegaLiteChart"]:hover { border-color: var(--cc-border-bright) !important; }

[data-testid="stPydeckChart"] {
    border-radius: var(--cc-radius) !important;
    overflow: hidden;
    border: 1px solid var(--cc-border) !important;
    box-shadow: 0 16px 40px rgba(0,0,0,0.4) !important;
}
</style>
"""


def inject_theme():
    import streamlit as st
    st.markdown(COMMAND_CENTER_CSS, unsafe_allow_html=True)