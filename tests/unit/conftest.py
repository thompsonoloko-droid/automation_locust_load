"""
pytest fixtures for the automation_locust_load unit tests.

Provides:
- Mock Locust environment for unit testing user classes / task sets
- Pre-built AuthManager instances with stubbed HTTP clients
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

# Make the project root importable from tests/unit/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# Mock HTTP client fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_http_client() -> MagicMock:
    """Return a MagicMock that mimics the Locust HttpSession interface."""
    client = MagicMock()

    # Default: POST /login returns a successful auth response
    login_response = MagicMock()
    login_response.status_code = 200
    login_response.text = '{"Auth_token": "mock-token-abc123"}'
    login_response.__enter__ = lambda s: login_response
    login_response.__exit__ = MagicMock(return_value=False)

    # Default: cookies contain a 'user' cookie
    client.cookies.get_dict.return_value = {"user": "mock-session-cookie-xyz"}
    client.post.return_value.__enter__ = lambda s: login_response
    client.post.return_value.__exit__ = MagicMock(return_value=False)

    return client


@pytest.fixture()
def mock_http_user(mock_http_client: MagicMock) -> MagicMock:
    """Return a MagicMock representing a Locust HttpUser with a mock client."""
    user = MagicMock()
    user.client = mock_http_client
    return user


@pytest.fixture()
def mock_locust_environment() -> MagicMock:
    """Minimal mock of locust.env.Environment for event-hook testing."""
    env = MagicMock()
    env.host = "https://demoblaze.com"
    env.process_exit_code = 0
    env.stats.total.num_requests = 1000
    env.stats.total.num_failures = 0
    env.stats.total.avg_response_time = 250.0
    env.stats.total.fail_ratio = 0.0
    env.stats.total.get_response_time_percentile.return_value = 500.0
    return env
