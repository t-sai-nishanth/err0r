"""Unit tests for BookError LLM layer (Layer 4)."""

from __future__ import annotations

from bookerrror.llm.client import explain
from bookerrror.llm.prompt_builder import build_prompt
from tests.fixtures.sample_data import MOCK_CAUSAL_PATH


def test_build_prompt():
    prompt = build_prompt(MOCK_CAUSAL_PATH)
    assert "A Jupyter notebook raised an error" in prompt
    assert "cell-2" in prompt
    assert "cell-5" in prompt
    assert "KeyError: 'age'" in prompt
    # Verify token footprint is small (< 150 words)
    assert len(prompt.split()) < 150


def test_explain_mock_fallback():
    explanation = explain(MOCK_CAUSAL_PATH)
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    assert "cell-9" in explanation or "cell-2" in explanation or "Causal sequence" in explanation
