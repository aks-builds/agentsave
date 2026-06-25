import pytest


def _make_fake_model():
    """Minimal smolagents Model that always returns a final_answer tool call."""
    smolagents = pytest.importorskip("smolagents")
    from smolagents.models import (
        Model,
        ChatMessage,
        ChatMessageToolCall,
        ChatMessageToolCallFunction,
        MessageRole,
        TokenUsage,
    )

    class FakeModel(Model):
        def __init__(self):
            self.model_id = "fake-model"
            self.last_input_token_count = 10
            self.last_output_token_count = 5

        def generate(self, messages, stop_sequences=None, tools_to_call_from=None, **kwargs):
            fn = ChatMessageToolCallFunction(
                name="final_answer",
                arguments='{"answer": "The answer is 42."}',
            )
            tool_call = ChatMessageToolCall(id="toolu_01", type="function", function=fn)
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content="",
                tool_calls=[tool_call],
                token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            )

    return FakeModel()


def test_smolagents_agent_detected():
    pytest.importorskip("smolagents")
    from smolagents import ToolCallingAgent
    from agentsave import supervise

    agent = ToolCallingAgent(tools=[], model=_make_fake_model(), max_steps=2)
    supervised = supervise(agent)
    assert type(supervised).__name__ == "SmolagentsAdapter"


def test_smolagents_run_records_run_state():
    pytest.importorskip("smolagents")
    from smolagents import ToolCallingAgent
    from agentsave import supervise

    agent = ToolCallingAgent(tools=[], model=_make_fake_model(), max_steps=2)
    supervised = supervise(agent)
    result = supervised.run("What is 6 * 7?")

    assert "42" in str(result)
    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "smolagents"
    assert supervised.last_run_state.tokens_consumed > 0


def test_smolagents_restores_callbacks_after_run():
    pytest.importorskip("smolagents")
    from smolagents import ToolCallingAgent
    from smolagents.memory import CallbackRegistry
    from agentsave import supervise

    agent = ToolCallingAgent(tools=[], model=_make_fake_model(), max_steps=2)
    registry = agent.step_callbacks
    assert isinstance(registry, CallbackRegistry)
    callbacks_before = {cls: list(cbs) for cls, cbs in registry._callbacks.items()}

    supervised = supervise(agent)
    supervised.run("test task")

    callbacks_after = {cls: list(cbs) for cls, cbs in registry._callbacks.items()}
    assert callbacks_before == callbacks_after
