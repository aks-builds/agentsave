from unittest.mock import MagicMock
from agentsave.adapters.langgraph import LangGraphAdapter

def _make_mock_graph(return_value=None):
    graph = MagicMock()
    graph.__class__.__name__ = "CompiledStateGraph"
    graph.__class__.__module__ = "langgraph.graph.state"
    graph.invoke.return_value = return_value or {"messages": ["final answer"]}
    return graph

def test_langgraph_adapter_invoke_returns_result():
    graph = _make_mock_graph()
    adapter = LangGraphAdapter(agent=graph, budget=100_000)
    result = adapter.invoke({"messages": ["What is 2+2?"]})
    assert result == {"messages": ["final answer"]}

def test_langgraph_adapter_exposes_run_state():
    graph = _make_mock_graph()
    adapter = LangGraphAdapter(agent=graph, budget=100_000)
    adapter.invoke({"messages": ["test"]})
    assert adapter.last_run_state is not None
    assert adapter.last_run_state.framework == "langgraph"
