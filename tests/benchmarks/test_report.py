# tests/benchmarks/test_report.py
import os, tempfile
from benchmarks.report import write_report
from benchmarks.runner import run_benchmark


def test_write_report_creates_file():
    result = run_benchmark()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name
    try:
        write_report(result, path)
        assert os.path.exists(path)
        content = open(path, encoding="utf-8").read()
        assert "Token reduction" in content
        assert "Accuracy" in content
        assert str(round(result.reduction_pct, 1)) in content
    finally:
        os.unlink(path)
