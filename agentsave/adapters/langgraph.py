from typing import Any
from .base import BaseAdapter
from ..core.budget import BudgetGate
from ..core.models import RunState
from ..core.token_counter import count_tokens


class LangGraphAdapter(BaseAdapter):
    def __init__(self, agent: Any, **kwargs: Any):
        super().__init__(agent=agent, **kwargs)
        self.last_run_state: RunState | None = None

    def invoke(self, input: dict, **kwargs: Any) -> dict:
        budget = BudgetGate(budget=self._budget)
        state = RunState.new(
            framework="langgraph",
            model_name=self._model_name,
            budget_tokens=self._budget,
        )
        budget.consume(count_tokens(str(input)))
        result = self._agent.invoke(input, **kwargs)
        budget.consume(count_tokens(str(result)))
        state.tokens_consumed = budget.consumed
        state.task_success = True
        self.last_run_state = state

        # Fire-and-forget telemetry — never raises, never blocks
        from ..telemetry.client import get_client
        _client = get_client()
        if _client.enabled:
            _client.send(state, tokens_baseline=state.budget_tokens)

        return result

    def stream(self, input: dict, **kwargs: Any):
        budget = BudgetGate(budget=self._budget)
        state = RunState.new(
            framework="langgraph",
            model_name=self._model_name,
            budget_tokens=self._budget,
        )
        budget.consume(count_tokens(str(input)))
        for chunk in self._agent.stream(input, **kwargs):
            if budget.is_exhausted():
                state.should_exit_early = True
                break
            budget.consume(count_tokens(str(chunk)))
            yield chunk
        state.tokens_consumed = budget.consumed
        state.task_success = not state.should_exit_early
        self.last_run_state = state

        # Fire-and-forget telemetry — never raises, never blocks
        from ..telemetry.client import get_client
        _client = get_client()
        if _client.enabled:
            _client.send(state, tokens_baseline=state.budget_tokens)
