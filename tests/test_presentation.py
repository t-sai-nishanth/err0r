"""Unit tests for BookError presentation layer (Layer 3)."""

from __future__ import annotations

from bookerrror.presentation.banner import render_banner, render_no_chain_banner
from bookerrror.presentation.graph_widget import render_graph
from bookerrror.presentation.path_display import render_path, render_path_text
from tests.fixtures.sample_data import MOCK_CAUSAL_PATH


def test_render_banner_mock_path():
    html_output = render_banner(MOCK_CAUSAL_PATH)
    assert "BookError Causal Trace" in html_output
    assert "KeyError" in html_output
    assert "cell-2" in html_output
    assert "cell-5" in html_output
    assert "cell-9" in html_output
    assert "dropped column 'age' from df" in html_output
    assert "bookerror-pipeline" in html_output


def test_render_no_chain_banner():
    html_output = render_no_chain_banner("ValueError", "invalid literal")
    assert "BookError" in html_output
    assert "ValueError" in html_output
    assert "No earlier notebook cell dependencies" in html_output


def test_render_path_html():
    html_path = render_path(MOCK_CAUSAL_PATH)
    assert "bookerror-path-list" in html_path
    assert "cell-2" in html_path
    assert "cell-5" in html_path


def test_render_path_text():
    text = render_path_text(MOCK_CAUSAL_PATH)
    assert "KeyError: 'age'" in text
    assert "1. [cell-2 | exec_id=1]" in text
    assert "2. [cell-5 | exec_id=2]" in text


def test_render_graph_svg():
    svg_output = render_graph(causal_path=MOCK_CAUSAL_PATH)
    assert "<svg" in svg_output
    assert "</svg>" in svg_output
    assert "cell-2" in svg_output
    assert "cell-5" in svg_output
    assert "cell-9" in svg_output
    assert "line" in svg_output
