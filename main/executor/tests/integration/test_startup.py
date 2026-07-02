"""Integration tests — live Bridge startup."""

from __future__ import annotations

from vespawd_executor.startup.sequence import run_startup

from tests.conftest import requires_vedaws


@requires_vedaws
def test_live_startup_fixture(fixture_workspace) -> None:
    result = run_startup(fixture_workspace)
    assert result.sync_invoked
    assert result.ok, result.blockers
