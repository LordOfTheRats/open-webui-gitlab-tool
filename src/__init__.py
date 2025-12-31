"""
GitLab Flock Tool - Version 2.0.0

A sophisticated multi-agent system for GitLab automation using the Flock blackboard pattern.

Author: René Vögeli
License: MIT
Repository: https://github.com/LordOfTheRats/open-webui-gitlab-tool

System Overview:
---------------
This package implements a complete reimagination of GitLab automation, moving from
a monolithic design to an intelligent multi-agent system with coordinated problem-solving.

Architecture:
------------
- FastAPI REST API server
- Flock blackboard for agent coordination
- Specialized AI agents for different operations
- Human approval workflow for critical operations
- Async task execution with status tracking

Agents:
-------
1. Project Planner - Overall project analysis and planning
2. Issue Summarizer - Issue analysis and summarization
3. MR Analyzer - Merge request analysis
4. Code Reviewer - AI-powered code review
5. Pipeline Reviewer - CI/CD pipeline analysis
6. Repository Browser - Repository content browsing

Quick Start:
-----------
1. Install: pip install -e .
2. Configure: cp .env.example .env (edit with your settings)
3. Run: uvicorn src.main:app --reload
4. Test: curl http://localhost:8000/health

Documentation:
-------------
- QUICKSTART.md - 5-minute setup guide
- USAGE.md - Complete API documentation
- ARCHITECTURE.md - System design details
- MIGRATION.md - Upgrade from V1

Integration:
-----------
Open WebUI: Add as function tool using http://localhost:8000
Docker: docker-compose up -d

Example Usage:
-------------
# Analyze a project
curl -X POST http://localhost:8000/api/analyze-project \\
  -H "Content-Type: application/json" \\
  -d '{"project": "group/project-name"}'

# Review code
curl -X POST http://localhost:8000/api/review-code \\
  -H "Content-Type: application/json" \\
  -d '{"project": "group/project", "file_path": "src/main.py", "ref": "main"}'

For more information, see the documentation files in the repository.
"""

__version__ = "2.0.0"
__author__ = "René Vögeli"
__license__ = "MIT"

# Package exports
from .config import settings
from .main import app

__all__ = ["app", "settings", "__version__"]
