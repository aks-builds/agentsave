from unittest.mock import MagicMock
from agentsave.adapters.langchain import LangChainAdapter, _SupervisorCallback

def _make_mock_agent(return_value=None):
    agent = MagicMock()
    agent.__class__.__name__ = "AgentExecutor"
    agent.__class__.__module__ = "langchain.agents"
    agent.invoke.return_value = return_value or {"output": "Paris is the capital of France."}
    agent.tools = []
    return agent

def test_langchain_adapter_invoke_returns_result():
    mock_agent = _make_mock_agent()
    adapter = LangChainAdapter(agent=mock_agent, budget=100_000)
    result = adapter.invoke({"input": "What is the capital of France?"})
    assert result["output"] == "Paris is the capital of France."

def test_langchain_adapter_tracks_model_name():
    mock_agent = _make_mock_agent()
    adapter = LangChainAdapter(agent=mock_agent, model_name="claude-sonnet-4-6")
    assert adapter._model_name == "claude-sonnet-4-6"

def test_langchain_adapter_exposes_run_state():
    mock_agent = _make_mock_agent()
    adapter = LangChainAdapter(agent=mock_agent, budget=100_000)
    adapter.invoke({"input": "test question"})
    assert adapter.last_run_state is not None
    assert adapter.last_run_state.framework == "langchain"

def test_langchain_adapter_injects_callback():
    """Callback is injected into agent.invoke call kwargs."""
    mock_agent = _make_mock_agent()
    adapter = LangChainAdapter(agent=mock_agent, budget=100_000)
    adapter.invoke({"input": "What is the capital of France?"})
    call_kwargs = mock_agent.invoke.call_args[1]
    callbacks = call_kwargs.get("callbacks", [])
    assert any(isinstance(cb, _SupervisorCallback) for cb in callbacks)

def test_supervisor_callback_records_tool_output():
    from agentsave.core.context_filter import ContextFilter
    from agentsave.core.early_exit import EarlyExitDetector
    from agentsave.core.budget import BudgetGate
    from agentsave.core.models import RunState
    ctx = ContextFilter(threshold=0.1)
    ctx.set_goal("Paris capital")
    eed = EarlyExitDetector(window=3, threshold=0.05)
    budget = BudgetGate(budget=100_000)
    state = RunState.new("langchain", "gpt-4o", 100_000)
    cb = _SupervisorCallback(ctx, eed, budget, state)
    cb.on_tool_end("Paris is the capital of France")
    assert budget.consumed > 0
