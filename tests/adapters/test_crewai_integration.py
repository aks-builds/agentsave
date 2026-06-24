import pytest


def test_crewai_crew_detected():
    crewai = pytest.importorskip("crewai")
    from crewai import Crew
    from agentsave import supervise

    crew = Crew.__new__(Crew)
    crew.kickoff = lambda **kw: "Research complete: Paris is the capital."
    crew.step_callback = None

    supervised = supervise(crew)
    assert type(supervised).__name__ == "CrewAIAdapter"


def test_crewai_kickoff_passes_through():
    pytest.importorskip("crewai")
    from crewai import Crew
    from agentsave import supervise

    crew = Crew.__new__(Crew)
    crew.kickoff = lambda **kw: "Research complete: Paris is the capital."
    crew.step_callback = None

    supervised = supervise(crew)
    result = supervised.kickoff(inputs={"topic": "France capital"})
    assert "Paris" in str(result)


def test_crewai_records_run_state():
    pytest.importorskip("crewai")
    from crewai import Crew
    from agentsave import supervise

    crew = Crew.__new__(Crew)
    crew.kickoff = lambda **kw: "Done."
    crew.step_callback = None

    supervised = supervise(crew)
    supervised.kickoff(inputs={})
    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "crewai"
