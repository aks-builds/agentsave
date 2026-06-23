from agentsave.core.supervisor import loop
from agentsave.core.models import RunState

def test_loop_context_manager_basic():
    with loop(budget=10_000) as run:
        assert run.should_continue() is True
        run.observe("some tool output")
    assert run.state.run_id is not None

def test_loop_exits_when_budget_exhausted():
    with loop(budget=10) as run:
        run.state.tokens_consumed = 10
        run._budget.consume(10)
        assert run.should_continue() is False

def test_loop_state_tracks_framework():
    with loop(budget=100_000, model_name="gpt-4o", framework="raw") as run:
        run.observe("hello world this is some output text")
    assert run.state.model_name == "gpt-4o"
    assert run.state.framework == "raw"

def test_loop_should_continue_false_after_manual_stop():
    with loop(budget=100_000) as run:
        run.stop()
        assert run.should_continue() is False

def test_loop_task_success_true_on_normal_exit():
    with loop(budget=100_000) as run:
        run.observe("normal output")
    assert run.state.task_success is True

def test_loop_task_success_false_on_budget_exit():
    with loop(budget=5) as run:
        run._budget.consume(5)
        run.should_continue()  # triggers should_exit_early flag
    assert run.state.task_success is False
