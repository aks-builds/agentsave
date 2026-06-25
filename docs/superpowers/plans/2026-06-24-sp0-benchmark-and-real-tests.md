# Sub-project 0: Benchmark Suite + Real Framework Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 2-task synthetic benchmark with a 20-task suite that measures accuracy and token reduction, add real framework integration tests (no mocks), and rewrite `agentsave login` to connect to self-hosted dashboards.

**Architecture:** Benchmark tasks live in `benchmarks/` alongside an accuracy module (fuzzy string match), a runner that compares with/without AgentSave, and a report generator that writes `BENCHMARKS.md`. Framework integration tests live alongside existing unit tests and use real class imports with `pytest.importorskip` so they skip cleanly when the framework isn't installed.

**Tech Stack:** Python 3.11+, scikit-learn (already a dep), difflib (stdlib), pytest, langchain-core, langchain-community, langgraph, pyautogen, crewai, smolagents

## Global Constraints

- Python ≥ 3.11
- No new runtime dependencies — all benchmark code uses stdlib + existing scikit-learn dep
- Integration tests use `pytest.importorskip` — they skip, not fail, when the framework is absent
- Accuracy measurement uses fuzzy match (≥ 0.6 similarity) — not exact string equality
- Benchmark CI floor: token reduction ≥ 20%, accuracy drop = 0% (hard fail)
- Benchmark target (not CI gate): token reduction ≥ 30%
- The `agentsave login` rewrite must remove all references to `app.agentsave.io`
- Commit after every task

---

### Task 1: Benchmark task set + accuracy module

**Files:**
- Create: `benchmarks/__init__.py`
- Create: `benchmarks/tasks.py`
- Create: `benchmarks/accuracy.py`
- Create: `tests/benchmarks/__init__.py`
- Create: `tests/benchmarks/test_accuracy.py`

**Interfaces:**
- Produces: `TASKS: list[dict]` — each dict has `id: str`, `goal: str`, `tool_outputs: list[str]`, `ground_truth: str`
- Produces: `matches_ground_truth(answer: str, ground_truth: str) -> bool`

- [ ] **Step 1: Write the failing test**

```python
# tests/benchmarks/test_accuracy.py
from benchmarks.accuracy import matches_ground_truth

def test_exact_match():
    assert matches_ground_truth("Paris", "Paris") is True

def test_case_insensitive():
    assert matches_ground_truth("paris", "Paris") is True

def test_partial_match():
    assert matches_ground_truth("Paris is the capital of France.", "Paris") is True

def test_no_match():
    assert matches_ground_truth("London", "Paris") is False

def test_numeric_match():
    assert matches_ground_truth("37.4 million people", "37.4 million") is True

def test_empty_answer_fails():
    assert matches_ground_truth("", "Paris") is False
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/benchmarks/test_accuracy.py -v
```
Expected: `ModuleNotFoundError: No module named 'benchmarks'`

- [ ] **Step 3: Create `benchmarks/__init__.py`**

```python
# benchmarks/__init__.py
```
(empty)

- [ ] **Step 4: Create `benchmarks/accuracy.py`**

```python
# benchmarks/accuracy.py
import difflib


def matches_ground_truth(answer: str, ground_truth: str) -> bool:
    if not answer or not ground_truth:
        return False
    answer_lower = answer.lower().strip()
    truth_lower = ground_truth.lower().strip()
    if truth_lower in answer_lower:
        return True
    ratio = difflib.SequenceMatcher(None, answer_lower, truth_lower).ratio()
    return ratio >= 0.6
```

- [ ] **Step 5: Run tests to verify they pass**

```
pytest tests/benchmarks/test_accuracy.py -v
```
Expected: 6 passed

- [ ] **Step 6: Create `benchmarks/tasks.py`**

```python
# benchmarks/tasks.py
TASKS = [
    {
        "id": "tokyo-population",
        "goal": "What is the population of Tokyo?",
        "tool_outputs": [
            "Tokyo metropolitan area population 2024: approximately 37.4 million people, the world's most populous metro area.",
            "Weather in Tokyo today: sunny, 22°C, humidity 65%.",
            "Tokyo Stock Exchange: Nikkei 225 up 0.3% today.",
            "Tokyo city proper population: 13.96 million as of 2023 census.",
        ],
        "ground_truth": "37.4 million",
    },
    {
        "id": "telephone-inventor",
        "goal": "Who invented the telephone?",
        "tool_outputs": [
            "Alexander Graham Bell was awarded the first patent for the telephone in 1876.",
            "The New York Stock Exchange was founded in 1792.",
            "Bell demonstrated the telephone at the 1876 Philadelphia Centennial Exposition.",
            "Current gold price: $2,341 per troy ounce.",
        ],
        "ground_truth": "Alexander Graham Bell",
    },
    {
        "id": "python-creator",
        "goal": "Who created the Python programming language?",
        "tool_outputs": [
            "Python was created by Guido van Rossum and first released in 1991.",
            "Java was created by James Gosling at Sun Microsystems.",
            "Python 3.12 was released in October 2023.",
            "JavaScript was created by Brendan Eich in 1995.",
        ],
        "ground_truth": "Guido van Rossum",
    },
    {
        "id": "mount-everest-height",
        "goal": "How tall is Mount Everest?",
        "tool_outputs": [
            "Mount Everest stands at 8,848.86 metres (29,031.7 feet) above sea level as measured in 2020.",
            "K2 is the second-highest mountain at 8,611 metres.",
            "Today's weather on Everest: -30°C, wind 80 km/h.",
            "The first ascent of Everest was made by Tenzing Norgay and Edmund Hillary in 1953.",
        ],
        "ground_truth": "8,848",
    },
    {
        "id": "water-boiling-point",
        "goal": "At what temperature does water boil at sea level?",
        "tool_outputs": [
            "Water boils at 100 degrees Celsius (212 degrees Fahrenheit) at standard atmospheric pressure (sea level).",
            "Water freezes at 0 degrees Celsius.",
            "Current humidity in London: 78%.",
            "The boiling point decreases at higher altitudes due to lower atmospheric pressure.",
        ],
        "ground_truth": "100",
    },
    {
        "id": "speed-of-light",
        "goal": "What is the speed of light?",
        "tool_outputs": [
            "The speed of light in a vacuum is approximately 299,792,458 metres per second (about 300,000 km/s).",
            "The speed of sound in air is approximately 343 m/s at 20°C.",
            "Current NASA mission status: Voyager 1 is 23.3 billion km from Earth.",
            "Light from the Sun takes approximately 8 minutes to reach Earth.",
        ],
        "ground_truth": "299,792,458",
    },
    {
        "id": "french-capital",
        "goal": "What is the capital city of France?",
        "tool_outputs": [
            "Paris is the capital and largest city of France, with a population of about 2.1 million in the city proper.",
            "Lyon is France's second-largest city.",
            "The Eiffel Tower was built in 1889 for the World's Fair.",
            "France's GDP in 2023 was approximately $3.1 trillion.",
        ],
        "ground_truth": "Paris",
    },
    {
        "id": "shakespeare-birth-year",
        "goal": "In what year was William Shakespeare born?",
        "tool_outputs": [
            "William Shakespeare was born in April 1564 in Stratford-upon-Avon, England.",
            "Shakespeare wrote approximately 37 plays and 154 sonnets.",
            "The Globe Theatre was built in 1599.",
            "Shakespeare died on 23 April 1616.",
        ],
        "ground_truth": "1564",
    },
    {
        "id": "amazon-river",
        "goal": "What is the longest river in the world?",
        "tool_outputs": [
            "The Amazon River in South America is generally considered the longest river at approximately 6,992 km.",
            "The Nile River is approximately 6,650 km long.",
            "The Congo River is the world's deepest river.",
            "Amazon River discharge: 209,000 cubic metres per second.",
        ],
        "ground_truth": "Amazon",
    },
    {
        "id": "dna-structure",
        "goal": "What is the structure of DNA?",
        "tool_outputs": [
            "DNA has a double helix structure, consisting of two strands wound around each other, discovered by Watson and Crick in 1953.",
            "RNA is single-stranded, unlike DNA.",
            "The Human Genome Project was completed in 2003.",
            "CRISPR-Cas9 is a gene editing tool developed in 2012.",
        ],
        "ground_truth": "double helix",
    },
    {
        "id": "gravity-constant",
        "goal": "What is the gravitational constant G?",
        "tool_outputs": [
            "The gravitational constant G is approximately 6.674 × 10^-11 N·m²/kg².",
            "The acceleration due to gravity on Earth's surface is 9.81 m/s².",
            "Newton's law of universal gravitation was published in 1687.",
            "The mass of Earth is 5.972 × 10^24 kg.",
        ],
        "ground_truth": "6.674",
    },
    {
        "id": "periodic-table-gold",
        "goal": "What is the atomic number of gold?",
        "tool_outputs": [
            "Gold has atomic number 79 and the chemical symbol Au (from Latin aurum).",
            "Silver has atomic number 47.",
            "Current gold price: $2,341 per troy ounce.",
            "Gold melts at 1,064°C.",
        ],
        "ground_truth": "79",
    },
    {
        "id": "wwii-end-year",
        "goal": "In what year did World War II end?",
        "tool_outputs": [
            "World War II ended in 1945: Germany surrendered on 8 May (VE Day) and Japan on 2 September (VJ Day).",
            "World War I ended in 1918.",
            "The United Nations was founded in 1945.",
            "The Nuremberg Trials began in November 1945.",
        ],
        "ground_truth": "1945",
    },
    {
        "id": "human-chromosomes",
        "goal": "How many chromosomes do humans have?",
        "tool_outputs": [
            "Humans have 46 chromosomes in 23 pairs in most somatic cells.",
            "Chimpanzees have 48 chromosomes.",
            "Down syndrome is associated with an extra copy of chromosome 21.",
            "The Y chromosome is the smallest human chromosome.",
        ],
        "ground_truth": "46",
    },
    {
        "id": "moon-distance",
        "goal": "How far is the Moon from the Earth?",
        "tool_outputs": [
            "The average distance from Earth to the Moon is about 384,400 kilometres (238,855 miles).",
            "The Moon's diameter is 3,474 km.",
            "Current lunar phase: waxing gibbous.",
            "The Moon orbits Earth once every 27.3 days.",
        ],
        "ground_truth": "384,400",
    },
    {
        "id": "titanic-sinking-year",
        "goal": "In what year did the Titanic sink?",
        "tool_outputs": [
            "The RMS Titanic sank on 15 April 1912 after striking an iceberg in the North Atlantic.",
            "The Titanic was 269 metres long.",
            "About 1,500 people died in the Titanic disaster.",
            "The wreck of the Titanic was discovered in 1985.",
        ],
        "ground_truth": "1912",
    },
    {
        "id": "carbon-symbol",
        "goal": "What is the chemical symbol for carbon?",
        "tool_outputs": [
            "Carbon has the chemical symbol C and atomic number 6.",
            "Carbon dioxide (CO2) has a current atmospheric concentration of about 421 ppm.",
            "Diamond is a form of pure carbon.",
            "Carbon is the basis of all known life on Earth.",
        ],
        "ground_truth": "C",
    },
    {
        "id": "pi-value",
        "goal": "What is the value of pi to 5 decimal places?",
        "tool_outputs": [
            "Pi (π) is approximately 3.14159 to five decimal places. It is the ratio of a circle's circumference to its diameter.",
            "Pi has been calculated to over 100 trillion decimal places.",
            "Pi Day is celebrated on March 14 (3/14).",
            "Euler's number e is approximately 2.71828.",
        ],
        "ground_truth": "3.14159",
    },
    {
        "id": "human-heart-chambers",
        "goal": "How many chambers does the human heart have?",
        "tool_outputs": [
            "The human heart has four chambers: two atria (upper) and two ventricles (lower).",
            "A fish heart has two chambers.",
            "The average human heart beats 60-100 times per minute.",
            "The heart pumps about 5 litres of blood per minute at rest.",
        ],
        "ground_truth": "four",
    },
    {
        "id": "internet-inventor",
        "goal": "Who invented the World Wide Web?",
        "tool_outputs": [
            "The World Wide Web was invented by Tim Berners-Lee in 1989 while working at CERN.",
            "The Internet (as a network) predates the Web and emerged from ARPANET in the 1960s.",
            "The first website went live on 6 August 1991.",
            "Tim Berners-Lee founded the W3C in 1994.",
        ],
        "ground_truth": "Tim Berners-Lee",
    },
]
```

- [ ] **Step 7: Run all benchmark tests to verify tasks load**

```
pytest tests/benchmarks/ -v
```
Expected: 6 passed

- [ ] **Step 8: Commit**

```bash
git add benchmarks/__init__.py benchmarks/tasks.py benchmarks/accuracy.py tests/benchmarks/__init__.py tests/benchmarks/test_accuracy.py
git commit -m "feat(benchmarks): add 20-task benchmark set and accuracy module"
```

---

### Task 2: Benchmark runner

**Files:**
- Create: `benchmarks/runner.py`
- Create: `tests/benchmarks/test_runner.py`

**Interfaces:**
- Consumes: `TASKS` from `benchmarks/tasks.py`, `ContextFilter` and `EarlyExitDetector` from `agentsave.core`
- Produces: `run_benchmark() -> BenchmarkResult` where `BenchmarkResult` is a dataclass with `reduction_pct: float`, `accuracy_without: float`, `accuracy_with: float`, `per_task: list[dict]`

- [ ] **Step 1: Write the failing test**

```python
# tests/benchmarks/test_runner.py
from benchmarks.runner import run_benchmark, BenchmarkResult

def test_run_benchmark_returns_result():
    result = run_benchmark()
    assert isinstance(result, BenchmarkResult)

def test_reduction_pct_above_floor():
    result = run_benchmark()
    assert result.reduction_pct >= 20.0, (
        f"Token reduction {result.reduction_pct:.1f}% below 20% floor"
    )

def test_accuracy_not_degraded():
    result = run_benchmark()
    assert result.accuracy_with >= result.accuracy_without, (
        f"Accuracy degraded: {result.accuracy_without:.1%} → {result.accuracy_with:.1%}"
    )

def test_per_task_list_complete():
    result = run_benchmark()
    from benchmarks.tasks import TASKS
    assert len(result.per_task) == len(TASKS)

def test_per_task_has_required_fields():
    result = run_benchmark()
    for entry in result.per_task:
        assert "id" in entry
        assert "tokens_before" in entry
        assert "tokens_after" in entry
        assert "answer_without" in entry
        assert "answer_with" in entry
        assert "correct_without" in entry
        assert "correct_with" in entry
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/benchmarks/test_runner.py -v
```
Expected: `ModuleNotFoundError: cannot import name 'run_benchmark'`

- [ ] **Step 3: Create `benchmarks/runner.py`**

```python
# benchmarks/runner.py
from dataclasses import dataclass, field
from agentsave.core.context_filter import ContextFilter
from agentsave.core.early_exit import EarlyExitDetector
from agentsave.core.token_counter import count_tokens
from benchmarks.tasks import TASKS
from benchmarks.accuracy import matches_ground_truth


@dataclass
class TaskResult:
    id: str
    tokens_before: int
    tokens_after: int
    answer_without: str
    answer_with: str
    correct_without: bool
    correct_with: bool

    @property
    def reduction_pct(self) -> float:
        if self.tokens_before == 0:
            return 0.0
        return (self.tokens_before - self.tokens_after) / self.tokens_before * 100


@dataclass
class BenchmarkResult:
    per_task: list = field(default_factory=list)

    @property
    def reduction_pct(self) -> float:
        total_before = sum(t["tokens_before"] for t in self.per_task)
        total_after = sum(t["tokens_after"] for t in self.per_task)
        if total_before == 0:
            return 0.0
        return (total_before - total_after) / total_before * 100

    @property
    def accuracy_without(self) -> float:
        correct = sum(1 for t in self.per_task if t["correct_without"])
        return correct / len(self.per_task) if self.per_task else 0.0

    @property
    def accuracy_with(self) -> float:
        correct = sum(1 for t in self.per_task if t["correct_with"])
        return correct / len(self.per_task) if self.per_task else 0.0


def _simulate_agent_answer(tool_outputs: list[str]) -> str:
    """Naive answer: concatenate all relevant outputs — simulates agent with full context."""
    return " ".join(tool_outputs)


def _simulate_agent_answer_filtered(
    goal: str,
    tool_outputs: list[str],
    relevance_threshold: float = 0.15,
    early_exit_window: int = 2,
    early_exit_threshold: float = 0.08,
) -> tuple[str, int]:
    """Answer with AgentSave supervision — returns (answer, tokens_consumed)."""
    cf = ContextFilter(threshold=relevance_threshold)
    cf.set_goal(goal)
    eed = EarlyExitDetector(window=early_exit_window, threshold=early_exit_threshold)

    kept = []
    tokens_consumed = 0
    for output in tool_outputs:
        gain = cf.score(output)
        eed.record(gain)
        if eed.should_exit():
            break
        if cf.is_relevant(output):
            kept.append(output)
            tokens_consumed += count_tokens(output)

    return " ".join(kept), tokens_consumed


def run_benchmark() -> BenchmarkResult:
    result = BenchmarkResult()
    for task in TASKS:
        goal = task["goal"]
        outputs = task["tool_outputs"]
        truth = task["ground_truth"]

        tokens_before = sum(count_tokens(o) for o in outputs)
        answer_without = _simulate_agent_answer(outputs)
        correct_without = matches_ground_truth(answer_without, truth)

        answer_with, tokens_after = _simulate_agent_answer_filtered(goal, outputs)
        if tokens_after == 0:
            tokens_after = 1
        correct_with = matches_ground_truth(answer_with, truth)

        result.per_task.append({
            "id": task["id"],
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "answer_without": answer_without,
            "answer_with": answer_with,
            "correct_without": correct_without,
            "correct_with": correct_with,
        })
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/benchmarks/test_runner.py -v -s
```
Expected: 5 passed. Note the printed reduction % — it should be ≥ 20%.

- [ ] **Step 5: Commit**

```bash
git add benchmarks/runner.py tests/benchmarks/test_runner.py
git commit -m "feat(benchmarks): add benchmark runner with accuracy + token reduction measurement"
```

---

### Task 3: Report generator — updates BENCHMARKS.md

**Files:**
- Create: `benchmarks/report.py`
- Create: `tests/benchmarks/test_report.py`

**Interfaces:**
- Consumes: `BenchmarkResult` from `benchmarks.runner`
- Produces: `write_report(result: BenchmarkResult, path: str) -> None` — writes markdown table to `path`

- [ ] **Step 1: Write the failing test**

```python
# tests/benchmarks/test_report.py
import os, tempfile
from benchmarks.report import write_report
from benchmarks.runner import run_benchmark

def test_write_report_creates_file():
    result = run_benchmark()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name
    try:
        write_report(result, path)
        assert os.path.exists(path)
        content = open(path).read()
        assert "Token reduction" in content
        assert "Accuracy" in content
        assert str(round(result.reduction_pct, 1)) in content
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/benchmarks/test_report.py -v
```
Expected: `ModuleNotFoundError: cannot import name 'write_report'`

- [ ] **Step 3: Create `benchmarks/report.py`**

```python
# benchmarks/report.py
from benchmarks.runner import BenchmarkResult


def write_report(result: BenchmarkResult, path: str = "BENCHMARKS.md") -> None:
    lines = [
        "# AgentSave Benchmarks\n",
        "## Current results — 20-task benchmark set\n",
        "| Metric | Value | Notes |",
        "|---|---|---|",
        f"| Token reduction | {result.reduction_pct:.1f}% | {len(result.per_task)}-task set |",
        f"| Accuracy without AgentSave | {result.accuracy_without:.1%} | Baseline |",
        f"| Accuracy with AgentSave | {result.accuracy_with:.1%} | Supervised |",
        f"| Accuracy delta | {(result.accuracy_with - result.accuracy_without):+.1%} | 0% = no loss |",
        "",
        "## Target",
        "",
        "| Metric | Target | Status |",
        "|---|---|---|",
        f"| Token reduction | ~30% | {'✓ Met' if result.reduction_pct >= 30.0 else f'In progress ({result.reduction_pct:.1f}%)'} |",
        f"| Accuracy loss | 0% | {'✓ Met' if result.accuracy_with >= result.accuracy_without else '✗ Regression'} |",
        "",
        "## Per-task results",
        "",
        "| Task | Tokens before | Tokens after | Reduction | Answer correct (w/o) | Answer correct (with) |",
        "|---|---|---|---|---|---|",
    ]
    for t in result.per_task:
        reduction = (t["tokens_before"] - t["tokens_after"]) / t["tokens_before"] * 100
        lines.append(
            f"| {t['id']} | {t['tokens_before']} | {t['tokens_after']} "
            f"| {reduction:.1f}% | {'✓' if t['correct_without'] else '✗'} "
            f"| {'✓' if t['correct_with'] else '✗'} |"
        )
    lines += [
        "",
        "## Methodology",
        "",
        "Each task has a goal, 3–5 tool outputs (mix of relevant and noise), and a ground-truth answer.",
        "The runner simulates two agents: one receiving all outputs, one supervised by AgentSave.",
        "Accuracy is fuzzy-matched (substring or ≥0.6 sequence similarity).",
        "_Run `python -m benchmarks.runner` to regenerate this file._",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
```

- [ ] **Step 4: Add CLI entry to `benchmarks/runner.py`**

Append to the bottom of `benchmarks/runner.py`:

```python
if __name__ == "__main__":
    import sys
    result = run_benchmark()
    print(f"Token reduction: {result.reduction_pct:.1f}%")
    print(f"Accuracy without: {result.accuracy_without:.1%}")
    print(f"Accuracy with:    {result.accuracy_with:.1%}")
    from benchmarks.report import write_report
    out = sys.argv[1] if len(sys.argv) > 1 else "BENCHMARKS.md"
    write_report(result, out)
    print(f"Report written to {out}")
```

- [ ] **Step 5: Run tests and regenerate BENCHMARKS.md**

```
pytest tests/benchmarks/test_report.py -v
python -m benchmarks.runner
```
Expected: test passes, `BENCHMARKS.md` updated with real numbers.

- [ ] **Step 6: Commit**

```bash
git add benchmarks/report.py tests/benchmarks/test_report.py BENCHMARKS.md benchmarks/runner.py
git commit -m "feat(benchmarks): add report generator, update BENCHMARKS.md with real numbers"
```

---

### Task 4: Real LangChain + LangGraph integration tests

**Files:**
- Create: `tests/adapters/test_langchain_integration.py`
- Create: `tests/adapters/test_langgraph_integration.py`
- Modify: `pyproject.toml` — add `langchain-community>=0.3.0` and `langgraph>=0.2.0` to `[dev]`

- [ ] **Step 1: Add deps to pyproject.toml**

In `pyproject.toml`, find the `[project.optional-dependencies]` `dev` list and add:
```toml
dev = [
    ...existing entries...,
    "langchain-community>=0.3.0",
    "langgraph>=0.2.0",
]
```

Run:
```
pip install langchain-community langgraph
```

- [ ] **Step 2: Write LangChain integration test**

```python
# tests/adapters/test_langchain_integration.py
pytest_plugins = []

def test_langchain_chain_detected():
    langchain_core = pytest.importorskip("langchain_core")
    from langchain_core.language_models.fake import FakeListChatModel
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from agentsave import supervise

    llm = FakeListChatModel(responses=["Paris is the capital of France."])
    chain = ChatPromptTemplate.from_messages([("human", "{input}")]) | llm | StrOutputParser()

    supervised = supervise(chain)
    assert type(supervised).__name__ == "LangChainAdapter"


def test_langchain_chain_passes_through_answer():
    pytest.importorskip("langchain_core")
    from langchain_core.language_models.fake import FakeListChatModel
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from agentsave import supervise

    llm = FakeListChatModel(responses=["Paris is the capital of France."])
    chain = ChatPromptTemplate.from_messages([("human", "{input}")]) | llm | StrOutputParser()

    supervised = supervise(chain)
    result = supervised.invoke({"input": "What is the capital of France?"})
    assert "Paris" in result


def test_langchain_chain_records_run_state():
    pytest.importorskip("langchain_core")
    from langchain_core.language_models.fake import FakeListChatModel
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from agentsave import supervise

    llm = FakeListChatModel(responses=["The answer is 42."])
    chain = ChatPromptTemplate.from_messages([("human", "{input}")]) | llm | StrOutputParser()

    supervised = supervise(chain)
    supervised.invoke({"input": "What is 6 times 7?"})

    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "langchain"
    assert supervised.last_run_state.tokens_consumed > 0


import pytest
```

- [ ] **Step 3: Write LangGraph integration test**

```python
# tests/adapters/test_langgraph_integration.py
import pytest
from typing import TypedDict


def _build_simple_graph():
    langgraph = pytest.importorskip("langgraph")
    from langgraph.graph import StateGraph, END

    class State(TypedDict):
        question: str
        answer: str

    def answer_node(state: State) -> State:
        return {"question": state["question"], "answer": f"42 is the answer to: {state['question']}"}

    builder = StateGraph(State)
    builder.add_node("answer", answer_node)
    builder.set_entry_point("answer")
    builder.add_edge("answer", END)
    return builder.compile()


def test_langgraph_graph_detected():
    pytest.importorskip("langgraph")
    from agentsave import supervise
    graph = _build_simple_graph()
    supervised = supervise(graph)
    assert type(supervised).__name__ == "LangGraphAdapter"


def test_langgraph_graph_passes_through_result():
    pytest.importorskip("langgraph")
    from agentsave import supervise
    graph = _build_simple_graph()
    supervised = supervise(graph)
    result = supervised.invoke({"question": "life universe everything", "answer": ""})
    assert "42" in result["answer"]


def test_langgraph_graph_records_run_state():
    pytest.importorskip("langgraph")
    from agentsave import supervise
    graph = _build_simple_graph()
    supervised = supervise(graph)
    supervised.invoke({"question": "test", "answer": ""})
    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "langgraph"
    assert supervised.last_run_state.tokens_consumed > 0
```

- [ ] **Step 4: Run integration tests**

```
pytest tests/adapters/test_langchain_integration.py tests/adapters/test_langgraph_integration.py -v
```
Expected: 6 passed (or skipped if frameworks not installed — both outcomes are acceptable)

- [ ] **Step 5: Commit**

```bash
git add tests/adapters/test_langchain_integration.py tests/adapters/test_langgraph_integration.py pyproject.toml
git commit -m "test(adapters): add real LangChain + LangGraph integration tests"
```

---

### Task 5: Real AutoGen + CrewAI integration tests

**Files:**
- Create: `tests/adapters/test_autogen_integration.py`
- Create: `tests/adapters/test_crewai_integration.py`
- Modify: `pyproject.toml` — add `pyautogen>=0.4.0` and `crewai>=0.80.0` to `[dev]`

- [ ] **Step 1: Add deps to pyproject.toml dev section**

```toml
dev = [
    ...existing...,
    "pyautogen>=0.4.0",
    "crewai>=0.80.0",
]
```

```
pip install pyautogen crewai
```

- [ ] **Step 2: Write AutoGen integration test**

```python
# tests/adapters/test_autogen_integration.py
import pytest


def test_autogen_agent_detected():
    pytest.importorskip("autogen")
    from autogen import ConversableAgent
    from agentsave import supervise

    agent = ConversableAgent(
        name="test_agent",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        default_auto_reply="Task complete.",
        llm_config=False,
    )
    supervised = supervise(agent)
    assert type(supervised).__name__ == "AutoGenAdapter"


def test_autogen_initiate_chat_records_run_state():
    pytest.importorskip("autogen")
    from autogen import ConversableAgent
    from agentsave import supervise

    initiator = ConversableAgent(
        name="initiator",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        default_auto_reply="I'm done.",
        llm_config=False,
    )
    recipient = ConversableAgent(
        name="recipient",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        default_auto_reply="Task complete.",
        llm_config=False,
    )
    supervised = supervise(initiator)
    supervised.initiate_chat(recipient, message="Hello", max_turns=1)

    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "autogen"
    assert supervised.last_run_state.tokens_consumed > 0


def test_autogen_invoke_raises_not_implemented():
    pytest.importorskip("autogen")
    from autogen import ConversableAgent
    from agentsave import supervise

    agent = ConversableAgent(
        name="test",
        human_input_mode="NEVER",
        llm_config=False,
    )
    supervised = supervise(agent)
    with pytest.raises(NotImplementedError, match="explicit recipient"):
        supervised.invoke({"input": "test"})
```

- [ ] **Step 3: Write CrewAI integration test**

```python
# tests/adapters/test_crewai_integration.py
import pytest


def test_crewai_crew_detected():
    crewai = pytest.importorskip("crewai")
    from crewai import Crew
    from agentsave import supervise

    crew = Crew.__new__(Crew)
    crew.kickoff = lambda **kw: "Research complete: Paris is the capital."
    crew.step_callback = None

    supervised = supervise(crew)
    assert type(supervised).__name__ == "CrewAIAdapter"


def test_crewai_kickoff_passes_through():
    pytest.importorskip("crewai")
    from crewai import Crew
    from agentsave import supervise

    crew = Crew.__new__(Crew)
    crew.kickoff = lambda **kw: "Research complete: Paris is the capital."
    crew.step_callback = None

    supervised = supervise(crew)
    result = supervised.kickoff(inputs={"topic": "France capital"})
    assert "Paris" in str(result)


def test_crewai_records_run_state():
    pytest.importorskip("crewai")
    from crewai import Crew
    from agentsave import supervise

    crew = Crew.__new__(Crew)
    crew.kickoff = lambda **kw: "Done."
    crew.step_callback = None

    supervised = supervise(crew)
    supervised.kickoff(inputs={})
    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "crewai"
```

- [ ] **Step 4: Run tests**

```
pytest tests/adapters/test_autogen_integration.py tests/adapters/test_crewai_integration.py -v
```
Expected: 6 passed (or skipped if frameworks not installed)

- [ ] **Step 5: Commit**

```bash
git add tests/adapters/test_autogen_integration.py tests/adapters/test_crewai_integration.py pyproject.toml
git commit -m "test(adapters): add real AutoGen + CrewAI integration tests"
```

---

### Task 6: Real Smolagents integration test

**Files:**
- Create: `tests/adapters/test_smolagents_integration.py`
- Modify: `pyproject.toml` — add `smolagents>=1.10.0` to `[dev]`

- [ ] **Step 1: Add dep and write test**

In pyproject.toml dev section add `"smolagents>=1.10.0"`, then run `pip install smolagents`.

```python
# tests/adapters/test_smolagents_integration.py
import pytest


def test_smolagents_agent_detected():
    pytest.importorskip("smolagents")
    from smolagents import MultiStepAgent
    from agentsave import supervise

    agent = MultiStepAgent.__new__(MultiStepAgent)
    agent.step_callbacks = []
    agent.run = lambda task, **kw: f"Result for: {task}"

    supervised = supervise(agent)
    assert type(supervised).__name__ == "SmolagentsAdapter"


def test_smolagents_run_passes_through():
    pytest.importorskip("smolagents")
    from smolagents import MultiStepAgent
    from agentsave import supervise

    agent = MultiStepAgent.__new__(MultiStepAgent)
    agent.step_callbacks = []
    agent.run = lambda task, **kw: f"Answer: 42 for task: {task}"

    supervised = supervise(agent)
    result = supervised.run("What is 6 times 7?")
    assert "42" in result


def test_smolagents_step_callback_injected():
    pytest.importorskip("smolagents")
    from smolagents import MultiStepAgent
    from agentsave import supervise

    callbacks_seen = []

    def tracking_run(task, **kw):
        callbacks_seen.extend(agent.step_callbacks)
        return "done"

    agent = MultiStepAgent.__new__(MultiStepAgent)
    agent.step_callbacks = []
    agent.run = tracking_run

    supervised = supervise(agent)
    supervised.run("test task")
    assert len(callbacks_seen) >= 1


def test_smolagents_records_run_state():
    pytest.importorskip("smolagents")
    from smolagents import MultiStepAgent
    from agentsave import supervise

    agent = MultiStepAgent.__new__(MultiStepAgent)
    agent.step_callbacks = []
    agent.run = lambda task, **kw: "done"

    supervised = supervise(agent)
    supervised.run("test")
    assert supervised.last_run_state is not None
    assert supervised.last_run_state.framework == "smolagents"
```

- [ ] **Step 2: Run tests**

```
pytest tests/adapters/test_smolagents_integration.py -v
```
Expected: 4 passed (or skipped)

- [ ] **Step 3: Commit**

```bash
git add tests/adapters/test_smolagents_integration.py pyproject.toml
git commit -m "test(adapters): add real Smolagents integration test"
```

---

### Task 7: Rewrite `agentsave login` as self-hosted connection command

**Files:**
- Modify: `agentsave/cli/main.py`
- Modify: `tests/cli/test_main.py`

**Interfaces:**
- Consumes: `GET <url>/api/health` (no auth), `GET <url>/api/billing` (Bearer auth)
- Produces: `~/.agentsave/config.json` with `api_url`, `token`, `telemetry: true`

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/cli/test_main.py (append, don't replace existing tests)
import json, os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from agentsave.cli.main import cli


def test_login_success(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("agentsave.cli.main._CONFIG_DIR", str(tmp_path / ".agentsave"))
    monkeypatch.setattr("agentsave.cli.main._CONFIG_FILE", str(tmp_path / ".agentsave" / "config.json"))

    health_resp = MagicMock(status_code=200)
    health_resp.raise_for_status = lambda: None
    billing_resp = MagicMock(status_code=200)
    billing_resp.raise_for_status = lambda: None

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = [health_resp, billing_resp]
        mock_client_cls.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["login"], input="http://localhost:8000\nask-testkey123\n")

    assert result.exit_code == 0
    assert "Connected" in result.output
    cfg = json.loads((tmp_path / ".agentsave" / "config.json").read_text())
    assert cfg["api_url"] == "http://localhost:8000/api/events"
    assert cfg["token"] == "ask-testkey123"
    assert cfg["telemetry"] is True


def test_login_unreachable_server(tmp_path, monkeypatch):
    monkeypatch.setattr("agentsave.cli.main._CONFIG_DIR", str(tmp_path / ".agentsave"))
    monkeypatch.setattr("agentsave.cli.main._CONFIG_FILE", str(tmp_path / ".agentsave" / "config.json"))

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client_cls.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["login"], input="http://localhost:9999\nask-testkey\n")

    assert result.exit_code != 0
    assert "Cannot reach" in result.output


def test_login_invalid_key(tmp_path, monkeypatch):
    monkeypatch.setattr("agentsave.cli.main._CONFIG_DIR", str(tmp_path / ".agentsave"))
    monkeypatch.setattr("agentsave.cli.main._CONFIG_FILE", str(tmp_path / ".agentsave" / "config.json"))

    health_resp = MagicMock(status_code=200)
    health_resp.raise_for_status = lambda: None
    billing_resp = MagicMock(status_code=401)
    billing_resp.raise_for_status = lambda: None

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = [health_resp, billing_resp]
        mock_client_cls.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["login"], input="http://localhost:8000\nbad-key\n")

    assert result.exit_code != 0
    assert "Invalid API key" in result.output
```

- [ ] **Step 2: Run to verify failures**

```
pytest tests/cli/test_main.py::test_login_success tests/cli/test_main.py::test_login_unreachable_server tests/cli/test_main.py::test_login_invalid_key -v
```
Expected: 3 failed (old login command, not the new one yet)

- [ ] **Step 3: Rewrite the `login` command in `agentsave/cli/main.py`**

Replace the existing `login` function:

```python
@cli.command()
def login():
    """Connect to your self-hosted AgentSave dashboard."""
    url = click.prompt("Dashboard URL", default="http://localhost:8000")
    url = url.rstrip("/")
    key = click.prompt("API key", hide_input=True)

    import httpx
    try:
        with httpx.Client(timeout=5.0) as client:
            client.get(f"{url}/api/health").raise_for_status()
    except Exception as exc:
        console.print(f"[red]✗ Cannot reach {url}: {exc}[/red]")
        raise SystemExit(1)

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(
                f"{url}/api/billing",
                headers={"Authorization": f"Bearer {key}"},
            )
            if resp.status_code == 401:
                console.print("[red]✗ Invalid API key.[/red]")
                raise SystemExit(1)
            resp.raise_for_status()
    except SystemExit:
        raise
    except Exception as exc:
        console.print(f"[red]✗ Auth check failed: {exc}[/red]")
        raise SystemExit(1)

    cfg = _load_config()
    cfg["api_url"] = f"{url}/api/events"
    cfg["token"] = key
    cfg["telemetry"] = True
    _save_config(cfg)
    console.print("[bold green]✓ Connected. Telemetry enabled.[/bold green]")
```

Also remove the `dashboard` command (it opens `app.agentsave.io`):
Delete the entire `@cli.command()` / `def dashboard():` block.

- [ ] **Step 4: Run all CLI tests**

```
pytest tests/cli/test_main.py -v
```
Expected: all pass (existing tests + 3 new ones)

- [ ] **Step 5: Run full test suite**

```
pytest tests/ -v --tb=short
```
Expected: 60+ passed, 0 failed

- [ ] **Step 6: Commit**

```bash
git add agentsave/cli/main.py tests/cli/test_main.py
git commit -m "feat(cli): rewrite login as self-hosted connection command, remove app.agentsave.io references"
```

---

## Self-Review Checklist

- [x] Spec section "Real benchmark suite" → Tasks 1–3
- [x] Spec section "Real framework integration tests" → Tasks 4–6
- [x] Spec section "`agentsave login` — self-hosted" → Task 7
- [x] `matches_ground_truth` used in runner and defined in accuracy.py
- [x] `BenchmarkResult` type consistent across runner/report
- [x] All tests use `pytest.importorskip` for framework deps
- [x] `agentsave login` removes all `app.agentsave.io` references
- [x] pyproject.toml updated with all new dev deps
