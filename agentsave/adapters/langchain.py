from typing import Any
from .base import BaseAdapter
from ..core.context_filter import ContextFilter
from ..core.early_exit import EarlyExitDetector
from ..core.budget import BudgetGate
from ..core.models import RunState
from ..core.token_counter import count_tokens


class _SupervisorCallback:
    """LangChain-compatible callback handler (duck-typed, no langchain import needed)."""

    def __init__(
        self,
        ctx_filter: ContextFilter,
        early_exit: EarlyExitDetector,
        budget: BudgetGate,
        state: RunState,
    ):
        self._ctx_filter = ctx_filter
        self._early_exit = early_exit
        self._budget = budget
        self._state = state
        self.raise_error = False

    # LangChain callback protocol — called after each tool finishes
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        tokens = count_tokens(output)
        self._budget.consume(tokens)
        gain = self._ctx_filter.score(output)
        self._early_exit.record(gain)
        if self._budget.is_exhausted() or self._early_exit.should_exit():
            self._state.should_exit_early = True

    # LangChain callback protocol stubs — must exist to satisfy the interface
    def on_llm_start(self, *args: Any, **kwargs: Any) -> None: pass
    def on_llm_end(self, *args: Any, **kwargs: Any) -> None: pass
    def on_llm_error(self, *args: Any, **kwargs: Any) -> None: pass
    def on_chain_start(self, *args: Any, **kwargs: Any) -> None: pass
    def on_chain_end(self, *args: Any, **kwargs: Any) -> None: pass
    def on_chain_error(self, *args: Any, **kwargs: Any) -> None: pass
    def on_tool_start(self, *args: Any, **kwargs: Any) -> None: pass
    def on_tool_error(self, *args: Any, **kwargs: Any) -> None: pass
    def on_agent_action(self, *args: Any, **kwargs: Any) -> None: pass
    def on_agent_finish(self, *args: Any, **kwargs: Any) -> None: pass
    def on_text(self, *args: Any, **kwargs: Any) -> None: pass


class LangChainAdapter(BaseAdapter):
    def __init__(self, agent: Any, **kwargs: Any):
        super().__init__(agent=agent, **kwargs)
        self.last_run_state: RunState | None = None

    def invoke(self, input: dict, **kwargs: Any) -> dict:
        goal = input.get("input", str(input))
        ctx_filter = ContextFilter(threshold=self._relevance_threshold)
        ctx_filter.set_goal(goal)
        early_exit = EarlyExitDetector(
            window=self._early_exit_window,
            threshold=self._early_exit_threshold,
        )
        budget = BudgetGate(budget=self._budget)
        state = RunState.new(
            framework="langchain",
            model_name=self._model_name,
            budget_tokens=self._budget,
        )
        budget.consume(count_tokens(str(input)))

        callback = _SupervisorCallback(ctx_filter, early_exit, budget, state)

        # Inject callback — works without importing langchain (duck-typed)
        agent_type = type(self._agent).__name__
        # LCEL Runnables (RunnableSequence, RunnableParallel, etc.) accept callbacks via config
        # Old-style AgentExecutor accepts callbacks as a direct kwarg
        if "Runnable" in agent_type or "Chain" in agent_type:
            existing_config = kwargs.pop("config", None) or {}
            if isinstance(existing_config, dict):
                existing_cbs = list(existing_config.get("callbacks", []))
            else:
                existing_cbs = []
            config = {**existing_config, "callbacks": existing_cbs + [callback]}
            result = self._agent.invoke(input, config=config, **kwargs)
        else:
            existing_callbacks = kwargs.pop("callbacks", None) or []
            kwargs["callbacks"] = list(existing_callbacks) + [callback]
            result = self._agent.invoke(input, **kwargs)

        output_tokens = count_tokens(str(result))
        budget.consume(output_tokens)
        state.task_success = not state.should_exit_early
        state.tokens_consumed = budget.consumed
        self.last_run_state = state

        from ..telemetry.client import get_client
        _client = get_client()
        if _client.enabled:
            _client.send(state, tokens_baseline=state.budget_tokens)

        return result
