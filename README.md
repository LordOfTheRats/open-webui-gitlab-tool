# Flock GitLab Tool

A reimagined GitLab tool for Open WebUI, built with `flock-core` and specialized agents.

## Overview

This project provides a powerful and flexible way to interact with GitLab from Open WebUI. It uses a dynamic orchestration of specialist agents for various operations, including:

- Project planning (issues and merge requests)
- Issue and merge request summarization
- Code review
- Pipeline triage
- Code repository operations

## Features

- **Modular Architecture**: Based on `flock-core` for easy extension and maintenance.
- **FastAPI Server**: Implements the Open WebUI tool server specification.
- **Human-in-the-Loop**: Requires human approval for critical operations.
- **Self-Hosted Focus**: Designed for self-hosted GitLab Community Edition and Ollama instances.

## Getting Started

1.  **Install dependencies:**
    ```bash
    poetry install
    ```

2.  **Run the server:**
    ```bash
    poetry run uvicorn flock_gitlab.server.main:app --reload
    ```
