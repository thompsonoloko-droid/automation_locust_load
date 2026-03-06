"""
Smoke Load Test — quick sanity check at low concurrency.

Purpose: Verify that all key endpoints are reachable and return HTTP 200
before triggering heavier load scenarios. Run this first in CI pipelines.

Run:
    locust -f tests/test_smoke_load.py --headless -u 5 -r 1 --run-time 1m
"""

import logging
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from locust import HttpUser, between, events, task

from common.auth import AuthManager
from common.config import auth as _auth_cfg
from common.config import products, target

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs) -> None:  # type: ignore[type-arg]
    logger.info("Smoke test starting — target: %s", environment.host)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # type: ignore[type-arg]
    stats = environment.stats.total
    logger.info(
        "Smoke test done — requests=%d  failures=%d  failure_rate=%.2f%%",
        stats.num_requests,
        stats.num_failures,
        stats.fail_ratio * 100,
    )
    # Allow up to 10 % failure rate on smoke (tolerates auth misconfiguration
    # in CI environments where credentials may not be injected).
    if stats.fail_ratio * 100 > 10.0:
        logger.error(
            "SMOKE FAILED: failure rate %.2f%% exceeds 10%% threshold",
            stats.fail_ratio * 100,
        )
        environment.process_exit_code = 1


class SmokeUser(HttpUser):
    """
    Minimal user that hits each key endpoint exactly once per iteration.
    Five virtual users are sufficient for smoke validation.
    """

    host = "https://demoblaze.com"
    wait_time = between(1, 2)

    def on_start(self) -> None:
        self.auth = AuthManager(
            user=self,
            username=_auth_cfg.username or "",
            password=_auth_cfg.password or "",
        )
        # Only attempt login when credentials are available; in CI
        # environments without secrets, skip auth to avoid counting
        # guaranteed login failures against the SLA threshold.
        if _auth_cfg.is_configured():
            self.auth.login()

    def on_stop(self) -> None:
        self.auth.logout()

    @task
    def smoke_homepage(self) -> None:
        """Verify homepage is reachable."""
        with self.client.get("/", catch_response=True, name="Smoke: GET /") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Homepage unavailable: HTTP {r.status_code}")

    @task
    def smoke_entries(self) -> None:
        """Verify product catalogue endpoint."""
        with self.client.post(
            f"{target.api_host}/entries",
            catch_response=True,
            name="Smoke: POST /entries",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Entries unavailable: HTTP {r.status_code}")

    @task
    def smoke_bycat(self) -> None:
        """Verify category filter endpoint."""
        with self.client.post(
            f"{target.api_host}/bycat",
            json={"cat": "phone"},
            catch_response=True,
            name="Smoke: POST /bycat",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Bycat unavailable: HTTP {r.status_code}")

    @task
    def smoke_product_page(self) -> None:
        """Verify product detail page loads."""
        pid = random.choice(products.known_product_ids)
        with self.client.get(
            f"/prod.html?idp_={pid}",
            catch_response=True,
            name="Smoke: GET /prod.html",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Product page unavailable: HTTP {r.status_code}")

    @task
    def smoke_cart_page(self) -> None:
        """Verify cart page loads."""
        with self.client.get(
            "/cart.html",
            catch_response=True,
            name="Smoke: GET /cart.html",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Cart page unavailable: HTTP {r.status_code}")
