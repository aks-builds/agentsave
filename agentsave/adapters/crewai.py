from typing import Any
from .base import BaseAdapter
from ..core.budget import BudgetGate
from ..core.early_exit import EarlyExitDetector
from ..core.context_filter import ContextFilter
from ..core.models import RunState
from ..core.token_counter import count_tokens


class CrewAIAdapter(BaseAdapter):
    def __init__(self, agent: Any, **kwargs: Any):
        super().__init__(agent=agent, **kwargs)
        self.last_run_state: RunState | None = None

    def kickoff(self, inputs: dict | None = None, **kwargs: Any) -> Any:
        budget = BudgetGate(budget=self._budget)
        early_exit = EarlyExitDetector(
            window=self._early_exit_window,
            threshold=self._early_exit_threshold,
        )
        goal = str(inputs) if inputs else ""
        ctx_filter = ContextFilter(threshold=self._relevance_threshold)
        if goal:
            ctx_filter.set_goal(goal)
        state = RunState.new(
            framework="crewai",
            model_name=self._model_name,
            budget_tokens=self._budget,
        )
        budget.consume(count_tokens(goal))

        original_callback = getattr(self._agent, "step_callback", None)

        def _step_callback(step_output: Any) -> None:
            content = str(step_output)
            budget.consume(count_tokens(content))
            gain = ctx_filter.score(content)
            early_exit.record(gain)
            if original_callback:
                original_callback(step_output)

        self._agent.step_callback = _step_callback

        try:
            result = self._agent.kickoff(inputs=inputs, **kwargs)
        finally:
            self._agent.step_callback = original_callback

        state.tokens_consumed = budget.consumed
        state.should_exit_early = early_exit.should_exit()
        state.task_success = not state.should_exit_early
        self.last_run_state = state

        # Fire-and-forget telemetry — never raises, never blocks
        from ..telemetry.client import get_client
        _client = get_client()
        if _client.enabled:
            _client.send(state, tokens_baseline=state.budget_tokens)

        return result

    def invoke(self, input: Any, **kwargs: Any) -> Any:
        inputs = input if isinstance(input, dict) else {"input": str(input)}
        return self.kickoff(inputs=inputs, **kwargs)
