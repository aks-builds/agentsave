import pytest


def _make_fake_crew(kickoff_return="done"):
    """
    Create a plain-Python object that passes supervise()'s crewai detection.

    crewai.Crew is a Pydantic v2 model on Python 3.11; its __setattr__
    raises ValueError when assigning non-field names like 'kickoff'.
    We mimic the type-detection signature (type(x).__name__ == "Crew" and
    "crewai" in type(x).__module__) without using the real Pydantic model.
    """
    class FakeCrew:
        step_callback = None

        def kickoff(self, inputs=None, **kwargs):
            return kickoff_return

    FakeCrew.__name__ = "Crew"
    FakeCrew.__module__ = "crewai.crew"
    return FakeCrew()


def test_crewai_crew_detected():
    pytest.importorskip("crewai")
    from agentsave import supervise

    crew = _make_fake_crew("Research complete: Paris is the capital.")
    supervised = supervise(crew)
    assert type(supervised).__name__ == "CrewAIAdapter"


def test_crewai_kickoff_passes_through():
    pytest.importorskip("crewai")
    from agentsave import supervise

    crew = _make_fake_crew("Research complete: Paris is the capital.")
    supervised = supervise(crew)
    result = supervised.kickoff(inputs={"topic": "France capital"})
    assert "Paris" in str(result)


def test_crewai_records_run_state():
    pytest.importorskip("crewai")
    from agentsave import supervise

    crew = _make_fake_crew("Done.")
    supervised = supervise(crew)
    supervised.kickoff(inputs={})
    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "crewai"
