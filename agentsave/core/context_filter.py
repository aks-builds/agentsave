from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ContextFilter:
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self._goal: str = ""

    def set_goal(self, goal: str) -> None:
        self._goal = goal.strip()

    def score(self, observation: str) -> float:
        if not observation or not observation.strip():
            return 0.0
        if not self._goal:
            return 1.0
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            matrix = vectorizer.fit_transform([self._goal, observation])
            return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        except ValueError:
            return 0.0

    def is_relevant(self, observation: str) -> bool:
        return self.score(observation) >= self.threshold

    def filter(self, observations: list[str]) -> list[str]:
        return [obs for obs in observations if self.is_relevant(obs)]
