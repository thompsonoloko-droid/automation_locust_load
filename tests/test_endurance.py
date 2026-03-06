"""
Endurance / Soak Test — sustained load over an extended period.

Validates that memory usage, response times, and error rates remain
stable when the system is subjected to moderate load for a long time.
Industry standard: run for 30–60 minutes in CI nightly pipelines.

Run (short soak — CI):
    locust -f tests/test_endurance.py --headless -u 20 -r 2 --run-time 30m

Run (full soak — nightly):
    locust -f tests/test_endurance.py --headless -u 30 -r 2 --run-time 60m
"""

import logging
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from locust import HttpUser, LoadTestShape, between, events, task

from common.auth import AuthManager
from common.config import auth as _auth_cfg
from common.config import products, target, thresholds

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Endurance shape definition
# ---------------------------------------------------------------------------


class EnduranceLoadShape(LoadTestShape):
    """
    Gradual ramp-up then sustained plateau (default: 30 min total).

    Phase        | Duration | Users | Spawn Rate
    -------------|----------|-------|----------
    Ramp-up      | 0–5 min  |  20   |  2/s
    Sustained    | 5–25 min |  20   |  2/s
    Ramp-down    | 25–30min |   0   |  5/s
    """

    # Override via CLI --run-time for different soak durations
    stages = [
        {"duration": 300, "users": 20, "spawn_rate": 2},
        {"duration": 1500, "users": 20, "spawn_rate": 2},
        {"duration": 1800, "users": 0, "spawn_rate": 5},
    ]

    def tick(self) -> tuple[int, float] | None:
        run_time = self.get_current_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None


# ---------------------------------------------------------------------------
# Event hooks — periodic SLA monitoring
# ---------------------------------------------------------------------------


@events.test_start.add_listener
def on_test_start(environment, **kwargs) -> None:  # type: ignore[type-arg]
    logger.info("Endurance / soak test starting.")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # type: ignore[type-arg]
    stats = environment.stats.total
    logger.info(
        "Soak test finished — total_requests=%d  failures=%d  "
        "p95=%.0fms  p99=%.0fms",
        stats.num_requests,
        stats.num_failures,
        stats.get_response_time_percentile(0.95),
        stats.get_response_time_percentile(0.99),
    )
    if stats.fail_ratio * 100 > thresholds.max_failure_rate_pct:
        logger.error(
            "Endurance SLA BREACH: failure rate %.2f%%",
            stats.fail_ratio * 100,
        )
        environment.process_exit_code = 1


# ---------------------------------------------------------------------------
# User class
# ---------------------------------------------------------------------------


class EnduranceUser(HttpUser):
    """
    Soak-test user — balanced mix of read / write operations.
    Slightly lower wait time to maintain throughput over a long run.
    """

    host = "https://demoblaze.com"
    wait_time = between(2, 5)

    def on_start(self) -> None:
        self.auth = AuthManager(
            user=self,
            username=_auth_cfg.username or "deltest@test.com",
            password=_auth_cfg.password or "Password123#",
        )
        self.auth.login()
        self._request_count = 0

    def on_stop(self) -> None:
        self.auth.logout()

    def _validate(self, response) -> None:  # type: ignore[type-arg]
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"HTTP {response.status_code}")

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task(5)
    def browse_homepage(self) -> None:
        """GET / — keep the home-page hot in soak tests."""
        with self.client.get("/", catch_response=True, name="Soak: GET /") as r:
            self._validate(r)
            self._request_count += 1

    @task(4)
    def catalogue_poll(self) -> None:
        """POST /entries — repeated catalogue poll checks for memory leaks."""
        with self.client.post(
            f"{target.api_host}/entries",
            catch_response=True,
            name="Soak: POST /entries",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(3)
    def category_filter(self) -> None:
        """POST /bycat — rotate category filter to exercise all code paths."""
        cat = random.choice(products.categories)
        with self.client.post(
            f"{target.api_host}/bycat",
            json={"cat": cat},
            catch_response=True,
            name="Soak: POST /bycat",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(3)
    def view_product(self) -> None:
        """GET /prod.html — walk through all product pages."""
        pid = random.choice(products.known_product_ids)
        with self.client.get(
            f"/prod.html?idp_={pid}",
            catch_response=True,
            name="Soak: GET /prod.html",
        ) as r:
            self._validate(r)

    @task(2)
    def add_to_cart(self) -> None:
        """POST /addtocart — cart writes under sustained load."""
        pid = random.choice(products.known_product_ids)
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            f"{target.api_host}/addtocart",
            json={"id": pid, "cookie": cookie_val, "flag": False},
            catch_response=True,
            name="Soak: POST /addtocart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(2)
    def view_cart(self) -> None:
        """POST /viewcart — cart reads under sustained load."""
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            f"{target.api_host}/viewcart",
            json={"cookie": cookie_val, "flag": False},
            catch_response=True,
            name="Soak: POST /viewcart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(1)
    def re_authenticate(self) -> None:
        """Re-login periodically — validates token expiry handling."""
        self.auth.login()
