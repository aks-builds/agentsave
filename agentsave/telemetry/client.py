import threading
from typing import Optional
from .models import SavingsEvent
from ..core.models import RunState

_DEFAULT_API_URL = "https://app.agentsave.io/api/events"


class TelemetryClient:
    def __init__(
        self,
        enabled: bool = False,
        api_url: str = _DEFAULT_API_URL,
        token: Optional[str] = None,
    ):
        self.enabled = enabled
        self._api_url = api_url
        self._token = token

    def send(self, state: RunState, tokens_baseline: int) -> None:
        if not self.enabled or not self._token:
            return
        event = SavingsEvent.from_run_state(state, tokens_baseline=tokens_baseline)
        thread = threading.Thread(
            target=self._post, args=(event,), daemon=True
        )
        thread.start()

    def _post(self, event: SavingsEvent) -> None:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
            with httpx.Client(timeout=5.0) as client:
                client.post(self._api_url, json=event.to_dict(), headers=headers)
        except Exception:
            pass


def get_client() -> TelemetryClient:
    """Load config from ~/.agentsave/config.json and return a configured client."""
    import json
    import os
    config_file = os.path.expanduser("~/.agentsave/config.json")
    if not os.path.exists(config_file):
        return TelemetryClient(enabled=False)
    try:
        with open(config_file) as f:
            cfg = json.load(f)
    except Exception:
        return TelemetryClient(enabled=False)
    token = cfg.get("token")
    enabled = bool(token) and cfg.get("telemetry", False)
    api_url = cfg.get("api_url", _DEFAULT_API_URL)
    return TelemetryClient(enabled=enabled, api_url=api_url, token=token)
