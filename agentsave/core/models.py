from dataclasses import dataclass, field
import time
import uuid


@dataclass
class IterationRecord:
    iteration: int
    input_tokens: int
    output_tokens: int
    information_gain: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class RunState:
    run_id: str
    framework: str
    model_name: str
    budget_tokens: int
    tokens_consumed: int = 0
    iterations: list = field(default_factory=list)
    should_exit_early: bool = False
    task_success: bool = False

    @property
    def total_tokens(self) -> int:
        return sum(r.input_tokens + r.output_tokens for r in self.iterations)

    @classmethod
    def new(cls, framework: str, model_name: str, budget_tokens: int) -> "RunState":
        return cls(
            run_id=str(uuid.uuid4()),
            framework=framework,
            model_name=model_name,
            budget_tokens=budget_tokens,
        )
