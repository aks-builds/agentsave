import pytest
from typing import TypedDict


def _build_simple_graph():
    pytest.importorskip("langgraph")
    from langgraph.graph import StateGraph, END

    class State(TypedDict):
        question: str
        answer: str

    def answer_node(state: State) -> State:
        return {"question": state["question"], "answer": f"42 is the answer to: {state['question']}"}

    builder = StateGraph(State)
    builder.add_node("answer", answer_node)
    builder.set_entry_point("answer")
    builder.add_edge("answer", END)
    return builder.compile()


def test_langgraph_graph_detected():
    pytest.importorskip("langgraph")
    from agentsave import supervise
    graph = _build_simple_graph()
    supervised = supervise(graph)
    assert type(supervised).__name__ == "LangGraphAdapter"


def test_langgraph_graph_passes_through_result():
    pytest.importorskip("langgraph")
    from agentsave import supervise
    graph = _build_simple_graph()
    supervised = supervise(graph)
    result = supervised.invoke({"question": "life universe everything", "answer": ""})
    assert "42" in result["answer"]


def test_langgraph_graph_records_run_state():
    pytest.importorskip("langgraph")
    from agentsave import supervise
    graph = _build_simple_graph()
    supervised = supervise(graph)
    supervised.invoke({"question": "test", "answer": ""})
    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "langgraph"
    assert supervised.last_run_state.tokens_consumed > 0
