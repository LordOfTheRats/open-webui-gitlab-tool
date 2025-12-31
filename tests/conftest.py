"""Pytest configuration."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Set async backend for tests."""
    return "asyncio"
