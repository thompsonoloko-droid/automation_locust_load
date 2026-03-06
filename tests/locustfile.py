"""
Main Locust performance test — browsing & cart flow for Demoblaze.

Target: https://demoblaze.com
Run (interactive UI):
    locust -f tests/locustfile.py

Run (headless):
    locust -f tests/locustfile.py --headless -u 50 -r 5 --run-time 5m

Run via locust.conf defaults:
    locust -f tests/locustfile.py
"""

import logging
import os
import random
import sys

# Allow 'common' imports when running locust from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from locust import HttpUser, between, events, task

from common.auth import AuthManager
from common.config import auth as _auth_cfg
from common.config import products, target, thresholds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Global event hooks
# ---------------------------------------------------------------------------


@events.test_start.add_listener
def on_test_start(environment, **kwargs) -> None:  # type: ignore[type-arg]
    logger.info("Load test starting — target: %s", environment.host)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # type: ignore[type-arg]
    stats = environment.stats.total
    logger.info(
        "Load test finished — requests=%d  failures=%d  avg_resp=%.0fms",
        stats.num_requests,
        stats.num_failures,
        stats.avg_response_time,
    )
    if stats.fail_ratio * 100 > thresholds.max_failure_rate_pct:
        logger.error(
            "SLA BREACH: failure rate %.2f%% exceeds threshold %.2f%%",
            stats.fail_ratio * 100,
            thresholds.max_failure_rate_pct,
        )
        environment.process_exit_code = 1


# ---------------------------------------------------------------------------
# DemoblazeUser: Simulates Realistic Shopper Behaviour
# ---------------------------------------------------------------------------


class DemoblazeUser(HttpUser):
    """
    Locust user for https://demoblaze.com/.
    Simulates realistic browsing, cart, and authentication flows.
    """

    wait_time = between(1, 3)
    host = "https://demoblaze.com"

    def on_start(self) -> None:
        """Authenticate before executing tasks."""
        self.auth = AuthManager(
            user=self,
            username=_auth_cfg.username or "deltest@test.com",
            password=_auth_cfg.password or "Password123#",
        )
        self.auth.login()

    def on_stop(self) -> None:
        self.auth.logout()

    def _validate(self, response) -> None:  # type: ignore[type-arg]
        if response.status_code != 200:
            response.failure(f"HTTP {response.status_code}")
        else:
            response.success()

    @task(5)
    def view_homepage(self) -> None:
        """GET / — most frequent action."""
        with self.client.get("/", catch_response=True, name="GET /") as r:
            self._validate(r)

    @task(4)
    def browse_by_category(self) -> None:
        """POST /bycat — browse phones / notebooks / monitors."""
        category = random.choice(products.categories)
        with self.client.post(
            f"{target.api_host}/bycat",
            json={"cat": category},
            catch_response=True,
            name="POST /bycat",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(3)
    def view_product_detail(self) -> None:
        """GET /prod.html — view a random product."""
        pid = random.choice(products.known_product_ids)
        with self.client.get(
            f"/prod.html?idp_={pid}",
            catch_response=True,
            name="GET /prod.html",
        ) as r:
            self._validate(r)

    @task(3)
    def get_product_entries(self) -> None:
        """POST /entries — retrieve all product listings."""
        with self.client.post(
            f"{target.api_host}/entries",
            json={},
            catch_response=True,
            name="POST /entries",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(2)
    def add_to_cart(self) -> None:
        """POST /addtocart — add random product to cart."""
        pid = random.choice(products.known_product_ids)
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            f"{target.api_host}/addtocart",
            json={"id": pid, "cookie": cookie_val, "flag": False},
            catch_response=True,
            name="POST /addtocart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Add-to-cart failed: {r.status_code}")

    @task(2)
    def view_cart(self) -> None:
        """POST /viewcart — retrieve current cart contents."""
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            f"{target.api_host}/viewcart",
            json={"cookie": cookie_val, "flag": False},
            catch_response=True,
            name="POST /viewcart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"View-cart failed: {r.status_code}")

    @task(1)
    def view_cart_page(self) -> None:
        """GET /cart.html — load the shopping-cart SPA page."""
        with self.client.get(
            "/cart.html", catch_response=True, name="GET /cart.html"
        ) as r:
            self._validate(r)

    @task(1)
    def place_order(self) -> None:
        """POST /purchase — simulate order submission."""
        with self.client.post(
            f"{target.api_host}/purchase",
            json={
                "name": "Load Test User",
                "country": "UK",
                "city": "London",
                "card": "4444333322221111",
                "month": "12",
                "year": "2030",
            },
            catch_response=True,
            name="POST /purchase",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Purchase failed: {r.status_code}")
