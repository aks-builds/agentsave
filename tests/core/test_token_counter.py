from agentsave.core.token_counter import count_tokens

def test_empty_string():
    assert count_tokens("") == 0

def test_single_word():
    result = count_tokens("hello")
    assert result > 0
    assert isinstance(result, int)

def test_longer_text_more_tokens():
    short = count_tokens("hello")
    long = count_tokens("hello world this is a longer sentence with many more words")
    assert long > short

def test_non_string_returns_zero():
    assert count_tokens(None) == 0
    assert count_tokens(42) == 0
