"""Tests for GitLab client."""

import pytest
from httpx import AsyncClient, Response

from src.gitlab_client import GitLabClient


@pytest.fixture
def gitlab_client() -> GitLabClient:
    """Create GitLab client for testing."""
    return GitLabClient(base_url="https://gitlab.test", token="test-token")


@pytest.mark.asyncio
async def test_encode_project_path(gitlab_client: GitLabClient) -> None:
    """Test project path encoding."""
    assert gitlab_client._encode_project_path(123) == "123"
    assert gitlab_client._encode_project_path("group/project") == "group%2Fproject"


@pytest.mark.asyncio
async def test_get_project(gitlab_client: GitLabClient, httpx_mock: Any) -> None:
    """Test getting project information."""
    httpx_mock.add_response(
        json={
            "id": 1,
            "name": "Test Project",
            "path_with_namespace": "group/test-project",
            "description": "A test project",
            "default_branch": "main",
            "visibility": "private",
            "web_url": "https://gitlab.test/group/test-project",
        }
    )
    
    project = await gitlab_client.get_project("group/test-project")
    
    assert project.id == 1
    assert project.name == "Test Project"
    assert project.visibility == "private"
