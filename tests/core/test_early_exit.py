from agentsave.core.early_exit import EarlyExitDetector

def test_does_not_exit_before_window_fills():
    eed = EarlyExitDetector(window=3, threshold=0.05)
    eed.record(0.01)
    eed.record(0.01)
    assert eed.should_exit() is False

def test_exits_when_all_gains_below_threshold():
    eed = EarlyExitDetector(window=3, threshold=0.05)
    eed.record(0.01)
    eed.record(0.02)
    eed.record(0.01)
    assert eed.should_exit() is True

def test_does_not_exit_when_one_gain_above_threshold():
    eed = EarlyExitDetector(window=3, threshold=0.05)
    eed.record(0.01)
    eed.record(0.10)
    eed.record(0.01)
    assert eed.should_exit() is False

def test_window_slides():
    eed = EarlyExitDetector(window=3, threshold=0.05)
    eed.record(0.10)
    eed.record(0.01)
    eed.record(0.01)
    eed.record(0.01)
    assert eed.should_exit() is True

def test_reset_clears_state():
    eed = EarlyExitDetector(window=3, threshold=0.05)
    eed.record(0.01)
    eed.record(0.01)
    eed.record(0.01)
    assert eed.should_exit() is True
    eed.reset()
    assert eed.should_exit() is False
