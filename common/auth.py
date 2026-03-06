"""
Authentication helpers for the Locust performance test framework.

Provides a reusable :class:`AuthManager` that handles login, token extraction,
and session-cookie management for Demoblaze-style authentication flows.

Architecture:
    1. Login POSTs to api.demoblaze.com/login with username/password
    2. Server returns Auth_token in JSON response body
    3. Browser automatically receives 'user' cookie (HTTP-Only, implicit)
    4. Subsequent requests (cart, checkout) use the 'user' cookie

Example:
    >>> from common.auth import AuthManager
    >>> auth = AuthManager(user, username="test@example.com", password="Secret1!")
    >>> auth.login()  # True if successful
    >>> auth.session_cookie  # 'user' cookie value for subsequent requests
    >>> auth.logout()  # Clears all auth state
"""

import json
import logging

from locust import HttpUser

from common.config import target as _target_cfg

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages authentication state for a single Locust virtual user.

    Usage inside a :class:`locust.HttpUser` subclass::

        def on_start(self) -> None:
            self.auth = AuthManager(self, username="user@test.com", password="Secret1!")
            self.auth.login()

        def authenticated_action(self) -> None:
            payload = {"cookie": self.auth.session_cookie, ...}
    """

    def __init__(self, user: HttpUser, username: str, password: str) -> None:
        self._user = user
        self._username = username
        self._password = password
        self.token: str | None = None
        self.session_cookie: str | None = None
        self.is_authenticated: bool = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def login(self) -> bool:
        """
        Perform a POST /login request and extract the auth token.

        Returns:
            ``True`` when authentication succeeds, ``False`` otherwise.
        """
        payload = {"username": self._username, "password": self._password}
        # Use the API host (api.demoblaze.com) for the login endpoint,
        # not the SPA host (demoblaze.com) which does not serve the REST API.
        login_url = f"{_target_cfg.api_host}/login"
        try:
            with self._user.client.post(
                login_url, json=payload, catch_response=True, name="/login [auth]"
            ) as response:
                if response.status_code == 200 and "Auth_token" in response.text:
                    data: dict = json.loads(response.text)
                    self.token = data.get("Auth_token")
                    self.is_authenticated = True
                    self._extract_session_cookie()
                    response.success()
                    logger.debug("AuthManager: login successful for %s", self._username)
                    return True
                else:
                    reason = f"Login failed — status={response.status_code}, body={response.text[:120]}"
                    response.failure(reason)
                    logger.warning("AuthManager: %s", reason)
                    return False
        except Exception as exc:  # noqa: BLE001
            logger.error("AuthManager: login request raised %s", exc)
            return False

    def logout(self) -> None:
        """Clear local authentication state."""
        self.token = None
        self.session_cookie = None
        self.is_authenticated = False
        logger.debug("AuthManager: session cleared for %s", self._username)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_session_cookie(self) -> None:
        """Read the ``user`` cookie set by Demoblaze after a successful login."""
        cookies = self._user.client.cookies.get_dict()
        self.session_cookie = cookies.get("user")
        if not self.session_cookie:
            logger.warning("AuthManager: 'user' session cookie not found after login.")

    # ------------------------------------------------------------------
    # Descriptor protocol helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"AuthManager(username={self._username!r}, "
            f"authenticated={self.is_authenticated})"
        )
