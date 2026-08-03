"""
tests/dashboard/test_status_badge.py
======================================
Unit tests for dashboard.components.status_badge.

Tests the pure-Python helpers (status_colour, status_badge_html).
Does NOT call any Streamlit rendering functions.
"""

from __future__ import annotations

import pytest

from dashboard.components.status_badge import status_badge_html, status_colour


class TestStatusColour:
    def test_passed_is_green(self) -> None:
        bg, fg = status_colour("PASSED")
        assert bg == "#22c55e"
        assert fg == "#ffffff"

    def test_failed_is_red(self) -> None:
        bg, _ = status_colour("FAILED")
        assert bg == "#ef4444"

    def test_error_is_orange(self) -> None:
        bg, _ = status_colour("ERROR")
        assert bg == "#f97316"

    def test_case_insensitive(self) -> None:
        assert status_colour("passed") == status_colour("PASSED")

    def test_unknown_status_returns_default(self) -> None:
        bg, fg = status_colour("FOOBAR")
        assert isinstance(bg, str)
        assert bg.startswith("#")


class TestStatusBadgeHtml:
    def test_returns_string(self) -> None:
        html = status_badge_html("PASSED")
        assert isinstance(html, str)

    def test_contains_status_text(self) -> None:
        html = status_badge_html("FAILED")
        assert "FAILED" in html

    def test_contains_span_tag(self) -> None:
        html = status_badge_html("PASSED")
        assert "<span" in html
        assert "</span>" in html

    def test_contains_background_colour(self) -> None:
        html = status_badge_html("PASSED")
        assert "#22c55e" in html

    @pytest.mark.parametrize("status", ["PASSED", "FAILED", "ERROR", "RUNNING", "SKIPPED"])
    def test_all_known_statuses_produce_html(self, status: str) -> None:
        html = status_badge_html(status)
        assert status in html
