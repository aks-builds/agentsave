class BudgetGate:
    def __init__(self, budget: int):
        self.budget = budget
        self._consumed: int = 0

    def consume(self, tokens: int) -> None:
        self._consumed += tokens

    @property
    def consumed(self) -> int:
        return self._consumed

    @property
    def remaining(self) -> int:
        return max(0, self.budget - self._consumed)

    def is_exhausted(self) -> bool:
        return self._consumed >= self.budget

    def would_exceed(self, tokens: int) -> bool:
        return (self._consumed + tokens) > self.budget
