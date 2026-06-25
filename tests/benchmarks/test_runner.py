# tests/benchmarks/test_runner.py
from benchmarks.runner import run_benchmark, BenchmarkResult


def test_run_benchmark_returns_result():
    result = run_benchmark()
    assert isinstance(result, BenchmarkResult)


def test_reduction_pct_above_floor():
    result = run_benchmark()
    assert result.reduction_pct >= 20.0, (
        f"Token reduction {result.reduction_pct:.1f}% below 20% floor"
    )


def test_accuracy_not_degraded():
    result = run_benchmark()
    assert result.accuracy_with >= result.accuracy_without, (
        f"Accuracy degraded: {result.accuracy_without:.1%} → {result.accuracy_with:.1%}"
    )


def test_per_task_list_complete():
    result = run_benchmark()
    from benchmarks.tasks import TASKS
    assert len(result.per_task) == len(TASKS)


def test_per_task_has_required_fields():
    result = run_benchmark()
    for entry in result.per_task:
        assert "id" in entry
        assert "tokens_before" in entry
        assert "tokens_after" in entry
        assert "answer_without" in entry
        assert "answer_with" in entry
        assert "correct_without" in entry
        assert "correct_with" in entry
