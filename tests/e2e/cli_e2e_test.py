from strands_solver.cli import main


def test_main(monkeypatch, caplog):
    """Solve a real puzzle through the CLI and assert that a solution is logged."""
    date = "2025-09-23"
    monkeypatch.setattr("sys.argv", ["strands-solver", date])

    with caplog.at_level("INFO"):
        main()

    assert any(record.message.startswith("Solution:") for record in caplog.records)
