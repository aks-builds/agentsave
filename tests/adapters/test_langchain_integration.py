import pytest

pytest_plugins = []


def test_langchain_chain_detected():
    pytest.importorskip("langchain_core.language_models.fake_chat_models")
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from agentsave import supervise

    llm = FakeListChatModel(responses=["Paris is the capital of France."])
    chain = ChatPromptTemplate.from_messages([("human", "{input}")]) | llm | StrOutputParser()

    supervised = supervise(chain)
    assert type(supervised).__name__ == "LangChainAdapter"


def test_langchain_chain_passes_through_answer():
    pytest.importorskip("langchain_core.language_models.fake_chat_models")
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from agentsave import supervise

    llm = FakeListChatModel(responses=["Paris is the capital of France."])
    chain = ChatPromptTemplate.from_messages([("human", "{input}")]) | llm | StrOutputParser()

    supervised = supervise(chain)
    result = supervised.invoke({"input": "What is the capital of France?"})
    assert "Paris" in result


def test_langchain_chain_records_run_state():
    pytest.importorskip("langchain_core.language_models.fake_chat_models")
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from agentsave import supervise

    llm = FakeListChatModel(responses=["The answer is 42."])
    chain = ChatPromptTemplate.from_messages([("human", "{input}")]) | llm | StrOutputParser()
    supervised = supervise(chain)
    supervised.invoke({"input": "What is 6 times 7?"})

    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "langchain"
    # tokens_consumed must reflect BOTH input AND output (not just the pre-invoke input tokenization)
    # If only input was counted, tokens_consumed == count_tokens(str({"input": "What is 6 times 7?"}))
    # Output "The answer is 42." adds more tokens, so total must be higher than input alone
    from agentsave.core.token_counter import count_tokens
    input_only_tokens = count_tokens(str({"input": "What is 6 times 7?"}))
    assert supervised.last_run_state.tokens_consumed > input_only_tokens, (
        f"tokens_consumed ({supervised.last_run_state.tokens_consumed}) should exceed "
        f"input-only count ({input_only_tokens}) — output tokens must also be counted"
    )
