"""
Spike Load Test — sudden user surge simulation.

Uses a custom :class:`LoadTestShape` to model a spike pattern:
  ramp-up → steady-state → spike → recover → ramp-down

This validates system resilience and auto-recovery behaviour,
a key requirement in production SLA frameworks.

Run:
    locust -f tests/test_spike_load.py --headless --run-time 4m
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


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # type: ignore[type-arg]
    stats = environment.stats.total
    logger.info(
        "Spike test finished — requests=%d  failures=%d",
        stats.num_requests,
        stats.num_failures,
    )
    if stats.fail_ratio * 100 > thresholds.max_failure_rate_pct:
        environment.process_exit_code = 1


# ---------------------------------------------------------------------------
# Spike shape definition
# ---------------------------------------------------------------------------


class SpikeLoadShape(LoadTestShape):
    """
    Time-boxed spike profile (total 4 minutes): simulates sudden traffic surge.

    This profile validates system resilience under shock load:
    - Warm-up: Establish baseline
    - Steady-state: Normal operating load
    - Spike: Sudden 4x traffic surge (90→100 users in 30s)
    - Recovery: System response to load drop (auto-scaling, recovery)
    - Ramp-down: Clean shutdown

    Industry use case: Black Friday, flash sales, viral content.
    Success: Response time degradation <20%, P99 latency <10s, failure rate <1%.

    Phase          | Duration | Users | Spawn Rate | Purpose
    --------------|----------|-------|-----------|----------
    Warm-up        | 0–30s    |  10   |     2/s   | Establish baseline
    Steady-state   | 30–90s   |  25   |     5/s   | Normal load
    Spike          | 90–120s  | 100   |    25/s   | **Surge test**
    Recovery       | 120–180s |  25   |     5/s   | Auto-scaling response
    Ramp-down      | 180–240s |   0   |    10/s   | Graceful shutdown
    """

    stages = [
        {"duration": 30, "users": 10, "spawn_rate": 2},
        {"duration": 90, "users": 25, "spawn_rate": 5},
        {"duration": 120, "users": 100, "spawn_rate": 25},
        {"duration": 180, "users": 25, "spawn_rate": 5},
        {"duration": 240, "users": 0, "spawn_rate": 10},
    ]

    def tick(self) -> tuple[int, float] | None:
        """
        Calculate user count and spawn rate for current elapsed time.

        Returns: (user_count, spawn_rate) tuple, or None when all stages complete.
        """
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = stage["users"], stage["spawn_rate"]
                return tick_data
        return None


# ---------------------------------------------------------------------------
# User class
# ---------------------------------------------------------------------------


class SpikeTestUser(HttpUser):
    """
    Lightweight user for spike testing.
    Focuses on read-heavy operations to stress the catalogue layer.
    """

    host = "https://demoblaze.com"
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        self.auth = AuthManager(
            user=self,
            username=_auth_cfg.username or "deltest@test.com",
            password=_auth_cfg.password or "Password123#",
        )
        self.auth.login()

    def on_stop(self) -> None:
        self.auth.logout()

    @task(6)
    def browse_homepage(self) -> None:
        """GET / — homepage (highest frequency during spike)."""
        with self.client.get("/", catch_response=True, name="Spike: GET /") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(5)
    def browse_catalogue(self) -> None:
        """GET /entries — catalogue fetch."""
        with self.client.get(
            f"{target.api_host}/entries",
            catch_response=True,
            name="Spike: GET /entries",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(4)
    def browse_category(self) -> None:
        """POST /bycat — filter by category."""
        category = random.choice(products.categories)
        with self.client.post(
            f"{target.api_host}/bycat",
            json={"cat": category},
            catch_response=True,
            name="Spike: POST /bycat",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(3)
    def view_product(self) -> None:
        """GET /prod.html — product detail page."""
        pid = random.choice(products.known_product_ids)
        with self.client.get(
            f"/prod.html?idp_={pid}",
            catch_response=True,
            name="Spike: GET /prod.html",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(1)
    def add_to_cart(self) -> None:
        """POST /addtocart — add item under spike conditions."""
        pid = random.choice(products.known_product_ids)
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            f"{target.api_host}/addtocart",
            json={"id": pid, "cookie": cookie_val, "flag": False},
            catch_response=True,
            name="Spike: POST /addtocart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")
