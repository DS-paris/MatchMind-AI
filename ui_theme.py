"""Presentation helpers derived from the supplied Stitch HTML design tokens."""
from html import escape
from pathlib import Path
import streamlit as st


def apply_theme(dark=False):
    css = (Path(__file__).parent / "static" / "stitch.css").read_text(encoding="utf-8")
    css = (Path(__file__).parent / "static" / "fonts" / "fonts.css").read_text(encoding="utf-8") + css
    if dark:
        css += """:root {--bg:#06151D;--sidebar:#0F1D26;--panel:#13212A;--low:#1E2C35;
        --ink:#D5E4F1;--muted:#BEC8CB;--line:#3E484B;--primary:#80D3E2;
        --primary-fill:#1B7C8A;--primary-ink:#E5FBFF;--accent:#FFB695;}
        [data-testid="stAlertContainer"] {background:var(--low);border:1px solid var(--line);color:var(--ink);}
        input,textarea {background:var(--panel)!important;}
        a {color:var(--primary);}"""
    with st.container(key="theme_injection"):
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def label(text):
    return escape(str(text))


def section_title(title, description=""):
    st.markdown(f'<div class="section-heading"><h2>{label(title)}</h2><p>{label(description)}</p></div>', unsafe_allow_html=True)


def stat(title, value, detail, icon="description"):
    value_class = "stat-value is-text" if len(str(value)) > 8 else "stat-value"
    st.markdown(f'<article class="stat-card"><div class="stat-label">{label(title)}'
        f'<span class="material-symbols-outlined">{label(icon)}</span></div>'
        f'<div class="{value_class}">{label(value)}</div><div class="stat-detail">{label(detail)}</div></article>', unsafe_allow_html=True)


def empty_state(title, description, icon="manage_search"):
    st.markdown(f'<div class="empty-state"><span class="material-symbols-outlined">{label(icon)}</span>'
        f'<h3>{label(title)}</h3><p>{label(description)}</p></div>', unsafe_allow_html=True)


def badge(text):
    st.markdown(f'<span class="mm-badge">{label(text)}</span>', unsafe_allow_html=True)
