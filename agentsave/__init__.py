def supervise(agent, **kwargs):
    from agentsave.adapters.base import supervise as _supervise
    return _supervise(agent, **kwargs)

def loop(*args, **kwargs):
    from agentsave.core.supervisor import loop as _loop
    return _loop(*args, **kwargs)

__all__ = ["supervise", "loop"]
__version__ = "0.1.0"
