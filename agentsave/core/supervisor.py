from contextlib import contextmanager
from .models import RunState
from .context_filter import ContextFilter
from .early_exit import EarlyExitDetector
from .budget import BudgetGate
from .token_counter import count_tokens


class RunLoop:
    def __init__(
        self,
        budget: int,
        model_name: str = "unknown",
        framework: str = "raw",
        goal: str = "",
        relevance_threshold: float = 0.3,
        early_exit_window: int = 3,
        early_exit_threshold: float = 0.05,
    ):
        self.state = RunState.new(
            framework=framework,
            model_name=model_name,
            budget_tokens=budget,
        )
        self._budget = BudgetGate(budget=budget)
        self._context_filter = ContextFilter(threshold=relevance_threshold)
        self._early_exit = EarlyExitDetector(
            window=early_exit_window, threshold=early_exit_threshold
        )
        self._stopped = False
        if goal:
            self._context_filter.set_goal(goal)

    def observe(self, text: str) -> str:
        tokens = count_tokens(text)
        self._budget.consume(tokens)
        self.state.tokens_consumed += tokens
        gain = self._context_filter.score(text)
        self._early_exit.record(gain)
        if not self._context_filter.is_relevant(text):
            return "[filtered: low relevance]"
        return text

    def should_continue(self) -> bool:
        if self._stopped:
            return False
        if self._budget.is_exhausted():
            self.state.should_exit_early = True
            return False
        if self._early_exit.should_exit():
            self.state.should_exit_early = True
            return False
        return True

    def stop(self) -> None:
        self._stopped = True


@contextmanager
def loop(
    budget: int = 100_000,
    model_name: str = "unknown",
    framework: str = "raw",
    goal: str = "",
    relevance_threshold: float = 0.3,
    early_exit_window: int = 3,
    early_exit_threshold: float = 0.05,
):
    run = RunLoop(
        budget=budget,
        model_name=model_name,
        framework=framework,
        goal=goal,
        relevance_threshold=relevance_threshold,
        early_exit_window=early_exit_window,
        early_exit_threshold=early_exit_threshold,
    )
    try:
        yield run
    finally:
        run.state.task_success = not run.state.should_exit_early
        from agentsave.telemetry.client import get_client
        _client = get_client()
        if _client.enabled:
            _client.send(run.state, tokens_baseline=run.state.budget_tokens)
