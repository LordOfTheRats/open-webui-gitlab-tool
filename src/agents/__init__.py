"""Agent registry and initialization."""

from typing import Any

from ..blackboard import GitLabBlackboard
from ..gitlab_client import GitLabClient
from ..models import AgentRole
from ..ollama_client import OllamaClient
from .base import BaseAgent
from .code_reviewer import CodeReviewerAgent
from .issue_summarizer import IssueSummarizerAgent
from .mr_analyzer import MRAnalyzerAgent
from .pipeline_reviewer import PipelineReviewerAgent
from .project_planner import ProjectPlannerAgent
from .repo_browser import RepoBrowserAgent

__all__ = [
    "BaseAgent",
    "CodeReviewerAgent",
    "IssueSummarizerAgent",
    "MRAnalyzerAgent",
    "PipelineReviewerAgent",
    "ProjectPlannerAgent",
    "RepoBrowserAgent",
    "create_agents",
]


def create_agents(
    blackboard: GitLabBlackboard,
    gitlab_client: GitLabClient,
    ollama_client: OllamaClient,
) -> dict[AgentRole, BaseAgent]:
    """Create all specialist agents."""
    agents: dict[AgentRole, BaseAgent] = {}
    
    agent_classes: list[type[BaseAgent]] = [
        ProjectPlannerAgent,
        IssueSummarizerAgent,
        MRAnalyzerAgent,
        CodeReviewerAgent,
        PipelineReviewerAgent,
        RepoBrowserAgent,
    ]
    
    for agent_class in agent_classes:
        agent = agent_class(
            blackboard=blackboard,
            gitlab_client=gitlab_client,
            ollama_client=ollama_client,
        )
        agents[agent.role] = agent
    
    return agents
