# benchmarks/report.py
from benchmarks.runner import BenchmarkResult


def write_report(result: BenchmarkResult, path: str = "BENCHMARKS.md") -> None:
    lines = [
        "# AgentSave Benchmarks\n",
        "## Current results — 20-task benchmark set\n",
        "| Metric | Value | Notes |",
        "|---|---|---|",
        f"| Token reduction | {result.reduction_pct:.1f}% | {len(result.per_task)}-task set |",
        f"| Accuracy without AgentSave | {result.accuracy_without:.1%} | Baseline |",
        f"| Accuracy with AgentSave | {result.accuracy_with:.1%} | Supervised |",
        f"| Accuracy delta | {(result.accuracy_with - result.accuracy_without):+.1%} | 0% = no loss |",
        "",
        "## Target",
        "",
        "| Metric | Target | Status |",
        "|---|---|---|",
        f"| Token reduction | ~30% | {'✓ Met' if result.reduction_pct >= 30.0 else f'In progress ({result.reduction_pct:.1f}%)'} |",
        f"| Accuracy loss | 0% | {'✓ Met' if result.accuracy_with >= result.accuracy_without else '✗ Regression'} |",
        "",
        "## Per-task results",
        "",
        "| Task | Tokens before | Tokens after | Reduction | Answer correct (w/o) | Answer correct (with) |",
        "|---|---|---|---|---|---|",
    ]
    for t in result.per_task:
        reduction = (t["tokens_before"] - t["tokens_after"]) / t["tokens_before"] * 100
        lines.append(
            f"| {t['id']} | {t['tokens_before']} | {t['tokens_after']} "
            f"| {reduction:.1f}% | {'✓' if t['correct_without'] else '✗'} "
            f"| {'✓' if t['correct_with'] else '✗'} |"
        )
    lines += [
        "",
        "## Methodology",
        "",
        "Each task has a goal, 3–5 tool outputs (mix of relevant and noise), and a ground-truth answer.",
        "The runner simulates two agents: one receiving all outputs, one supervised by AgentSave.",
        "Accuracy is fuzzy-matched (substring or ≥0.6 sequence similarity).",
        "_Run `python -m benchmarks.runner` to regenerate this file._",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
