from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """
    Abstract base class for all specialist agents.
    """

    @abstractmethod
    def get_tool_def(self) -> Dict[str, Any]:
        """
        Returns the Open WebUI tool definition for this agent.
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes the agent's task.
        """
        pass
