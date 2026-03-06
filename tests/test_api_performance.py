"""
API Performance Test — Demoblaze REST Endpoints.

Focuses specifically on the backend API layer, bypassing SPA rendering.
Tests individual endpoints under load with strict SLA assertions.

Run:
    locust -f tests/test_api_performance.py --headless -u 20 -r 2 --run-time 2m
"""

import logging
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from locust import HttpUser, between, events, task

from common.auth import AuthManager
from common.config import auth as _auth_cfg
from common.config import products, thresholds

logger = logging.getLogger(__name__)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # type: ignore[type-arg]
    stats = environment.stats.total
    if stats.fail_ratio * 100 > thresholds.max_failure_rate_pct:
        logger.error(
            "API SLA BREACH: failure rate %.2f%%", stats.fail_ratio * 100
        )
        environment.process_exit_code = 1


class APIPerformanceUser(HttpUser):
    """
    Exercises each Demoblaze REST endpoint independently under load.

    This isolates API-level response times from front-end asset loading,
    which is the industry-standard approach for backend SLA validation.
    """

    host = "https://demoblaze.com"
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        self.auth = AuthManager(
            user=self,
            username=_auth_cfg.username or "deltest@test.com",
            password=_auth_cfg.password or "Password123#",
        )
        self.auth.login()

    def on_stop(self) -> None:
        self.auth.logout()

    # ------------------------------------------------------------------
    # Authentication endpoints
    # ------------------------------------------------------------------

    @task(1)
    def test_login_endpoint(self) -> None:
        """POST /login — measure auth latency under concurrent load."""
        payload = {
            "username": _auth_cfg.username or "deltest@test.com",
            "password": _auth_cfg.password or "Password123#",
        }
        with self.client.post(
            "/login",
            json=payload,
            catch_response=True,
            name="API: POST /login",
        ) as r:
            if r.status_code == 200 and "Auth_token" in r.text:
                r.success()
            elif r.status_code == 200 and "Wrong password" in r.text:
                r.failure("Invalid credentials")
            else:
                r.failure(f"Login failed: {r.status_code}")

    # ------------------------------------------------------------------
    # Product catalogue endpoints
    # ------------------------------------------------------------------

    @task(5)
    def test_entries_endpoint(self) -> None:
        """POST /entries — catalogue load, highest frequency endpoint."""
        with self.client.post(
            "/entries",
            json={},
            catch_response=True,
            name="API: POST /entries",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Entries failed: {r.status_code}")

    @task(4)
    def test_bycat_phone(self) -> None:
        """POST /bycat — filter by phones."""
        with self.client.post(
            "/bycat",
            json={"cat": "phone"},
            catch_response=True,
            name="API: POST /bycat [phone]",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"bycat/phone failed: {r.status_code}")

    @task(4)
    def test_bycat_notebook(self) -> None:
        """POST /bycat — filter by notebooks."""
        with self.client.post(
            "/bycat",
            json={"cat": "notebook"},
            catch_response=True,
            name="API: POST /bycat [notebook]",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"bycat/notebook failed: {r.status_code}")

    @task(4)
    def test_bycat_monitor(self) -> None:
        """POST /bycat — filter by monitors."""
        with self.client.post(
            "/bycat",
            json={"cat": "monitor"},
            catch_response=True,
            name="API: POST /bycat [monitor]",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"bycat/monitor failed: {r.status_code}")

    @task(3)
    def test_getitem_endpoint(self) -> None:
        """POST /getitem — retrieve single product details."""
        pid = random.choice(products.known_product_ids)
        with self.client.post(
            "/getitem",
            json={"id": pid},
            catch_response=True,
            name="API: POST /getitem",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"getitem failed: {r.status_code}")

    # ------------------------------------------------------------------
    # Cart endpoints
    # ------------------------------------------------------------------

    @task(2)
    def test_addtocart_endpoint(self) -> None:
        """POST /addtocart — add item with session cookie."""
        pid = random.choice(products.known_product_ids)
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            "/addtocart",
            json={"id": pid, "cookie": cookie_val, "flag": False},
            catch_response=True,
            name="API: POST /addtocart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"addtocart failed: {r.status_code}")

    @task(2)
    def test_viewcart_endpoint(self) -> None:
        """POST /viewcart — retrieve cart contents."""
        cookie_val = self.auth.session_cookie or ""
        with self.client.post(
            "/viewcart",
            json={"cookie": cookie_val, "flag": False},
            catch_response=True,
            name="API: POST /viewcart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"viewcart failed: {r.status_code}")

    @task(1)
    def test_deletecart_endpoint(self) -> None:
        """POST /deletecart — remove item from cart."""
        pid = random.choice(products.known_product_ids)
        with self.client.post(
            "/deletecart",
            json={"itemid": str(pid)},
            catch_response=True,
            name="API: POST /deletecart",
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"deletecart failed: {r.status_code}")
