import importlib
import inspect
import pkgutil
from typing import Any, Dict, List

from flock_gitlab.agents.base import BaseAgent

# A list of agents that require human approval before execution
CRITICAL_AGENTS = [
    "gitlab_create_issue",
    "gitlab_create_merge_request",
    "gitlab_create_commit",
]

class AgentOrchestrator:
    """
    Discovers, loads, and manages specialist agents.
    """

    def __init__(self, agents_package="flock_gitlab.agents"):
        self.agents_package = agents_package
        self.agents: Dict[str, BaseAgent] = {}
        self._discover_agents()

    def _discover_agents(self):
        """
        Dynamically discovers and loads agents from the specified package.
        """
        package = importlib.import_module(self.agents_package)
        for _, name, _ in pkgutil.iter_modules(package.__path__):
            if name == "base" or name == "orchestrator":
                continue
            
            module = importlib.import_module(f".{name}", package=self.agents_package)
            for _, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    instance = obj()
                    tool_name = instance.get_tool_def().get("function", {}).get("name")
                    if tool_name:
                        self.agents[tool_name] = instance

    def get_all_tool_defs(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all discovered agent tool definitions.
        """
        return [agent.get_tool_def() for agent in self.agents.values()]

    async def dispatch(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Dispatches a task to the appropriate agent.
        """
        if tool_name not in self.agents:
            raise ValueError(f"Agent '{tool_name}' not found.")
        
        # Human-in-the-loop approval for critical tasks
        if tool_name in CRITICAL_AGENTS:
            # In a real scenario, this would involve a callback, a UI prompt, etc.
            # For this simulation, we'll return a message requiring confirmation.
            return {
                "requires_approval": True,
                "tool_name": tool_name,
                "params": kwargs,
                "message": f"This is a critical operation. Please confirm you want to execute '{tool_name}'."
            }

        agent = self.agents[tool_name]
        return await agent.execute(**kwargs)

orchestrator = AgentOrchestrator()
