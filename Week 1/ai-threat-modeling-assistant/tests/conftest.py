"""Shared pytest fixtures and configuration for the test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the project package importable no matter where pytest is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    """Force the offline mock LLM so tests never need an API key or network.

    ``USE_MOCK_LLM=true`` takes priority in the client even if a real ``.env``
    provides an ``OPENAI_API_KEY``, so the flow is fully deterministic.
    """
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    yield
