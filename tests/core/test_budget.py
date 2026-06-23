from agentsave.core.budget import BudgetGate

def test_starts_empty():
    bg = BudgetGate(budget=1000)
    assert bg.consumed == 0
    assert bg.remaining == 1000
    assert bg.is_exhausted() is False

def test_consume_reduces_remaining():
    bg = BudgetGate(budget=1000)
    bg.consume(300)
    assert bg.consumed == 300
    assert bg.remaining == 700

def test_exhausted_when_at_limit():
    bg = BudgetGate(budget=1000)
    bg.consume(1000)
    assert bg.is_exhausted() is True

def test_exhausted_when_over_limit():
    bg = BudgetGate(budget=1000)
    bg.consume(1200)
    assert bg.is_exhausted() is True
    assert bg.remaining == 0

def test_would_exceed():
    bg = BudgetGate(budget=1000)
    bg.consume(800)
    assert bg.would_exceed(100) is False
    assert bg.would_exceed(201) is True
