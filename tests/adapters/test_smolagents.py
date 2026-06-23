from unittest.mock import MagicMock
from agentsave.adapters.smolagents import SmolagentsAdapter

def _make_mock_agent():
    agent = MagicMock()
    agent.__class__.__name__ = "ToolCallingAgent"
    agent.__class__.__module__ = "smolagents.agents"
    agent.run.return_value = "The answer is 42."
    agent.step_callbacks = []
    return agent

def test_smolagents_adapter_run():
    agent = _make_mock_agent()
    adapter = SmolagentsAdapter(agent=agent, budget=100_000)
    result = adapter.run("What is 6 * 7?")
    assert result == "The answer is 42."

def test_smolagents_adapter_exposes_run_state():
    agent = _make_mock_agent()
    adapter = SmolagentsAdapter(agent=agent, budget=100_000)
    adapter.run("test task")
    assert adapter.last_run_state is not None
    assert adapter.last_run_state.framework == "smolagents"

def test_smolagents_invoke_calls_run():
    agent = _make_mock_agent()
    adapter = SmolagentsAdapter(agent=agent, budget=100_000)
    result = adapter.invoke({"input": "What is 6 * 7?"})
    assert result == "The answer is 42."

def test_smolagents_restores_callbacks_after_run():
    agent = _make_mock_agent()
    original_cb = MagicMock()
    agent.step_callbacks = [original_cb]
    adapter = SmolagentsAdapter(agent=agent, budget=100_000)
    adapter.run("test task")
    assert agent.step_callbacks == [original_cb]
