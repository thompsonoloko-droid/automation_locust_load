"""
Unit tests — common/auth.py (AuthManager)

Tests authentication flow logic with mocked HTTP responses,
without making real network requests.
"""

import json
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Helpers to build mock context-manager responses
# ---------------------------------------------------------------------------


def _make_response(status_code: int, text: str) -> MagicMock:
    """Build a mock response that acts as a context manager."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.__enter__ = lambda s: resp
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAuthManagerLogin:
    """Tests for AuthManager.login()."""

    def test_successful_login_sets_token(self, mock_http_user: MagicMock) -> None:
        """login() must extract and store the Auth_token on HTTP 200."""
        from common.auth import AuthManager

        token_value = "abc123token"
        mock_resp = _make_response(200, json.dumps({"Auth_token": token_value}))
        mock_http_user.client.post.return_value = mock_resp

        manager = AuthManager(mock_http_user, "user@test.com", "Password123#")
        result = manager.login()

        assert result is True
        assert manager.token == token_value
        assert manager.is_authenticated is True

    def test_successful_login_extracts_session_cookie(
        self, mock_http_user: MagicMock
    ) -> None:
        """login() must extract the 'user' cookie from the client cookies."""
        from common.auth import AuthManager

        mock_resp = _make_response(200, json.dumps({"Auth_token": "tok"}))
        mock_http_user.client.post.return_value = mock_resp
        mock_http_user.client.cookies.get_dict.return_value = {
            "user": "session-cookie-val"
        }

        manager = AuthManager(mock_http_user, "user@test.com", "Password123#")
        manager.login()

        assert manager.session_cookie == "session-cookie-val"

    def test_failed_login_returns_false(self, mock_http_user: MagicMock) -> None:
        """login() must return False on non-200 response."""
        from common.auth import AuthManager

        mock_resp = _make_response(401, "Unauthorized")
        mock_http_user.client.post.return_value = mock_resp

        manager = AuthManager(mock_http_user, "user@test.com", "wrong_pass")
        result = manager.login()

        assert result is False
        assert manager.is_authenticated is False
        assert manager.token is None

    def test_wrong_password_response_returns_false(
        self, mock_http_user: MagicMock
    ) -> None:
        """login() returns False when response body signals wrong password."""
        from common.auth import AuthManager

        mock_resp = _make_response(200, "Wrong password.")
        mock_http_user.client.post.return_value = mock_resp

        manager = AuthManager(mock_http_user, "user@test.com", "wrong")
        result = manager.login()

        assert result is False

    def test_network_exception_returns_false(self, mock_http_user: MagicMock) -> None:
        """login() must return False (not raise) on a connection error."""
        from common.auth import AuthManager

        mock_http_user.client.post.side_effect = ConnectionError("Network unavailable")

        manager = AuthManager(mock_http_user, "user@test.com", "Password123#")
        result = manager.login()

        assert result is False
        assert manager.is_authenticated is False


class TestAuthManagerLogout:
    """Tests for AuthManager.logout()."""

    def test_logout_clears_state(self, mock_http_user: MagicMock) -> None:
        """logout() must reset all authentication state."""
        from common.auth import AuthManager

        mock_resp = _make_response(200, json.dumps({"Auth_token": "tok"}))
        mock_http_user.client.post.return_value = mock_resp

        manager = AuthManager(mock_http_user, "user@test.com", "Password123#")
        manager.login()

        # Confirm authenticated state
        assert manager.is_authenticated is True

        # Now logout
        manager.logout()

        assert manager.token is None
        assert manager.session_cookie is None
        assert manager.is_authenticated is False


class TestAuthManagerCookieExtraction:
    """Tests for cookie extraction edge cases."""

    def test_missing_user_cookie_does_not_raise(
        self, mock_http_user: MagicMock
    ) -> None:
        """AuthManager must not raise if 'user' cookie is absent."""
        from common.auth import AuthManager

        mock_resp = _make_response(200, json.dumps({"Auth_token": "tok"}))
        mock_http_user.client.post.return_value = mock_resp
        mock_http_user.client.cookies.get_dict.return_value = {}  # no cookie

        manager = AuthManager(mock_http_user, "user@test.com", "Password123#")
        # Should not raise
        manager.login()
        assert manager.session_cookie is None

    def test_repr_unauthenticated(self, mock_http_user: MagicMock) -> None:
        """__repr__ must return a descriptive string before login."""
        from common.auth import AuthManager

        manager = AuthManager(mock_http_user, "user@test.com", "Password123#")
        result = repr(manager)
        assert "user@test.com" in result
        assert "False" in result

    def test_repr_authenticated(self, mock_http_user: MagicMock) -> None:
        """__repr__ must reflect authenticated=True after login."""
        from common.auth import AuthManager

        mock_resp = _make_response(200, json.dumps({"Auth_token": "tok"}))
        mock_http_user.client.post.return_value = mock_resp

        manager = AuthManager(mock_http_user, "user@test.com", "Password123#")
        manager.login()
        result = repr(manager)
        assert "True" in result
