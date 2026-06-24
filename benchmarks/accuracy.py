# benchmarks/accuracy.py
import difflib


def matches_ground_truth(answer: str, ground_truth: str) -> bool:
    if not answer or not ground_truth:
        return False
    answer_lower = answer.lower().strip()
    truth_lower = ground_truth.lower().strip()
    if truth_lower in answer_lower:
        return True
    ratio = difflib.SequenceMatcher(None, answer_lower, truth_lower).ratio()
    return ratio >= 0.6
