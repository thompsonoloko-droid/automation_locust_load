"""
Checkout Flow Test — complete end-to-end purchase journey.

Models the full user journey through the Demoblaze purchase funnel:
    register (optional) → login → browse → add-to-cart → checkout → purchase

This is the highest-value scenario for business-critical SLA validation.

Run:
    locust -f tests/test_checkout_flow.py --headless -u 10 -r 1 --run-time 3m
"""

import logging
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from locust import HttpUser, SequentialTaskSet, between, events, task

from common.auth import AuthManager
from common.config import auth as _auth_cfg
from common.config import products, target, thresholds

logger = logging.getLogger(__name__)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # type: ignore[type-arg]
    stats = environment.stats.total
    logger.info(
        "Checkout flow test finished — requests=%d  failures=%d  p95=%.0fms",
        stats.num_requests,
        stats.num_failures,
        stats.get_response_time_percentile(0.95),
    )
    if stats.fail_ratio * 100 > thresholds.max_failure_rate_pct:
        environment.process_exit_code = 1


# ---------------------------------------------------------------------------
# Sequential task set — funnel order matters
# ---------------------------------------------------------------------------


class CheckoutTaskSet(SequentialTaskSet):
    """
    Ordered sequence representing a single customer purchase journey.
    SequentialTaskSet ensures tasks execute in definition order.
    """

    def on_start(self) -> None:
        """Initialise auth and cart state for this journey."""
        self.auth = AuthManager(
            user=self.user,
            username=_auth_cfg.username or "deltest@test.com",
            password=_auth_cfg.password or "Password123#",
        )
        self.selected_product: int = random.choice(products.known_product_ids)

    @task
    def step_1_login(self) -> None:
        """Step 1: Authenticate."""
        success = self.auth.login()
        if not success:
            logger.warning("Checkout journey aborted — login failed")

    @task
    def step_2_browse_catalogue(self) -> None:
        """Step 2: View product catalogue."""
        with self.client.post(
            f"{target.api_host}/entries",
            json={},
            catch_response=True,
            name="Checkout: POST /entries",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Catalogue load failed: {r.status_code}")

    @task
    def step_3_select_category(self) -> None:
        """Step 3: Filter by category."""
        cat = random.choice(products.categories)
        with self.client.post(
            f"{target.api_host}/bycat",
            json={"cat": cat},
            catch_response=True,
            name="Checkout: POST /bycat",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Category filter failed: {r.status_code}")

    @task
    def step_4_view_product(self) -> None:
        """Step 4: View chosen product detail page."""
        with self.client.get(
            f"/prod.html?idp_={self.selected_product}",
            catch_response=True,
            name="Checkout: GET /prod.html",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Product page failed: {r.status_code}")

    @task
    def step_5_add_to_cart(self) -> None:
        """Step 5: Add product to cart."""
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            f"{target.api_host}/addtocart",
            json={"id": self.selected_product, "cookie": cookie_val, "flag": False},
            catch_response=True,
            name="Checkout: POST /addtocart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Add-to-cart failed: {r.status_code}")

    @task
    def step_6_view_cart(self) -> None:
        """Step 6: Open the cart / review page."""
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            f"{target.api_host}/viewcart",
            json={"cookie": cookie_val, "flag": False},
            catch_response=True,
            name="Checkout: POST /viewcart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"View-cart failed: {r.status_code}")

    @task
    def step_7_place_order(self) -> None:
        """Step 7: Submit order (critical path, highest SLA weight)."""
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
            name="Checkout: POST /purchase",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Purchase failed: {r.status_code}")

    @task
    def step_8_logout(self) -> None:
        """Step 8: Reset journey — log out."""
        self.auth.logout()
        # Pick a new product for next journey iteration
        self.selected_product = random.choice(products.known_product_ids)


# ---------------------------------------------------------------------------
# User class
# ---------------------------------------------------------------------------


class CheckoutUser(HttpUser):
    """
    User that exclusively runs the complete checkout journey
    in strict sequential order.
    """

    host = "https://demoblaze.com"
    wait_time = between(1, 3)
    tasks = [CheckoutTaskSet]
