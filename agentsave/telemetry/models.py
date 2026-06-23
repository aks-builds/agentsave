from dataclasses import dataclass
from datetime import datetime, timezone
from ..core.models import RunState


@dataclass
class SavingsEvent:
    run_id: str
    framework: str
    model_name: str
    tokens_before: int
    tokens_after: int
    iterations_total: int
    iterations_saved: int
    task_success: bool
    timestamp: str

    @classmethod
    def from_run_state(cls, state: RunState, tokens_baseline: int) -> "SavingsEvent":
        return cls(
            run_id=state.run_id,
            framework=state.framework,
            model_name=state.model_name,
            tokens_before=tokens_baseline,
            tokens_after=state.tokens_consumed,
            iterations_total=len(state.iterations),
            iterations_saved=0,
            task_success=state.task_success,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "framework": self.framework,
            "model_name": self.model_name,
            "tokens_before": self.tokens_before,
            "tokens_after": self.tokens_after,
            "iterations_total": self.iterations_total,
            "iterations_saved": self.iterations_saved,
            "task_success": self.task_success,
            "timestamp": self.timestamp,
        }
