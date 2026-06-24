# benchmarks/accuracy.py
import difflib
import re


def matches_ground_truth(answer: str, ground_truth: str) -> bool:
    if not answer or not ground_truth:
        return False
    answer_lower = answer.lower().strip()
    truth_lower = ground_truth.lower().strip()
    # Bug 3: whitespace-only ground_truth must not match anything
    if not truth_lower:
        return False
    if len(truth_lower) <= 3 or truth_lower.isdigit():
        # Short or numeric: word-boundary only, no difflib fallback
        return bool(re.search(r'\b' + re.escape(truth_lower) + r'\b', answer_lower))

    # Longer non-numeric: substring check first, then difflib
    if truth_lower in answer_lower:
        return True
    ratio = difflib.SequenceMatcher(None, answer_lower, truth_lower).ratio()
    return ratio >= 0.6
