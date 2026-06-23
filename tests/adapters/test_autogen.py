from unittest.mock import MagicMock
from agentsave.adapters.autogen import AutoGenAdapter

def _make_mock_agent():
    agent = MagicMock()
    agent.__class__.__name__ = "ConversableAgent"
    agent.__class__.__module__ = "autogen"
    agent.initiate_chat.return_value = MagicMock(summary="The answer is 42.")
    return agent

def test_autogen_adapter_initiate_chat():
    agent = _make_mock_agent()
    recipient = MagicMock()
    adapter = AutoGenAdapter(agent=agent, budget=100_000)
    result = adapter.initiate_chat(recipient, message="What is 6 * 7?")
    assert result.summary == "The answer is 42."

def test_autogen_adapter_exposes_run_state():
    agent = _make_mock_agent()
    recipient = MagicMock()
    adapter = AutoGenAdapter(agent=agent, budget=100_000)
    adapter.initiate_chat(recipient, message="test")
    assert adapter.last_run_state is not None
    assert adapter.last_run_state.framework == "autogen"

def test_autogen_invoke_raises():
    import pytest
    agent = _make_mock_agent()
    adapter = AutoGenAdapter(agent=agent, budget=100_000)
    with pytest.raises(NotImplementedError, match="explicit recipient"):
        adapter.invoke({"input": "test"})
