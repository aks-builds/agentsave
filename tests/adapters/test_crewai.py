from unittest.mock import MagicMock
from agentsave.adapters.crewai import CrewAIAdapter

def _make_mock_crew():
    crew = MagicMock()
    crew.__class__.__name__ = "Crew"
    crew.__class__.__module__ = "crewai"
    crew.kickoff.return_value = "Research complete: Paris is the capital."
    crew.step_callback = None
    return crew

def test_crewai_adapter_kickoff():
    crew = _make_mock_crew()
    adapter = CrewAIAdapter(agent=crew, budget=100_000)
    result = adapter.kickoff(inputs={"topic": "France capital"})
    assert "Paris" in str(result)

def test_crewai_adapter_exposes_run_state():
    crew = _make_mock_crew()
    adapter = CrewAIAdapter(agent=crew, budget=100_000)
    adapter.kickoff(inputs={"topic": "test"})
    assert adapter.last_run_state is not None
    assert adapter.last_run_state.framework == "crewai"

def test_crewai_invoke_calls_kickoff():
    crew = _make_mock_crew()
    adapter = CrewAIAdapter(agent=crew, budget=100_000)
    result = adapter.invoke({"topic": "France"})
    assert "Paris" in str(result)
