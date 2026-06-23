import pytest
from unittest.mock import MagicMock
from agentsave.adapters.base import supervise, BaseAdapter

def test_supervise_raises_on_unknown_type():
    with pytest.raises(TypeError, match="Unsupported agent type"):
        supervise(object())

def test_supervise_raises_on_none():
    with pytest.raises(TypeError):
        supervise(None)

def test_base_adapter_is_abstract():
    with pytest.raises(TypeError):
        BaseAdapter(agent=MagicMock())
