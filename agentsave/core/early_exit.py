from collections import deque


class EarlyExitDetector:
    def __init__(self, window: int = 3, threshold: float = 0.05):
        self.window = window
        self.threshold = threshold
        self._gains: deque[float] = deque(maxlen=window)

    def record(self, gain: float) -> None:
        self._gains.append(gain)

    def should_exit(self) -> bool:
        if len(self._gains) < self.window:
            return False
        return all(g < self.threshold for g in self._gains)

    def reset(self) -> None:
        self._gains.clear()
