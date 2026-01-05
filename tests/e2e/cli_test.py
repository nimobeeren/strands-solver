import subprocess
import sys

import pytest


def run_cli(args: str) -> subprocess.CompletedProcess[str]:
    """Run the strands-solver CLI with the given arguments."""
    return subprocess.run(
        [sys.executable, "-m", "strands_solver.cli.main", *args.split()],
        capture_output=True,
        text=True,
    )


@pytest.mark.e2e
def test_solve():
    """Solve a real puzzle through the CLI and assert that a solution is output."""
    result = run_cli("solve 2025-09-23")
    assert result.returncode == 0
    assert "COLLEGE" in result.stdout


@pytest.mark.e2e
def test_show():
    """Display the official solution for a puzzle."""
    result = run_cli("show 2025-10-03")
    assert result.returncode == 0
    assert "LEADERSHIP" in result.stdout


@pytest.mark.e2e
def test_benchmark(tmp_path):
    """Run benchmark on a single puzzle and verify results are written."""
    report_dir = tmp_path / "report"
    result = run_cli(
        f"benchmark --start-date 2025-09-23 --end-date 2025-09-23 --timeout 90 --report-dir {report_dir}"
    )
    assert result.returncode == 0
    assert (report_dir / "summary.md").exists()
    assert (report_dir / "results.md").exists()
    results_content = (report_dir / "results.md").read_text()
    assert "2025-09-23" in results_content
