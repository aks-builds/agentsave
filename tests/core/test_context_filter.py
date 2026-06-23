from agentsave.core.context_filter import ContextFilter

def test_no_goal_passes_everything():
    cf = ContextFilter()
    assert cf.is_relevant("any observation") is True
    assert cf.score("any observation") == 1.0

def test_relevant_observation_scores_high():
    cf = ContextFilter(threshold=0.1)
    cf.set_goal("What is the capital of France?")
    score = cf.score("Paris is the capital city of France, located in northern France.")
    assert score > 0.1

def test_irrelevant_observation_scores_low():
    cf = ContextFilter(threshold=0.3)
    cf.set_goal("What is the capital of France?")
    score = cf.score("The stock market closed higher today with tech stocks leading gains.")
    assert score < 0.3

def test_filter_removes_irrelevant():
    cf = ContextFilter(threshold=0.2)
    cf.set_goal("Python programming language")
    observations = [
        "Python is a high-level programming language known for its simplicity.",
        "The weather today is sunny with a high of 25 degrees.",
        "Python uses indentation to define code blocks.",
    ]
    filtered = cf.filter(observations)
    assert len(filtered) < len(observations)
    assert all("Python" in obs for obs in filtered)

def test_empty_observation_scores_zero():
    cf = ContextFilter()
    cf.set_goal("some goal")
    assert cf.score("") == 0.0
