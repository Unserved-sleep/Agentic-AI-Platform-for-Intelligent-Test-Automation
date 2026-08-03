"""
dashboard/components/status_badge.py
======================================
Shared UI component: status badge and colour helpers.

Renders a coloured inline HTML badge for an execution status string.
"""

from __future__ import annotations

# Colour mapping: status → (background_hex, text_hex)
_STATUS_COLOURS: dict[str, tuple[str, str]] = {
    "PASSED": ("#22c55e", "#ffffff"),
    "FAILED": ("#ef4444", "#ffffff"),
    "ERROR": ("#f97316", "#ffffff"),
    "RUNNING": ("#3b82f6", "#ffffff"),
    "PENDING": ("#a3a3a3", "#ffffff"),
    "SKIPPED": ("#8b5cf6", "#ffffff"),
}

_DEFAULT_COLOUR: tuple[str, str] = ("#6b7280", "#ffffff")


def status_colour(status: str) -> tuple[str, str]:
    """
    Return (background, text) hex colours for *status*.

    Parameters
    ----------
    status:
        Status string, e.g. ``"PASSED"``.

    Returns
    -------
    tuple[str, str]
        (background_hex, text_hex)
    """
    return _STATUS_COLOURS.get(status.upper(), _DEFAULT_COLOUR)


def status_badge_html(status: str) -> str:
    """
    Return an inline HTML string for a status badge.

    Parameters
    ----------
    status:
        Status string.

    Returns
    -------
    str
        HTML ``<span>`` element.
    """
    bg, fg = status_colour(status)
    return (
        f'<span style="'
        f"background-color:{bg};"
        f"color:{fg};"
        f"padding:2px 10px;"
        f"border-radius:12px;"
        f"font-size:0.82em;"
        f"font-weight:600;"
        f"letter-spacing:0.04em;"
        f'">{status.upper()}</span>'
    )


def render_status_badge(status: str) -> None:
    """
    Render a status badge using ``st.markdown``.

    Parameters
    ----------
    status:
        Status string.
    """
    import streamlit as st  # noqa: PLC0415 — lazy import keeps tests streamlit-free
    st.markdown(status_badge_html(status), unsafe_allow_html=True)
