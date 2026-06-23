from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    def __init__(
        self,
        agent: Any,
        budget: int = 100_000,
        relevance_threshold: float = 0.3,
        early_exit_window: int = 3,
        early_exit_threshold: float = 0.05,
        model_name: str = "unknown",
    ):
        self._agent = agent
        self._budget = budget
        self._relevance_threshold = relevance_threshold
        self._early_exit_window = early_exit_window
        self._early_exit_threshold = early_exit_threshold
        self._model_name = model_name

    @abstractmethod
    def invoke(self, input: Any, **kwargs: Any) -> Any:
        pass


def supervise(agent: Any, **kwargs: Any) -> Any:
    if agent is None:
        raise TypeError("Unsupported agent type: NoneType")

    agent_type = type(agent).__name__
    module = type(agent).__module__

    if "langchain" in module and "AgentExecutor" in agent_type:
        from agentsave.adapters.langchain import LangChainAdapter
        return LangChainAdapter(agent=agent, **kwargs)

    if "langchain" in module and ("Runnable" in agent_type or "Chain" in agent_type):
        from agentsave.adapters.langchain import LangChainAdapter
        return LangChainAdapter(agent=agent, **kwargs)

    if "langgraph" in module or "CompiledStateGraph" in agent_type:
        from agentsave.adapters.langgraph import LangGraphAdapter
        return LangGraphAdapter(agent=agent, **kwargs)

    if "autogen" in module and "Agent" in agent_type:
        from agentsave.adapters.autogen import AutoGenAdapter
        return AutoGenAdapter(agent=agent, **kwargs)

    if "crewai" in module and "Crew" in agent_type:
        from agentsave.adapters.crewai import CrewAIAdapter
        return CrewAIAdapter(agent=agent, **kwargs)

    if "smolagents" in module and "Agent" in agent_type:
        from agentsave.adapters.smolagents import SmolagentsAdapter
        return SmolagentsAdapter(agent=agent, **kwargs)

    raise TypeError(
        f"Unsupported agent type: {type(agent)}. "
        "Supported: LangChain AgentExecutor, LangGraph StateGraph, "
        "AutoGen ConversableAgent, CrewAI Crew, Smolagents MultiStepAgent. "
        "For raw loops use: `with agentsave.loop(budget=N) as run:`"
    )
