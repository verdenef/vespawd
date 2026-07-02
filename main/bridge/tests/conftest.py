"""Pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def workspace_root() -> Path:
    return WORKSPACE_ROOT
