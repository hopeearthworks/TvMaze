"""Shared pytest fixtures."""

import pytest

from tvmaze import api_client


@pytest.fixture(autouse=True)
def empty_api_cache():
    """Make sure cached API responses never leak between tests."""
    api_client.clear_cache()
    yield
    api_client.clear_cache()
