# benchmarks/runner.py
from dataclasses import dataclass, field
from agentsave.core.context_filter import ContextFilter
from agentsave.core.early_exit import EarlyExitDetector
from agentsave.core.token_counter import count_tokens
from benchmarks.tasks import TASKS
from benchmarks.accuracy import matches_ground_truth


@dataclass
class BenchmarkResult:
    per_task: list = field(default_factory=list)

    @property
    def reduction_pct(self) -> float:
        total_before = sum(t["tokens_before"] for t in self.per_task)
        total_after = sum(t["tokens_after"] for t in self.per_task)
        if total_before == 0:
            return 0.0
        return (total_before - total_after) / total_before * 100

    @property
    def accuracy_without(self) -> float:
        correct = sum(1 for t in self.per_task if t["correct_without"])
        return correct / len(self.per_task) if self.per_task else 0.0

    @property
    def accuracy_with(self) -> float:
        correct = sum(1 for t in self.per_task if t["correct_with"])
        return correct / len(self.per_task) if self.per_task else 0.0


def _simulate_agent_answer(tool_outputs: list[str]) -> str:
    """Naive answer: concatenate all relevant outputs — simulates agent with full context."""
    return " ".join(tool_outputs)


def _simulate_agent_answer_filtered(
    goal: str,
    tool_outputs: list[str],
    relevance_threshold: float = 0.08,
    early_exit_window: int = 2,
    early_exit_threshold: float = 0.05,
) -> tuple[str, int]:
    """Answer with AgentSave supervision — returns (answer, tokens_consumed)."""
    cf = ContextFilter(threshold=relevance_threshold)
    cf.set_goal(goal)
    eed = EarlyExitDetector(window=early_exit_window, threshold=early_exit_threshold)

    kept = []
    tokens_consumed = 0
    for output in tool_outputs:
        gain = cf.score(output)
        eed.record(gain)
        if eed.should_exit():
            break
        if gain >= relevance_threshold:
            kept.append(output)
            tokens_consumed += count_tokens(output)

    return " ".join(kept), tokens_consumed


def run_benchmark() -> BenchmarkResult:
    result = BenchmarkResult()
    for task in TASKS:
        goal = task["goal"]
        outputs = task["tool_outputs"]
        truth = task["ground_truth"]

        tokens_before = sum(count_tokens(o) for o in outputs)
        answer_without = _simulate_agent_answer(outputs)
        correct_without = matches_ground_truth(answer_without, truth)

        answer_with, tokens_after = _simulate_agent_answer_filtered(goal, outputs)
        correct_with = matches_ground_truth(answer_with, truth)

        result.per_task.append({
            "id": task["id"],
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "answer_without": answer_without,
            "answer_with": answer_with,
            "correct_without": correct_without,
            "correct_with": correct_with,
        })
    return result
