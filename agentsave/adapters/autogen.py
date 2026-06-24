from typing import Any
from .base import BaseAdapter
from ..core.context_filter import ContextFilter
from ..core.early_exit import EarlyExitDetector
from ..core.budget import BudgetGate
from ..core.models import RunState
from ..core.token_counter import count_tokens


class AutoGenAdapter(BaseAdapter):
    def __init__(self, agent: Any, **kwargs: Any):
        super().__init__(agent=agent, **kwargs)
        self.last_run_state: RunState | None = None

    def initiate_chat(self, recipient: Any, message: str, **kwargs: Any) -> Any:
        ctx_filter = ContextFilter(threshold=self._relevance_threshold)
        ctx_filter.set_goal(message)
        early_exit = EarlyExitDetector(
            window=self._early_exit_window,
            threshold=self._early_exit_threshold,
        )
        budget = BudgetGate(budget=self._budget)
        state = RunState.new(
            framework="autogen",
            model_name=self._model_name,
            budget_tokens=self._budget,
        )
        budget.consume(count_tokens(message))

        def _process_message(
            agent_self: Any,
            messages: list[dict] | None = None,
            sender: Any = None,
            config: Any = None,
        ) -> tuple[bool, str | None]:
            if budget.is_exhausted() or early_exit.should_exit():
                state.should_exit_early = True
                return True, "Task complete (AgentSave budget/early-exit limit)."
            if messages:
                last_content = str(messages[-1].get("content", ""))
                tokens = count_tokens(last_content)
                budget.consume(tokens)
                gain = ctx_filter.score(last_content)
                early_exit.record(gain)
            return False, None

        if hasattr(self._agent, "register_reply"):
            self._agent.register_reply(
                trigger=lambda sender: True,
                reply_func=_process_message,
                position=0,
            )

        result = self._agent.initiate_chat(recipient, message=message, **kwargs)
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
        raise NotImplementedError(
            "AutoGen requires an explicit recipient agent. "
            "Use adapter.initiate_chat(recipient, message=...) directly."
        )
