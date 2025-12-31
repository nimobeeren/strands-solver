import pytest

from strands_solver.cli import main

pytestmark = pytest.mark.e2e


def test_main(monkeypatch, caplog):
    """End-to-end test solving a real puzzle using the CLI."""
    date = "2025-09-23"
    monkeypatch.setattr("sys.argv", ["strands-solver", date])

    with caplog.at_level("INFO"):
        main()

    assert any(record.message.startswith("Solution:") for record in caplog.records)
