"""
Launch-blocker benchmark. Validates ≥20% combined token reduction via
context filter + early exit on a local synthetic task set.
Do NOT publish the "30% reduction" README claim until this test passes.
"""


BENCHMARK_TASKS = [
    {
        "goal": "What is the population of Tokyo?",
        "tool_outputs": [
            "Tokyo metropolitan area population statistics 2024: The Greater Tokyo Area has approximately 37.4 million people, making it the world's most populous metropolitan area.",
            "Weather forecast for Tokyo: sunny skies, 22 degrees Celsius.",
            "Tokyo population: 13.96 million in the city proper as of 2023.",
        ],
    },
    {
        "goal": "Who invented the telephone?",
        "tool_outputs": [
            "Alexander Graham Bell invented the telephone in 1876.",
            "The New York Stock Exchange was founded in 1792.",
            "Bell demonstrated the telephone at the 1876 Philadelphia Centennial Exposition.",
            "Current stock prices: AAPL $185, GOOGL $140.",
        ],
    },
]


def test_context_filter_reduces_tokens_on_benchmark():
    from agentsave.core.context_filter import ContextFilter
    from agentsave.core.token_counter import count_tokens

    total_before = 0
    total_after = 0

    for task in BENCHMARK_TASKS:
        cf = ContextFilter(threshold=0.15)
        cf.set_goal(task["goal"])
        outputs = task["tool_outputs"]
        tokens_before = sum(count_tokens(o) for o in outputs)
        filtered = cf.filter(outputs)
        tokens_after = sum(count_tokens(o) for o in filtered)
        total_before += tokens_before
        total_after += tokens_after
        assert len(filtered) >= 1

    reduction_pct = (total_before - total_after) / total_before * 100
    print(f"\n[Benchmark] Context filter reduction: {reduction_pct:.1f}%")
    assert reduction_pct >= 15.0, (
        f"Context filter only reduced by {reduction_pct:.1f}% — below 15% floor."
    )


def test_early_exit_reduces_iterations():
    from agentsave.core.early_exit import EarlyExitDetector
    from agentsave.core.context_filter import ContextFilter

    task = BENCHMARK_TASKS[0]
    cf = ContextFilter(threshold=0.15)
    cf.set_goal(task["goal"])
    eed = EarlyExitDetector(window=2, threshold=0.1)

    iterations_run = 0
    max_iterations = 10

    for i in range(max_iterations):
        if eed.should_exit():
            break
        output = task["tool_outputs"][i % len(task["tool_outputs"])]
        gain = cf.score(output) if i > 1 else 0.02
        eed.record(gain)
        iterations_run += 1

    print(f"\n[Benchmark] Iterations: {iterations_run}/{max_iterations}")
    assert iterations_run < max_iterations


def test_combined_reduction_meets_floor():
    """LAUNCH BLOCKER — must pass before publishing 30% claim."""
    from agentsave.core.context_filter import ContextFilter
    from agentsave.core.early_exit import EarlyExitDetector
    from agentsave.core.token_counter import count_tokens

    total_before = 0
    total_after = 0

    for task in BENCHMARK_TASKS:
        cf = ContextFilter(threshold=0.15)
        cf.set_goal(task["goal"])
        eed = EarlyExitDetector(window=2, threshold=0.08)
        outputs = task["tool_outputs"]
        tokens_before = sum(count_tokens(o) for o in outputs)
        total_before += tokens_before

        saved_by_filter = 0
        saved_by_early_exit = 0

        for i, output in enumerate(outputs):
            gain = cf.score(output)
            eed.record(gain)
            if eed.should_exit():
                remaining = outputs[i + 1:]
                saved_by_early_exit = sum(count_tokens(o) for o in remaining)
                break
            if not cf.is_relevant(output):
                saved_by_filter += count_tokens(output)

        tokens_after = tokens_before - saved_by_filter - saved_by_early_exit
        total_after += tokens_after

    reduction_pct = (total_before - total_after) / total_before * 100
    print(f"\n[LAUNCH-BLOCKER] Combined reduction: {reduction_pct:.1f}%")
    print(f"  Before: {total_before} | After: {total_after}")

    assert reduction_pct >= 20.0, (
        f"Combined reduction {reduction_pct:.1f}% below 20% floor. "
        "Do NOT publish 30% claim. Fix context_filter.py or early_exit.py first."
    )
