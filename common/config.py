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
    """Base URL and timeout settings for the system-under-test.

    Demoblaze exposes two origins:
    - ``host``     — HTML SPA served from demoblaze.com (GET pages)
    - ``api_host`` — REST API served from api.demoblaze.com (POST endpoints)
    """

    host: str = field(
        default_factory=lambda: os.getenv("TARGET_HOST", "https://demoblaze.com")
    )
    api_host: str = field(
        default_factory=lambda: os.getenv(
            "TARGET_API_HOST", "https://api.demoblaze.com"
        )
    )
    request_timeout: int = field(
        default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30"))
    )
    connect_timeout: int = field(
        default_factory=lambda: int(os.getenv("CONNECT_TIMEOUT", "10"))
    )


@dataclass(frozen=True)
class AuthConfig:
    """
    Credentials loaded from environment variables.

    Optional by design: Smoke tests can run with empty credentials (public catalog),
    but checkout/cart/order flows require valid username + password.

    Usage:
        config = AuthConfig()
        if config.is_configured():
            # Safe to use in authenticated tests
            manager = AuthManager(..., username=config.username, password=config.password)
        else:
            # Fallback to defaults or skip auth-required tests
            logger.warning("Credentials not configured; skipping authenticated scenarios")

    Environment Variables:
        TEST_USERNAME: Username for demoblaze.com (default: "")
        TEST_PASSWORD: Password for demoblaze.com (default: "")
    """

    username: str = field(default_factory=lambda: os.getenv("TEST_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("TEST_PASSWORD", ""))

    def is_configured(self) -> bool:
        """Return True when both username and password are set."""
        return bool(self.username and self.password)


@dataclass(frozen=True)
class LoadConfig:
    """
    Default load-shape parameters (overridable via Locust CLI flags).

    These control the fundamental behavior of Locust:
    - users: Total concurrent virtual users to simulate
    - spawn_rate: Users to spawn per second (ramp-up speed)
    - run_time: Total test duration (e.g., "5m" = 5 minutes)
    - min_wait, max_wait: Random think-time between requests (ms)

    CLI Override Example:
        locust -f tests/locustfile.py -u 100 -r 10 --run-time 10m
        (overrides users, spawn_rate, run_time from config)

    Environment Variables:
        LOCUST_USERS: Number of concurrent users (default: 50)
        LOCUST_SPAWN_RATE: Users spawned per second (default: 5)
        LOCUST_RUN_TIME: Total duration (default: "5m")
        LOCUST_MIN_WAIT: Min wait between requests in ms (default: 1)
        LOCUST_MAX_WAIT: Max wait between requests in ms (default: 3)
    """

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
    """
    SLA / acceptance thresholds for custom assertions and CI/CD gating.

    These values gate automated test execution in CI pipelines:
    - If max_failure_rate_pct threshold breached → exit code 1 (hard gate)
    - All metrics logged for reporting / APM integration

    SLA Interpretation:
        max_response_time_ms: P95 latency must stay <2s (industry standard: <1s)
        max_failure_rate_pct: Up to 1% failures tolerated (e-commerce: <0.1%)
        min_rps: Minimum throughput — validates system isn't saturated

    CI/CD Integration (GitHub Actions):
        Smoke Load: ~10% failure tolerance (optional experiments)
        Production: ~1% failure rate (hard billing SLA)

    Environment Variables:
        SLA_MAX_RESPONSE_MS: Max acceptable P95 response time (default: 2000)
        SLA_MAX_FAILURE_RATE: Max failure rate % for gating (default: 1.0)
        SLA_MIN_RPS: Minimum requests/sec throughput (default: 10.0)
    """

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
    """
    Known product IDs and categories from Demoblaze.

    Product Inventory:
        IDs 1–9 are guaranteed available on demoblaze.com
        IDs map to specific phones, notebooks, and monitors

    Categories:
        "phone": Mobile devices (IDs 1–5)
        "notebook": Laptops (IDs 6–8)
        "monitor": Displays (ID 9)

    Usage in Load Tests:
        - browse_by_category: Randomly select category, fetch products
        - view_product: Access product detail page (idp_={id})
        - add_to_cart: Add random product to cart

    Testing Strategy:
        - Always use known_product_ids to avoid 404 errors
        - Random selection prevents caching bias
        - Test data valid as of Demoblaze 2024
    """

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
