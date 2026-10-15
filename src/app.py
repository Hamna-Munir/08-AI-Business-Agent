"""
app.py
Streamlit front-end for the AI Business Agent — "Ledger" (v6).

Run with:
    streamlit run src/app.py
"""

import sys
import textwrap
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent import BusinessAgent
from src.database import build_database

st.set_page_config(page_title="Ledger — AI Business Agent", page_icon="◆", layout="wide")

# ---------------------------------------------------------------------------
# Themes — every colour in the UI comes from these CSS variables
# ---------------------------------------------------------------------------
THEMES = {
    "Midnight": {
        "ink": "#080C16", "glass": "rgba(17,24,39,0.72)", "glass2": "rgba(17,24,39,0.55)",
        "line": "rgba(255,255,255,0.08)", "line-soft": "rgba(255,255,255,0.05)",
        "text": "#EEF2F7", "soft": "#B4BECF", "muted": "#7A869B",
        "a": "#2DD4BF", "a2": "#F2765A", "a-grad": "#22B8E0", "a-ink": "#05201C",
        "a-dim": "rgba(45,212,191,0.12)", "a2-dim": "rgba(242,118,90,0.14)", "glow": "rgba(45,212,191,0.30)",
        "grid": "rgba(255,255,255,0.028)", "code-bg": "#080C16", "tile-bg": "rgba(8,12,22,0.5)",
        "shadow": "rgba(0,0,0,0.8)", "aur1": "rgba(45,212,191,0.15)", "aur2": "rgba(242,118,90,0.10)",
        "art-panel": "#111827", "art-stroke": "#2A3550", "art-grid": "#1B2540", "pill-bg": "#0B1220",
    },
    "Aurora": {
        "ink": "#0A0615", "glass": "rgba(26,17,48,0.72)", "glass2": "rgba(26,17,48,0.55)",
        "line": "rgba(255,255,255,0.09)", "line-soft": "rgba(255,255,255,0.05)",
        "text": "#F4F0FC", "soft": "#C6BDDC", "muted": "#8D82AA",
        "a": "#A78BFA", "a2": "#F472B6", "a-grad": "#7C5CFF", "a-ink": "#140A2E",
        "a-dim": "rgba(167,139,250,0.14)", "a2-dim": "rgba(244,114,182,0.14)", "glow": "rgba(139,92,246,0.38)",
        "grid": "rgba(255,255,255,0.03)", "code-bg": "#0A0615", "tile-bg": "rgba(10,6,21,0.5)",
        "shadow": "rgba(0,0,0,0.8)", "aur1": "rgba(124,92,255,0.22)", "aur2": "rgba(244,114,182,0.14)",
        "art-panel": "#150E2B", "art-stroke": "#35295A", "art-grid": "#241A44", "pill-bg": "#0F0820",
    },
    "Daylight": {
        "ink": "#F5F6FB", "glass": "rgba(255,255,255,0.88)", "glass2": "rgba(255,255,255,0.7)",
        "line": "rgba(15,23,42,0.10)", "line-soft": "rgba(15,23,42,0.06)",
        "text": "#0F172A", "soft": "#334155", "muted": "#64748B",
        "a": "#0E9F8E", "a2": "#E4572E", "a-grad": "#0B7FBF", "a-ink": "#FFFFFF",
        "a-dim": "rgba(14,159,142,0.10)", "a2-dim": "rgba(228,87,46,0.10)", "glow": "rgba(14,159,142,0.28)",
        "grid": "rgba(15,23,42,0.045)", "code-bg": "#F1F5F9", "tile-bg": "rgba(241,245,249,0.8)",
        "shadow": "rgba(15,23,42,0.18)", "aur1": "rgba(14,159,142,0.12)", "aur2": "rgba(228,87,46,0.08)",
        "art-panel": "#FFFFFF", "art-stroke": "#D5DBE6", "art-grid": "#E6EAF2", "pill-bg": "#F1F5F9",
    },
}
THEME_NAMES = list(THEMES.keys())

# The theme is read from the previous run's widget value (the radio is created further down).
active_theme = st.session_state.get("theme") or st.session_state.get("_theme_last", THEME_NAMES[0])
if active_theme not in THEMES:
    active_theme = THEME_NAMES[0]


def _on_theme_change() -> None:
    # segmented control can be deselected (None) — keep the last chosen theme in that case
    value = st.session_state.get("theme")
    if value is None:
        st.session_state["theme"] = st.session_state.get("_theme_last", THEME_NAMES[0])
    else:
        st.session_state["_theme_last"] = value

ROOT_CSS = ":root {" + "".join(f"--{k}: {v};" for k, v in THEMES[active_theme].items()) + "}"

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; height: 0; }
[data-testid="stSidebar"] { display: none; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ---------- Atmosphere ---------- */
.stApp {
    background:
        radial-gradient(900px 520px at 88% -8%, var(--aur1), transparent 60%),
        radial-gradient(700px 500px at -6% 12%, var(--aur2), transparent 60%),
        var(--ink);
    color: var(--text);
}
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image: linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px);
    background-size: 46px 46px;
    -webkit-mask-image: radial-gradient(ellipse at 50% 0%, #000 15%, transparent 72%);
    mask-image: radial-gradient(ellipse at 50% 0%, #000 15%, transparent 72%);
}
.block-container { position: relative; z-index: 1; max-width: 1060px; padding-top: 1.4rem; padding-bottom: 4rem; }
.stApp p, .stApp li, .stApp label, .stApp span { color: inherit; }
[data-testid="stSpinner"], [data-testid="stSpinner"] * { color: var(--soft) !important; }

/* ---------- Top bar ---------- */
.st-key-topbar {
    border: 1px solid var(--line); border-radius: 14px; padding: 0.7rem 1.1rem; margin-bottom: 2.4rem;
    background: var(--glass); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
.lg-brand { display: flex; align-items: center; gap: 0.7rem; }
.lg-mark .m1 { fill: var(--a); }
.lg-mark .m2 { fill: var(--a2); }
.lg-wordmark { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 700; color: var(--text); line-height: 1; letter-spacing: -0.01em; }
.lg-status { display: flex; align-items: center; gap: 0.9rem; }
.lg-live { display: flex; align-items: center; gap: 0.45rem; font-size: 0.76rem; color: var(--soft); white-space: nowrap; }
.lg-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--a); box-shadow: 0 0 0 3px var(--a-dim); }
.lg-pill {
    font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--soft); white-space: nowrap;
    border: 1px solid var(--line); border-radius: 999px; padding: 0.28rem 0.75rem; background: var(--tile-bg);
}

/* Theme switcher: segmented control (works for st.segmented_control and the st.radio fallback) */
.st-key-themebox { display: flex; justify-content: flex-end; }
.st-key-themebox [data-testid="stButtonGroup"], .st-key-themebox div[role="radiogroup"] {
    display: inline-flex !important; flex-wrap: nowrap; width: auto; gap: 0.2rem; padding: 0.25rem;
    background: var(--tile-bg); border: 1px solid var(--line); border-radius: 999px;
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
}
.st-key-themebox [data-testid="stRadio"] > label { display: none; }
.st-key-themebox button[data-testid^="stBaseButton-segmented_control"],
.st-key-themebox label[data-baseweb="radio"] {
    background: transparent !important; border: 1px solid transparent !important; border-radius: 999px !important;
    padding: 0.42rem 1.15rem !important; min-height: 0 !important; margin: 0 !important; box-shadow: none !important;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: background 0.2s ease, box-shadow 0.2s ease;
}
/* text: one clean font, always readable in every theme */
.st-key-themebox button[data-testid^="stBaseButton-segmented_control"] *,
.st-key-themebox label[data-baseweb="radio"] p,
.st-key-themebox label[data-baseweb="radio"] [data-testid="stMarkdownContainer"] {
    font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; font-weight: 500 !important;
    letter-spacing: 0.01em; color: var(--soft) !important; margin: 0 !important; white-space: nowrap; transition: color 0.2s ease;
}
/* hide the default radio circle (fallback mode) */
.st-key-themebox label[data-baseweb="radio"] > div:not(:has([data-testid="stMarkdownContainer"])),
.st-key-themebox label[data-baseweb="radio"] > span { display: none !important; }
/* hover */
.st-key-themebox button[data-testid^="stBaseButton-segmented_control"]:hover,
.st-key-themebox label[data-baseweb="radio"]:hover { background: var(--a-dim) !important; }
.st-key-themebox button[data-testid^="stBaseButton-segmented_control"]:hover *,
.st-key-themebox label[data-baseweb="radio"]:hover p { color: var(--text) !important; }
/* selected */
.st-key-themebox button[data-testid="stBaseButton-segmented_controlActive"],
.st-key-themebox button[aria-pressed="true"],
.st-key-themebox label[data-baseweb="radio"]:has(input:checked) {
    background: linear-gradient(135deg, var(--a) 0%, var(--a-grad) 100%) !important;
    box-shadow: 0 6px 18px -6px var(--glow) !important;
}
.st-key-themebox button[data-testid="stBaseButton-segmented_controlActive"] *,
.st-key-themebox button[aria-pressed="true"] *,
.st-key-themebox label[data-baseweb="radio"]:has(input:checked) p { color: var(--a-ink) !important; font-weight: 600 !important; }
.st-key-themebox button:focus-visible, .st-key-themebox label:has(input:focus-visible) { outline: 2px solid var(--a) !important; outline-offset: 2px; }

/* ---------- Hero ---------- */
.lg-hero-grid { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 2.2rem; align-items: center; margin-bottom: 2.2rem; }
.lg-hero-copy h1 {
    font-family: 'Space Grotesk', sans-serif; font-size: 3.1rem; font-weight: 700; line-height: 1.08;
    letter-spacing: -0.03em; color: var(--text); margin: 0 0 1rem 0; padding: 0;
    animation: rise 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
.lg-hero-copy p { font-size: 1.02rem; line-height: 1.65; color: var(--soft); margin: 0; max-width: 46ch; animation: rise 0.7s 0.1s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* Hero art */
.lg-art { width: 100%; height: auto; display: block; filter: drop-shadow(0 30px 50px var(--glow)); }
.lg-art .panel { fill: var(--art-panel); stroke: var(--art-stroke); }
.lg-art .axis { stroke: var(--art-stroke); }
.lg-art .gridline { stroke: var(--art-grid); }
.lg-art .s-a1 { stop-color: var(--a); }
.lg-art .s-a2 { stop-color: var(--a2); }
.lg-art .dot-a2 { fill: var(--a2); }
.lg-art .dot-a { fill: var(--a); }
.lg-art .dot-ring { stroke: var(--art-panel); }
.lg-art .trend { stroke: var(--text); }
.lg-art .pill { fill: var(--pill-bg); stroke: var(--art-stroke); }
.lg-art .pill-text { fill: var(--soft); }
.lg-art .bar { transform-origin: center bottom; transform-box: fill-box; animation: grow 0.9s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
.lg-art .b1 { animation-delay: 0.05s; } .lg-art .b2 { animation-delay: 0.15s; } .lg-art .b3 { animation-delay: 0.25s; }
.lg-art .b4 { animation-delay: 0.35s; } .lg-art .b5 { animation-delay: 0.45s; } .lg-art .b6 { animation-delay: 0.55s; } .lg-art .b7 { animation-delay: 0.65s; }
.lg-art .lg-line { stroke-dasharray: 100; stroke-dashoffset: 100; animation: draw 1.5s 0.8s ease forwards; }
.lg-art .lg-pulse { transform-origin: center; transform-box: fill-box; animation: pulse 1.9s 2s ease-out infinite; }
@keyframes grow { from { transform: scaleY(0); } to { transform: scaleY(1); } }
@keyframes draw { to { stroke-dashoffset: 0; } }
@keyframes pulse { 0% { transform: scale(1); opacity: 0.65; } 100% { transform: scale(3); opacity: 0; } }
@media (prefers-reduced-motion: reduce) {
    .lg-art .bar, .lg-art .lg-pulse, .lg-hero-copy h1, .lg-hero-copy p, [class*="st-key-card"], .lg-stepcard { animation: none !important; }
    .lg-art .lg-line { animation: none !important; stroke-dashoffset: 0; }
}

/* ---------- Command bar ---------- */
.st-key-cmd {
    background: var(--glass); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--line); border-radius: 18px; padding: 1.1rem 1.1rem 0.9rem 1.1rem;
    box-shadow: 0 24px 70px -28px var(--glow);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.st-key-cmd:focus-within { border-color: var(--a); box-shadow: 0 0 0 4px var(--a-dim), 0 24px 70px -24px var(--glow); }
.st-key-cmd [data-testid="stTextArea"] div { background: transparent !important; border: none !important; box-shadow: none !important; }
.st-key-cmd [data-testid="stTextArea"] { background: var(--tile-bg) !important; border: 1px solid var(--line-soft); border-radius: 12px; overflow: hidden; }
.st-key-cmd textarea {
    background: transparent !important; color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; caret-color: var(--a); border: none !important; box-shadow: none !important;
    font-family: 'Inter', sans-serif !important; font-size: 1.1rem !important; line-height: 1.5 !important; padding: 0.3rem 0.4rem !important;
}
.st-key-cmd textarea::placeholder { color: var(--muted) !important; opacity: 1; }
.lg-hint { font-size: 0.78rem; color: var(--muted); padding-top: 0.55rem; }

/* ---------- Buttons ---------- */
div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, var(--a) 0%, var(--a-grad) 100%) !important; color: var(--a-ink) !important; border: none !important;
    font-weight: 600 !important; border-radius: 11px !important; padding: 0.55rem 1.3rem !important;
    box-shadow: 0 8px 24px -8px var(--glow); transition: transform 0.15s ease, box-shadow 0.15s ease;
}
div[data-testid="stButton"] button[kind="primary"] p { color: var(--a-ink) !important; }
div[data-testid="stButton"] button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 12px 28px -8px var(--glow); }
div[data-testid="stButton"] button:not([kind="primary"]), [data-testid="stDownloadButton"] button {
    background: var(--glass2); color: var(--soft); border: 1px solid var(--line);
    border-radius: 999px; font-size: 0.78rem; font-weight: 500; padding: 0.3rem 0.9rem; transition: border-color 0.15s ease, color 0.15s ease;
}
div[data-testid="stButton"] button:not([kind="primary"]) p, [data-testid="stDownloadButton"] button p { color: inherit; }
div[data-testid="stButton"] button:not([kind="primary"]):hover, [data-testid="stDownloadButton"] button:hover { border-color: var(--a); color: var(--a); }
div[data-testid="stButton"] button:focus-visible, [data-testid="stDownloadButton"] button:focus-visible { outline: 2px solid var(--a); outline-offset: 2px; }

/* ---------- Example cards ---------- */
.lg-label { font-size: 0.82rem; color: var(--muted); margin: 1.6rem 0 0.6rem 0; }
.st-key-examples div[data-testid="stButton"] button:not([kind="primary"]) {
    width: 100%; min-height: 3.6rem; text-align: left; justify-content: flex-start; border-radius: 14px;
    padding: 0.8rem 1rem; font-size: 0.9rem; color: var(--soft); background: var(--glass2); border: 1px solid var(--line);
}
.st-key-examples div[data-testid="stButton"] button:not([kind="primary"]):hover { border-color: var(--a); color: var(--text); background: var(--a-dim); transform: translateY(-1px); }

/* ---------- How it works ---------- */
.lg-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.1rem; margin-top: 2.4rem; }
.lg-stepcard {
    position: relative; overflow: hidden; padding: 1.5rem 1.4rem 1.4rem 1.4rem; border-radius: 18px;
    border: 1px solid var(--line); background: var(--glass);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    transition: transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1), border-color 0.25s ease, box-shadow 0.35s ease;
    animation: rise 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
.lg-stepcard:nth-child(2) { animation-delay: 0.1s; }
.lg-stepcard:nth-child(3) { animation-delay: 0.2s; }
/* top gradient line: slides in left to right on hover */
.lg-stepcard::before {
    content: ""; position: absolute; left: 0; right: 0; top: 0; height: 2px;
    background: linear-gradient(90deg, var(--a), var(--a2));
    transform: scaleX(0); transform-origin: left; transition: transform 0.45s cubic-bezier(0.2, 0.8, 0.2, 1);
}
/* corner glow */
.lg-stepcard::after {
    content: ""; position: absolute; right: -60px; top: -60px; width: 180px; height: 180px; border-radius: 50%;
    background: radial-gradient(circle, var(--a-dim), transparent 70%); opacity: 0; transition: opacity 0.35s ease; pointer-events: none;
}
.lg-stepcard:hover {
    transform: translateY(-8px); border-color: var(--a);
    box-shadow: 0 30px 60px -30px var(--glow), 0 0 0 1px var(--a-dim);
}
.lg-stepcard:hover::before { transform: scaleX(1); }
.lg-stepcard:hover::after { opacity: 1; }

.lg-stepicon {
    width: 46px; height: 46px; border-radius: 13px; display: grid; place-items: center;
    background: var(--a-dim); color: var(--a); border: 1px solid var(--line-soft);
    transition: transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1), background 0.25s ease, color 0.25s ease;
}
.lg-stepicon svg { width: 22px; height: 22px; }
.lg-stepcard:hover .lg-stepicon {
    transform: rotate(-6deg) scale(1.1);
    background: linear-gradient(135deg, var(--a), var(--a-grad)); color: var(--a-ink);
}
.lg-stepnum {
    position: absolute; right: 1.2rem; top: 0.9rem; font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem; font-weight: 700; line-height: 1; color: var(--text); opacity: 0.06;
    transition: opacity 0.3s ease, transform 0.35s ease;
}
.lg-stepcard:hover .lg-stepnum { opacity: 0.16; transform: translateY(-3px); }
.lg-steptitle { font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 600; color: var(--text); margin: 1.1rem 0 0.4rem 0; }
.lg-stepbody { font-size: 0.86rem; line-height: 1.6; color: var(--muted); transition: color 0.25s ease; }
.lg-stepcard:hover .lg-stepbody { color: var(--soft); }

/* ---------- Results header ---------- */
.lg-results-head { font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 600; color: var(--text); margin: 2.6rem 0 0.3rem 0; letter-spacing: -0.01em; }

/* ---------- Result card ---------- */
[class*="st-key-card"] {
    position: relative; background: var(--glass); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    border: 1px solid var(--line); border-radius: 18px; padding: 1.4rem 1.6rem 0.8rem 1.6rem; margin-bottom: 1.4rem;
    box-shadow: 0 20px 60px -30px var(--shadow);
    animation: rise 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
[class*="st-key-card"]::before {
    content: ""; position: absolute; left: 1.6rem; right: 1.6rem; top: 0; height: 2px; border-radius: 2px;
    background: linear-gradient(90deg, var(--a), var(--a2) 45%, transparent 85%);
}
.lg-card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.7rem; }
.lg-category { font-size: 0.74rem; font-weight: 500; border-radius: 999px; padding: 0.18rem 0.75rem; }
.lg-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--muted); }
.lg-question { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 600; letter-spacing: -0.015em; color: var(--text); line-height: 1.25; margin-bottom: 1rem; }
.lg-tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1.1rem; }
.lg-tile { border: 1px solid var(--line-soft); border-radius: 12px; padding: 0.7rem 0.9rem; background: var(--tile-bg); }
.lg-tile b { display: block; font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--text); line-height: 1.1; }
.lg-tile span { font-size: 0.74rem; color: var(--muted); }

/* Report typography */
[class*="st-key-card"] [data-testid="stMarkdownContainer"] { max-width: 78ch; }
[class*="st-key-card"] [data-testid="stMarkdownContainer"] p,
[class*="st-key-card"] [data-testid="stMarkdownContainer"] li { font-size: 0.95rem; line-height: 1.75; color: var(--soft); }
[class*="st-key-card"] [data-testid="stMarkdownContainer"] strong { color: var(--text); font-weight: 600; }
[class*="st-key-card"] [data-testid="stMarkdownContainer"] h1,
[class*="st-key-card"] [data-testid="stMarkdownContainer"] h2,
[class*="st-key-card"] [data-testid="stMarkdownContainer"] h3 {
    font-family: 'Space Grotesk', sans-serif; color: var(--text); letter-spacing: -0.01em;
    font-size: 1.1rem; font-weight: 600; margin: 1.5rem 0 0.35rem 0; padding: 0 0 0 0.75rem; border-left: 2px solid var(--a);
}
[class*="st-key-card"] [data-testid="stMarkdownContainer"] table { border-collapse: collapse; width: 100%; margin: 0.7rem 0; font-size: 0.88rem; }
[class*="st-key-card"] [data-testid="stMarkdownContainer"] th { text-align: left; color: var(--muted); font-weight: 500; border-bottom: 1px solid var(--line); padding: 0.5rem 0.65rem; background: transparent; }
[class*="st-key-card"] [data-testid="stMarkdownContainer"] td { border-bottom: 1px solid var(--line-soft); padding: 0.5rem 0.65rem; color: var(--soft); background: transparent; }
[class*="st-key-card"] [data-testid="stMarkdownContainer"] a { color: var(--a); }
[class*="st-key-card"] [data-testid="stMarkdownContainer"] code { background: var(--code-bg); color: var(--a); padding: 0.1rem 0.35rem; border-radius: 4px; font-size: 0.82rem; }

/* ---------- Agent work timeline ---------- */
[data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 12px !important; background: var(--tile-bg) !important; margin: 1rem 0 0.8rem 0; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p, [data-testid="stExpander"] summary svg { font-size: 0.86rem; color: var(--soft); }
[data-testid="stExpander"] summary:hover, [data-testid="stExpander"] summary:hover p { color: var(--a); }
.lg-tl { position: relative; margin: 0.5rem 0 0.3rem 0.45rem; padding-left: 1.5rem; border-left: 1px solid var(--line); }
.lg-step { position: relative; margin-bottom: 1.1rem; }
.lg-step::before { content: ""; position: absolute; left: calc(-1.5rem - 5px); top: 0.3rem; width: 9px; height: 9px; border-radius: 50%; background: var(--a); box-shadow: 0 0 0 3px var(--a-dim); }
.lg-step.alt::before { background: var(--a2); box-shadow: 0 0 0 3px var(--a2-dim); }
.lg-step-title { font-size: 0.88rem; font-weight: 500; color: var(--text); }
.lg-step-sub { font-size: 0.8rem; color: var(--muted); margin-top: 0.15rem; line-height: 1.5; }
.lg-code {
    font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; color: var(--a); background: var(--code-bg);
    border: 1px solid var(--line-soft); border-radius: 8px; padding: 0.5rem 0.65rem; margin-top: 0.4rem; white-space: pre-wrap; word-break: break-word;
}
.lg-evidence { font-size: 0.82rem; color: var(--soft); line-height: 1.55; margin: 0.3rem 0 0 0; padding-left: 1rem; }
.lg-evidence li { margin-bottom: 0.25rem; }
.lg-evidence a { color: var(--a); }

/* ---------- Footer ---------- */
.lg-footer { text-align: center; color: var(--muted); font-size: 0.76rem; margin-top: 3rem; }

@media (max-width: 760px) {
    .lg-hero-grid, .lg-steps, .lg-tiles { grid-template-columns: 1fr; }
    .lg-hero-copy h1 { font-size: 2.1rem; }
    .lg-live { display: none; }
    .lg-question { font-size: 1.2rem; }
}
"""

# Streamlit ends an HTML block at the first blank line and shows the rest as text,
# so every blank line is stripped before the CSS goes inside one <style> tag.
_css_clean = "\n".join(line for line in (ROOT_CSS + "\n" + BASE_CSS).splitlines() if line.strip())
st.markdown(f"<style>\n{_css_clean}\n</style>", unsafe_allow_html=True)


def render_html(fragment: str) -> None:
    """Collapse to single-line HTML before rendering — avoids Streamlit's
    markdown parser treating a blank-line + indent as a code block."""
    collapsed = " ".join(line.strip() for line in textwrap.dedent(fragment).splitlines())
    st.markdown(collapsed, unsafe_allow_html=True)


MARK_SVG = (
    '<svg class="lg-mark" width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<rect class="m1" x="5" y="16" width="5" height="11" rx="1"/>'
    '<rect class="m1" x="13.5" y="10" width="5" height="17" rx="1"/>'
    '<rect class="m2" x="22" y="5" width="5" height="22" rx="1"/>'
    "</svg>"
)

# Decorative hero illustration: bars rise, the line draws, then dips; Ledger "investigates" the dip.
HERO_ART = """
<svg class="lg-art" viewBox="0 0 420 320" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Revenue chart with a dip being investigated">
<defs>
<linearGradient id="gT" x1="0" y1="0" x2="0" y2="1"><stop class="s-a1" offset="0"/><stop class="s-a1" offset="1" stop-opacity="0.15"/></linearGradient>
<linearGradient id="gC" x1="0" y1="0" x2="0" y2="1"><stop class="s-a2" offset="0"/><stop class="s-a2" offset="1" stop-opacity="0.15"/></linearGradient>
</defs>
<rect class="panel" x="1" y="1" width="418" height="318" rx="22" fill-opacity="0.85"/>
<line class="axis" x1="30" y1="250" x2="390" y2="250"/>
<line class="gridline" x1="30" y1="190" x2="390" y2="190" stroke-dasharray="3 5"/>
<line class="gridline" x1="30" y1="130" x2="390" y2="130" stroke-dasharray="3 5"/>
<rect class="bar b1" x="50" y="160" width="34" height="90" rx="5" fill="url(#gT)"/>
<rect class="bar b2" x="102" y="135" width="34" height="115" rx="5" fill="url(#gT)"/>
<rect class="bar b3" x="154" y="120" width="34" height="130" rx="5" fill="url(#gT)"/>
<rect class="bar b4" x="206" y="90" width="34" height="160" rx="5" fill="url(#gT)"/>
<rect class="bar b5" x="258" y="75" width="34" height="175" rx="5" fill="url(#gT)"/>
<rect class="bar b6" x="310" y="110" width="34" height="140" rx="5" fill="url(#gC)"/>
<rect class="bar b7" x="362" y="155" width="34" height="95" rx="5" fill="url(#gC)"/>
<path class="lg-line trend" pathLength="100" d="M67 160 L119 135 L171 120 L223 90 L275 75 L327 110 L379 155" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle class="lg-pulse dot-a2" cx="379" cy="155" r="6"/>
<circle class="dot-a2 dot-ring" cx="379" cy="155" r="5" stroke-width="2"/>
<rect class="pill" x="30" y="28" width="196" height="32" rx="16"/>
<circle class="dot-a" cx="48" cy="44" r="4"/>
<text class="pill-text" x="62" y="48.5" font-family="Inter, sans-serif" font-size="12.5">Revenue dipped. Investigating</text>
</svg>
"""

CATEGORY_LABELS = {
    "sales": "Sales", "marketing": "Marketing", "customers": "Customers",
    "operations": "Operations", "finance": "Finance", "inventory": "Inventory", "general": "General",
}
CATEGORY_COLORS = {
    "sales": "#0FB5A3", "marketing": "#8B5CF6", "customers": "#3B82F6", "operations": "#D99A06",
    "finance": "#10B981", "inventory": "#EF6B4A", "general": "#64748B",
}

EXAMPLES = [
    "📉  Why did our revenue drop this month?",
    "🏆  What were the top products in June?",
    "🌍  Which region is declining?",
    "💎  Which customer segment is most valuable?",
]

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "db_ready" not in st.session_state:
    with st.spinner("Preparing business database…"):
        build_database()
    st.session_state.db_ready = True

if "agent" not in st.session_state:
    st.session_state.agent = BusinessAgent()
    st.session_state.history = []  # list of {"trace": ..., "time": "HH:MM"}

if "question" not in st.session_state:
    st.session_state.question = ""


def use_example(text: str) -> None:
    # strip the emoji prefix so only the question is placed in the input
    st.session_state.question = text.split("  ", 1)[-1].strip()


def reset_history() -> None:
    st.session_state.history = []


# ---------------------------------------------------------------------------
# Top bar (brand · status · theme switcher)
# ---------------------------------------------------------------------------
with st.container(key="topbar"):
    c_brand, c_status, c_theme = st.columns([1.6, 1.8, 3.2], vertical_alignment="center")
    with c_brand:
        render_html(f'<div class="lg-brand">{MARK_SVG}<div class="lg-wordmark">Ledger</div></div>')
    with c_status:
        render_html(
            f"""
            <div class="lg-status">
                <span class="lg-live"><span class="lg-dot"></span>Agent ready</span>
                <span class="lg-pill">{len(st.session_state.history)} investigated</span>
            </div>
            """
        )
    with c_theme:
        with st.container(key="themebox"):
            if hasattr(st, "segmented_control"):
                st.segmented_control(
                    "Theme",
                    THEME_NAMES,
                    default=THEME_NAMES[0],
                    key="theme",
                    on_change=_on_theme_change,
                    label_visibility="collapsed",
                )
            else:  # older Streamlit versions
                st.radio(
                    "Theme",
                    THEME_NAMES,
                    key="theme",
                    horizontal=True,
                    on_change=_on_theme_change,
                    label_visibility="collapsed",
                )

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
render_html(
    f"""
    <div class="lg-hero-grid">
        <div class="lg-hero-copy">
            <h1>Business questions, answered with evidence.</h1>
            <p>Ask in plain English. Ledger plans the analysis, runs real queries on your data, and writes a report that shows its work.</p>
        </div>
        <div>{HERO_ART}</div>
    </div>
    """
)

# ---------------------------------------------------------------------------
# Command bar
# ---------------------------------------------------------------------------
with st.container(key="cmd"):
    question = st.text_area(
        "Business question",
        key="question",
        placeholder="Ask anything about sales, customers, regions or products…",
        label_visibility="collapsed",
        height=95,
    )
    hint_col, btn_col = st.columns([4, 1.2])
    with hint_col:
        st.markdown(
            '<div class="lg-hint">Tip: mention a period, region or product for a sharper answer.</div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        submitted = st.button("Investigate", type="primary", use_container_width=True)

st.markdown('<div class="lg-label">Try one of these</div>', unsafe_allow_html=True)
with st.container(key="examples"):
    ex_cols = st.columns(2)
    for i, example in enumerate(EXAMPLES):
        with ex_cols[i % 2]:
            st.button(example, key=f"ex_{i}", on_click=use_example, args=(example,), use_container_width=True)

if submitted and question.strip():
    try:
        with st.spinner("Planning, querying business data, and writing the report…"):
            trace = st.session_state.agent.investigate(question.strip())
        st.session_state.history.insert(0, {"trace": trace, "time": datetime.now().strftime("%H:%M")})
    except Exception as exc:  # keep the UI alive if the agent or API fails
        st.error(f"Ledger couldn't finish this investigation: {exc}. Check your API key and connection, then try again.")
elif submitted:
    st.warning("Type a question first, or pick one of the examples.")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if st.session_state.history:
    head_l, head_r = st.columns([6, 1])
    with head_l:
        st.markdown('<div class="lg-results-head">Investigations</div>', unsafe_allow_html=True)
    with head_r:
        st.markdown('<div style="height:2.9rem"></div>', unsafe_allow_html=True)
        st.button("Clear all", key="reset_btn", on_click=reset_history)

    for idx, item in enumerate(st.session_state.history):
        trace = item["trace"]
        cat_key = trace.classification.get("category", "general")
        if cat_key not in CATEGORY_LABELS:
            cat_key = "general"
        category = CATEGORY_LABELS[cat_key]
        c_color = CATEGORY_COLORS[cat_key]
        safe_question = escape(trace.question)
        n_calls = len(trace.tool_calls)
        n_findings = len(trace.findings) if trace.findings else 0
        n_sources = len(trace.research) if trace.research else 0

        with st.container(key=f"card_{idx}"):
            render_html(
                f"""
                <div class="lg-card-top">
                    <span class="lg-category" style="color:{c_color};background:color-mix(in srgb, {c_color} 14%, transparent);">{category}</span>
                    <span class="lg-meta">{item['time']}</span>
                </div>
                <div class="lg-question">{safe_question}</div>
                <div class="lg-tiles">
                    <div class="lg-tile"><b>{n_calls}</b><span>queries run</span></div>
                    <div class="lg-tile"><b>{n_findings}</b><span>findings used as evidence</span></div>
                    <div class="lg-tile"><b>{n_sources}</b><span>external sources</span></div>
                </div>
                """
            )
            st.markdown(trace.report, unsafe_allow_html=True)

            with st.expander("See how Ledger got this answer"):
                steps = [
                    '<div class="lg-step"><div class="lg-step-title">Planned the analysis</div>'
                    f'<div class="lg-step-sub">{escape(str(trace.classification.get("task", "n/a")))}</div></div>'
                ]
                for call in trace.tool_calls:
                    steps.append(
                        '<div class="lg-step"><div class="lg-step-title">'
                        f'{escape(str(call["label"]))}</div>'
                        f'<div class="lg-code">{escape(str(call["tool"]))}({escape(str(call["kwargs"]))})</div></div>'
                    )
                if trace.findings:
                    items_html = "".join(f"<li>{escape(str(f))}</li>" for f in trace.findings)
                    steps.append(
                        '<div class="lg-step alt"><div class="lg-step-title">Computed findings</div>'
                        '<div class="lg-step-sub">Fed to the language model as evidence.</div>'
                        f'<ul class="lg-evidence">{items_html}</ul></div>'
                    )
                if trace.research:
                    links = "".join(
                        f'<li><a href="{escape(str(r["url"]), quote=True)}" target="_blank">{escape(str(r["title"]))}</a></li>'
                        for r in trace.research
                    )
                    steps.append(
                        '<div class="lg-step alt"><div class="lg-step-title">External research</div>'
                        f'<ul class="lg-evidence">{links}</ul></div>'
                    )
                elif trace.research_note:
                    steps.append(
                        '<div class="lg-step alt"><div class="lg-step-title">External research</div>'
                        f'<div class="lg-step-sub">{escape(str(trace.research_note))}</div></div>'
                    )
                render_html(f'<div class="lg-tl">{"".join(steps)}</div>')

            st.download_button(
                "Download report",
                data=f"# {trace.question}\n\n{trace.report}\n",
                file_name=f"ledger-report-{item['time'].replace(':', '')}.md",
                mime="text/markdown",
                key=f"dl_{idx}",
            )
else:
    render_html(
        """
        <div class="lg-steps">
            <div class="lg-stepcard">
                <div class="lg-stepnum">01</div>
                <div class="lg-stepicon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01"/></svg></div>
                <div class="lg-steptitle">Plan</div>
                <div class="lg-stepbody">Ledger reads your question and decides which analysis to run.</div>
            </div>
            <div class="lg-stepcard">
                <div class="lg-stepnum">02</div>
                <div class="lg-stepicon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg></div>
                <div class="lg-steptitle">Query</div>
                <div class="lg-stepbody">It runs real queries against your business database and computes the findings.</div>
            </div>
            <div class="lg-stepcard">
                <div class="lg-stepnum">03</div>
                <div class="lg-stepicon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M8 13h8M8 17h6"/></svg></div>
                <div class="lg-steptitle">Report</div>
                <div class="lg-stepbody">You get a written answer with the queries and evidence attached.</div>
            </div>
        </div>
        """
    )

st.markdown('<div class="lg-footer">Built by Hamna Munir</div>', unsafe_allow_html=True)