"""
Unit tests — common/config.py

Ensures configuration dataclasses load correct defaults and respect
environment variable overrides.
"""

import os
import pytest


class TestTargetConfig:
    """Tests for TargetConfig dataclass."""

    def test_default_host(self) -> None:
        """Default host must point to Demoblaze when env var is absent."""
        # Remove env var if set
        os.environ.pop("TARGET_HOST", None)
        # Re-import to pick up env state (frozen dataclass uses factory)
        from common.config import TargetConfig
        cfg = TargetConfig()
        assert cfg.host == "https://demoblaze.com"

    def test_host_override_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TARGET_HOST env var must override the default."""
        monkeypatch.setenv("TARGET_HOST", "https://staging.example.com")
        from common.config import TargetConfig
        cfg = TargetConfig()
        assert cfg.host == "https://staging.example.com"

    def test_default_timeouts(self) -> None:
        """Default timeout values must be sensible integers."""
        from common.config import TargetConfig
        cfg = TargetConfig()
        assert isinstance(cfg.request_timeout, int)
        assert cfg.request_timeout > 0
        assert isinstance(cfg.connect_timeout, int)
        assert cfg.connect_timeout > 0

    def test_is_frozen(self) -> None:
        """TargetConfig must be immutable (frozen dataclass)."""
        from common.config import TargetConfig
        cfg = TargetConfig()
        with pytest.raises((AttributeError, TypeError)):
            cfg.host = "https://mutated.com"  # type: ignore[misc]


class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def test_is_configured_returns_false_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """is_configured() must return False when credentials are missing."""
        monkeypatch.delenv("TEST_USERNAME", raising=False)
        monkeypatch.delenv("TEST_PASSWORD", raising=False)
        from common.config import AuthConfig
        cfg = AuthConfig()
        assert cfg.is_configured() is False

    def test_is_configured_returns_true_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """is_configured() must return True when both credentials are provided."""
        monkeypatch.setenv("TEST_USERNAME", "user@test.com")
        monkeypatch.setenv("TEST_PASSWORD", "Secret1!")
        from common.config import AuthConfig
        cfg = AuthConfig()
        assert cfg.is_configured() is True

    def test_empty_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default credentials must be empty strings (not None)."""
        monkeypatch.delenv("TEST_USERNAME", raising=False)
        monkeypatch.delenv("TEST_PASSWORD", raising=False)
        from common.config import AuthConfig
        cfg = AuthConfig()
        assert cfg.username == ""
        assert cfg.password == ""


class TestLoadConfig:
    """Tests for LoadConfig dataclass."""

    def test_default_users(self) -> None:
        """Default user count must be a positive integer."""
        from common.config import LoadConfig
        cfg = LoadConfig()
        assert isinstance(cfg.users, int)
        assert cfg.users > 0

    def test_default_spawn_rate(self) -> None:
        """Default spawn rate must be a positive integer."""
        from common.config import LoadConfig
        cfg = LoadConfig()
        assert isinstance(cfg.spawn_rate, int)
        assert cfg.spawn_rate > 0

    def test_user_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LOCUST_USERS override must be respected."""
        monkeypatch.setenv("LOCUST_USERS", "200")
        from common.config import LoadConfig
        cfg = LoadConfig()
        assert cfg.users == 200


class TestThresholdConfig:
    """Tests for ThresholdConfig dataclass."""

    def test_default_response_time_positive(self) -> None:
        """Max response time threshold must be positive."""
        from common.config import ThresholdConfig
        cfg = ThresholdConfig()
        assert cfg.max_response_time_ms > 0

    def test_default_failure_rate_in_range(self) -> None:
        """Failure rate threshold must be between 0 and 100 percent."""
        from common.config import ThresholdConfig
        cfg = ThresholdConfig()
        assert 0 <= cfg.max_failure_rate_pct <= 100

    def test_default_min_rps_positive(self) -> None:
        """Minimum RPS threshold must be positive."""
        from common.config import ThresholdConfig
        cfg = ThresholdConfig()
        assert cfg.min_rps > 0


class TestProductConfig:
    """Tests for ProductConfig dataclass."""

    def test_product_id_range(self) -> None:
        """Product ID range must be a valid (min, max) tuple."""
        from common.config import ProductConfig
        cfg = ProductConfig()
        lo, hi = cfg.product_id_range
        assert lo < hi

    def test_categories_non_empty(self) -> None:
        """Categories tuple must not be empty."""
        from common.config import ProductConfig
        cfg = ProductConfig()
        assert len(cfg.categories) > 0

    def test_known_product_ids_non_empty(self) -> None:
        """Known product IDs must be populated."""
        from common.config import ProductConfig
        cfg = ProductConfig()
        assert len(cfg.known_product_ids) > 0

    def test_known_product_ids_within_range(self) -> None:
        """All known product IDs must fall within the declared range."""
        from common.config import ProductConfig
        cfg = ProductConfig()
        lo, hi = cfg.product_id_range
        for pid in cfg.known_product_ids:
            assert lo <= pid <= hi, f"Product ID {pid} out of range ({lo}, {hi})"
