from typing import Any
from .base import BaseAdapter
from ..core.budget import BudgetGate
from ..core.early_exit import EarlyExitDetector
from ..core.context_filter import ContextFilter
from ..core.models import RunState
from ..core.token_counter import count_tokens


class SmolagentsAdapter(BaseAdapter):
    def __init__(self, agent: Any, **kwargs: Any):
        super().__init__(agent=agent, **kwargs)
        self.last_run_state: RunState | None = None

    def run(self, task: str, **kwargs: Any) -> Any:
        budget = BudgetGate(budget=self._budget)
        early_exit = EarlyExitDetector(
            window=self._early_exit_window,
            threshold=self._early_exit_threshold,
        )
        ctx_filter = ContextFilter(threshold=self._relevance_threshold)
        ctx_filter.set_goal(task)
        state = RunState.new(
            framework="smolagents",
            model_name=self._model_name,
            budget_tokens=self._budget,
        )
        budget.consume(count_tokens(task))

        def _supervisor_callback(memory_step: Any) -> None:
            content = str(getattr(memory_step, "observations", memory_step))
            budget.consume(count_tokens(content))
            gain = ctx_filter.score(content)
            early_exit.record(gain)
            if early_exit.should_exit() or budget.is_exhausted():
                state.should_exit_early = True

        step_callbacks = getattr(self._agent, "step_callbacks", None)
        # smolagents >=1.10 uses CallbackRegistry (has .register()); older API
        # and mocks use a plain list — handle both so unit tests keep working.
        using_registry = step_callbacks is not None and hasattr(step_callbacks, "register")
        if using_registry:
            snapshot = {cls: list(cbs) for cls, cbs in step_callbacks._callbacks.items()}
            step_callbacks.register(object, _supervisor_callback)
        elif step_callbacks is not None:
            original_list = list(step_callbacks)
            self._agent.step_callbacks = original_list + [_supervisor_callback]

        try:
            result = self._agent.run(task, **kwargs)
        finally:
            if using_registry:
                step_callbacks._callbacks = snapshot
            elif step_callbacks is not None:
                self._agent.step_callbacks = original_list

        state.tokens_consumed = budget.consumed
        state.task_success = not state.should_exit_early
        self.last_run_state = state

        # Fire-and-forget telemetry — never raises, never blocks
        from ..telemetry.client import get_client
        _client = get_client()
        if _client.enabled:
            _client.send(state, tokens_baseline=state.budget_tokens)

        return result

    def invoke(self, input: Any, **kwargs: Any) -> Any:
        task = input.get("input", str(input)) if isinstance(input, dict) else str(input)
        return self.run(task, **kwargs)
