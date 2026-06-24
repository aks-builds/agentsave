import pytest


def test_autogen_agent_detected():
    pytest.importorskip("autogen")
    from autogen import ConversableAgent
    from agentsave import supervise

    agent = ConversableAgent(
        name="test_agent",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        default_auto_reply="Task complete.",
        llm_config=False,
    )
    supervised = supervise(agent)
    assert type(supervised).__name__ == "AutoGenAdapter"


def test_autogen_initiate_chat_records_run_state():
    pytest.importorskip("autogen")
    from autogen import ConversableAgent
    from agentsave import supervise

    # ag2/autogen >=0.13: max_consecutive_auto_reply=0 on both sides with
    # max_turns=1 causes the summary lookup to fail (recipient has no message).
    # Use max_consecutive_auto_reply=1 on the recipient so the chat completes.
    initiator = ConversableAgent(
        name="initiator",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        default_auto_reply="I'm done.",
        llm_config=False,
    )
    recipient = ConversableAgent(
        name="recipient",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        default_auto_reply="Task complete.",
        llm_config=False,
    )
    supervised = supervise(initiator)
    supervised.initiate_chat(recipient, message="Hello", max_turns=1)

    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "autogen"
    assert supervised.last_run_state.tokens_consumed > 0


def test_autogen_invoke_raises_not_implemented():
    pytest.importorskip("autogen")
    from autogen import ConversableAgent
    from agentsave import supervise

    agent = ConversableAgent(
        name="test",
        human_input_mode="NEVER",
        llm_config=False,
    )
    supervised = supervise(agent)
    with pytest.raises(NotImplementedError, match="explicit recipient"):
        supervised.invoke({"input": "test"})
