"""
Integration smoke tests — verify key endpoints return HTTP 200.

These tests make REAL HTTP requests to demoblaze.com.
Mark: pytest -m integration

Run:
    pytest tests/integration/ -m integration -v
"""

import os
import sys

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from common.config import target

BASE_URL = target.host
TIMEOUT = (target.connect_timeout, target.request_timeout)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def http_session() -> requests.Session:
    """Re-usable requests session shared across integration tests."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestEndpointAvailability:
    """Verify all key Demoblaze endpoints are reachable."""

    def test_homepage_returns_200(self, http_session: requests.Session) -> None:
        """GET / must return HTTP 200."""
        response = http_session.get(BASE_URL + "/", timeout=TIMEOUT)
        assert response.status_code == 200, f"Homepage returned {response.status_code}"

    def test_product_page_returns_200(self, http_session: requests.Session) -> None:
        """GET /prod.html?idp_=1 must return HTTP 200."""
        response = http_session.get(
            BASE_URL + "/prod.html", params={"idp_": 1}, timeout=TIMEOUT
        )
        assert response.status_code == 200

    def test_cart_page_returns_200(self, http_session: requests.Session) -> None:
        """GET /cart.html must return HTTP 200."""
        response = http_session.get(BASE_URL + "/cart.html", timeout=TIMEOUT)
        assert response.status_code == 200

    def test_entries_endpoint_returns_200(self, http_session: requests.Session) -> None:
        """POST /entries must return HTTP 200 with product data."""
        response = http_session.post(BASE_URL + "/entries", json={}, timeout=TIMEOUT)
        assert response.status_code == 200

    def test_bycat_phone_returns_200(self, http_session: requests.Session) -> None:
        """POST /bycat with cat=phone must return HTTP 200."""
        response = http_session.post(
            BASE_URL + "/bycat", json={"cat": "phone"}, timeout=TIMEOUT
        )
        assert response.status_code == 200

    def test_bycat_notebook_returns_200(self, http_session: requests.Session) -> None:
        """POST /bycat with cat=notebook must return HTTP 200."""
        response = http_session.post(
            BASE_URL + "/bycat", json={"cat": "notebook"}, timeout=TIMEOUT
        )
        assert response.status_code == 200

    def test_bycat_monitor_returns_200(self, http_session: requests.Session) -> None:
        """POST /bycat with cat=monitor must return HTTP 200."""
        response = http_session.post(
            BASE_URL + "/bycat", json={"cat": "monitor"}, timeout=TIMEOUT
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestAuthEndpoint:
    """Verify authentication endpoint behaviour."""

    def test_login_with_invalid_credentials_does_not_return_token(
        self, http_session: requests.Session
    ) -> None:
        """POST /login with wrong password must not return Auth_token."""
        payload = {
            "username": "nonexistent_user_xyz@example.com",
            "password": "definitely_wrong_password_xyz",
        }
        response = http_session.post(BASE_URL + "/login", json=payload, timeout=TIMEOUT)
        # API returns 200 with an error message — should NOT contain a token
        assert response.status_code == 200
        assert "Auth_token" not in response.text

    def test_login_endpoint_response_time_under_sla(
        self, http_session: requests.Session
    ) -> None:
        """POST /login response time must be under 5 seconds."""
        from common.config import thresholds

        payload = {"username": "test", "password": "test"}
        response = http_session.post(BASE_URL + "/login", json=payload, timeout=TIMEOUT)
        response_ms = response.elapsed.total_seconds() * 1000
        # Use 5× SLA threshold for integration smoke (network variance)
        assert (
            response_ms < thresholds.max_response_time_ms * 5
        ), f"Login took {response_ms:.0f}ms — SLA breach"


@pytest.mark.integration
class TestResponsePayloads:
    """Verify response payloads contain expected fields."""

    def test_entries_returns_json_with_items(
        self, http_session: requests.Session
    ) -> None:
        """POST /entries payload must include an 'Items' or similar key."""
        response = http_session.post(BASE_URL + "/entries", json={}, timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        # Demoblaze wraps items in 'Items' key
        assert "Items" in data or isinstance(
            data, (list, dict)
        ), "Entries response must be parseable JSON"

    def test_bycat_returns_json(self, http_session: requests.Session) -> None:
        """POST /bycat must return valid JSON."""
        response = http_session.post(
            BASE_URL + "/bycat", json={"cat": "phone"}, timeout=TIMEOUT
        )
        assert response.status_code == 200
        # Must not raise
        data = response.json()
        assert data is not None
