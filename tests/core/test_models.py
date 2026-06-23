from agentsave.core.models import IterationRecord, RunState
import time

def test_iteration_record_defaults():
    rec = IterationRecord(iteration=1, input_tokens=100, output_tokens=50)
    assert rec.iteration == 1
    assert rec.input_tokens == 100
    assert rec.output_tokens == 50
    assert rec.information_gain == 0.0
    assert rec.timestamp > 0

def test_run_state_initial():
    state = RunState(run_id="abc", framework="langchain", model_name="gpt-4o", budget_tokens=50_000)
    assert state.tokens_consumed == 0
    assert state.iterations == []
    assert state.should_exit_early is False
    assert state.task_success is False

def test_run_state_total_tokens():
    state = RunState(run_id="abc", framework="langchain", model_name="gpt-4o", budget_tokens=50_000)
    state.iterations.append(IterationRecord(iteration=1, input_tokens=200, output_tokens=80))
    state.iterations.append(IterationRecord(iteration=2, input_tokens=180, output_tokens=60))
    assert state.total_tokens == 520
