"""
Configuration module for the Locust performance test framework.

All settings are loaded from environment variables (with sensible defaults
for public demoblaze.com). Sensitive values MUST be provided via a .env file
or CI/CD secrets — never hard-coded here.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class TargetConfig:
    """Base URL and timeout settings for the system-under-test."""

    host: str = field(
        default_factory=lambda: os.getenv("TARGET_HOST", "https://demoblaze.com")
    )
    request_timeout: int = field(
        default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30"))
    )
    connect_timeout: int = field(
        default_factory=lambda: int(os.getenv("CONNECT_TIMEOUT", "10"))
    )


@dataclass(frozen=True)
class AuthConfig:
    """Credentials loaded from environment variables."""

    username: str = field(default_factory=lambda: os.getenv("TEST_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("TEST_PASSWORD", ""))

    def is_configured(self) -> bool:
        """Return True when both username and password are set."""
        return bool(self.username and self.password)


@dataclass(frozen=True)
class LoadConfig:
    """Default load-shape parameters (overridable via Locust CLI flags)."""

    users: int = field(default_factory=lambda: int(os.getenv("LOCUST_USERS", "50")))
    spawn_rate: int = field(
        default_factory=lambda: int(os.getenv("LOCUST_SPAWN_RATE", "5"))
    )
    run_time: str = field(default_factory=lambda: os.getenv("LOCUST_RUN_TIME", "5m"))
    min_wait: int = field(
        default_factory=lambda: int(os.getenv("LOCUST_MIN_WAIT", "1"))
    )
    max_wait: int = field(
        default_factory=lambda: int(os.getenv("LOCUST_MAX_WAIT", "3"))
    )


@dataclass(frozen=True)
class ThresholdConfig:
    """SLA / acceptance thresholds for custom assertions."""

    max_response_time_ms: int = field(
        default_factory=lambda: int(os.getenv("SLA_MAX_RESPONSE_MS", "2000"))
    )
    max_failure_rate_pct: float = field(
        default_factory=lambda: float(os.getenv("SLA_MAX_FAILURE_RATE", "1.0"))
    )
    min_rps: float = field(
        default_factory=lambda: float(os.getenv("SLA_MIN_RPS", "10.0"))
    )


@dataclass(frozen=True)
class ProductConfig:
    """Known product IDs and categories from Demoblaze."""

    product_id_range: tuple[int, int] = (1, 9)
    categories: tuple[str, ...] = ("phone", "notebook", "monitor")
    known_product_ids: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9)


# ---------------------------------------------------------------------------
# Module-level singletons — import directly where needed
# ---------------------------------------------------------------------------
target = TargetConfig()
auth = AuthConfig()
load = LoadConfig()
thresholds = ThresholdConfig()
products = ProductConfig()
