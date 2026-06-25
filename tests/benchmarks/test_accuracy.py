# tests/benchmarks/test_accuracy.py
from benchmarks.accuracy import matches_ground_truth


def test_exact_match():
    assert matches_ground_truth("Paris", "Paris") is True


def test_case_insensitive():
    assert matches_ground_truth("paris", "Paris") is True


def test_partial_match():
    assert matches_ground_truth("Paris is the capital of France.", "Paris") is True


def test_no_match():
    assert matches_ground_truth("London", "Paris") is False


def test_numeric_match():
    assert matches_ground_truth("37.4 million people", "37.4 million") is True


def test_empty_answer_fails():
    assert matches_ground_truth("", "Paris") is False


def test_tasks_schema():
    from benchmarks.tasks import TASKS
    assert len(TASKS) == 20
    for t in TASKS:
        assert "id" in t and isinstance(t["id"], str)
        assert "goal" in t and isinstance(t["goal"], str)
        assert "tool_outputs" in t and isinstance(t["tool_outputs"], list)
        assert "ground_truth" in t and isinstance(t["ground_truth"], str)
        assert 3 <= len(t["tool_outputs"]) <= 6
