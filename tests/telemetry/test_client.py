from agentsave.telemetry.client import TelemetryClient
from agentsave.telemetry.models import SavingsEvent
from agentsave.core.models import RunState


def _make_state() -> RunState:
    s = RunState.new(framework="langchain", model_name="gpt-4o", budget_tokens=100_000)
    s.tokens_consumed = 8_650
    s.task_success = True
    return s


def test_savings_event_from_state():
    state = _make_state()
    event = SavingsEvent.from_run_state(state, tokens_baseline=12_400)
    assert event.framework == "langchain"
    assert event.model_name == "gpt-4o"
    assert event.tokens_before == 12_400
    assert event.tokens_after == 8_650
    assert event.task_success is True


def test_telemetry_disabled_by_default():
    client = TelemetryClient()
    assert client.enabled is False


def test_telemetry_send_does_not_raise_when_disabled():
    client = TelemetryClient(enabled=False)
    state = _make_state()
    client.send(state, tokens_baseline=12_400)


def test_telemetry_send_does_not_raise_on_network_error():
    client = TelemetryClient(enabled=True, api_url="http://localhost:9999", token="test")
    state = _make_state()
    client.send(state, tokens_baseline=12_400)
    import time
    time.sleep(0.2)


def test_get_client_returns_disabled_when_no_config():
    from agentsave.telemetry.client import get_client
    import unittest.mock as mock
    with mock.patch("os.path.exists", return_value=False):
        client = get_client()
    assert client.enabled is False
