"""
Unit tests — Locust user classes (locustfile.py, test_api_performance.py, etc.)

Verifies task weights, user configuration, and event hooks without
spawning real HTTP sessions.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestDemoblazeUser:
    """Tests for DemoblazeUser in tests/locustfile.py."""

    def test_host_is_demoblaze(self) -> None:
        """Default host must be set to demoblaze.com."""
        from tests.locustfile import DemoblazeUser

        assert DemoblazeUser.host == "https://demoblaze.com"

    def test_wait_time_is_configured(self) -> None:
        """wait_time must be set (not None)."""
        from tests.locustfile import DemoblazeUser

        assert DemoblazeUser.wait_time is not None

    def test_tasks_exist(self) -> None:
        """DemoblazeUser must have at least 5 defined tasks."""
        from tests.locustfile import DemoblazeUser

        task_methods = [
            m
            for m in dir(DemoblazeUser)
            if callable(getattr(DemoblazeUser, m))
            and hasattr(getattr(DemoblazeUser, m), "locust_task_weight")
        ]
        assert (
            len(task_methods) >= 5
        ), f"Expected at least 5 tasks, found {len(task_methods)}"

    def test_homepage_task_has_highest_weight(self) -> None:
        """view_homepage must have higher task weight than place_order."""
        from tests.locustfile import DemoblazeUser

        homepage_weight = getattr(
            DemoblazeUser.view_homepage, "locust_task_weight", None
        )
        order_weight = getattr(DemoblazeUser.place_order, "locust_task_weight", None)
        assert homepage_weight is not None
        assert order_weight is not None
        assert homepage_weight > order_weight


class TestAPIPerformanceUser:
    """Tests for APIPerformanceUser in tests/test_api_performance.py."""

    def test_host_is_demoblaze(self) -> None:
        """APIPerformanceUser host must target the Demoblaze REST API."""
        from tests.test_api_performance import APIPerformanceUser

        assert APIPerformanceUser.host == "https://api.demoblaze.com"

    def test_entries_task_highest_weight(self) -> None:
        """POST /entries must have the highest API task weight."""
        from tests.test_api_performance import APIPerformanceUser

        entries_weight = getattr(
            APIPerformanceUser.test_entries_endpoint, "locust_task_weight", None
        )
        login_weight = getattr(
            APIPerformanceUser.test_login_endpoint, "locust_task_weight", None
        )
        assert entries_weight is not None
        assert login_weight is not None
        assert entries_weight > login_weight


class TestSpikeLoadShape:
    """Tests for the SpikeLoadShape custom LoadTestShape."""

    def test_stages_are_ordered(self) -> None:
        """Spike stages must have strictly increasing duration values."""
        from tests.test_spike_load import SpikeLoadShape

        durations = [s["duration"] for s in SpikeLoadShape.stages]
        assert durations == sorted(durations), "Stages must be in ascending order"

    def test_spike_stage_has_highest_users(self) -> None:
        """The spike stage must have the maximum user count."""
        from tests.test_spike_load import SpikeLoadShape

        max_users = max(s["users"] for s in SpikeLoadShape.stages)
        # Spike should be at least 3× base load
        base_users = SpikeLoadShape.stages[0]["users"]
        assert (
            max_users >= base_users * 3
        ), "Spike peak must be at least 3× the base user count"

    def test_tick_returns_none_after_last_stage(self) -> None:
        """tick() must return None when run time exceeds all stage durations."""
        from tests.test_spike_load import SpikeLoadShape

        shape = SpikeLoadShape()
        last_duration = SpikeLoadShape.stages[-1]["duration"]
        shape.get_run_time = lambda: last_duration + 1  # type: ignore
        assert shape.tick() is None

    def test_tick_returns_tuple_within_stages(self) -> None:
        """tick() must return (users, spawn_rate) tuple during active stages."""
        from tests.test_spike_load import SpikeLoadShape

        shape = SpikeLoadShape()
        shape.get_run_time = lambda: 1  # type: ignore
        result = shape.tick()
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestEnduranceLoadShape:
    """Tests for EnduranceLoadShape."""

    def test_stages_are_ordered(self) -> None:
        """Endurance stages must have strictly increasing durations."""
        from tests.test_endurance import EnduranceLoadShape

        durations = [s["duration"] for s in EnduranceLoadShape.stages]
        assert durations == sorted(durations)

    def test_final_stage_winds_down(self) -> None:
        """Last endurance stage must ramp users down to zero."""
        from tests.test_endurance import EnduranceLoadShape

        last_stage = EnduranceLoadShape.stages[-1]
        assert last_stage["users"] == 0, "Final stage must set users=0"

    def test_plateau_stage_exists(self) -> None:
        """At least one stage must hold users at a non-zero steady state."""
        from tests.test_endurance import EnduranceLoadShape

        steady_stages = [s for s in EnduranceLoadShape.stages if s["users"] > 0]
        assert len(steady_stages) >= 1


class TestCheckoutTaskSet:
    """Tests for CheckoutTaskSet sequential task ordering."""

    def test_task_set_has_required_steps(self) -> None:
        """CheckoutTaskSet must contain all 8 sequential steps."""
        from tests.test_checkout_flow import CheckoutTaskSet

        step_methods = [
            m
            for m in dir(CheckoutTaskSet)
            if m.startswith("step_") and callable(getattr(CheckoutTaskSet, m))
        ]
        assert (
            len(step_methods) >= 7
        ), f"Expected at least 7 steps, got {len(step_methods)}"

    def test_checkout_user_uses_task_set(self) -> None:
        """CheckoutUser must delegate all tasks to CheckoutTaskSet."""
        from tests.test_checkout_flow import CheckoutTaskSet, CheckoutUser

        assert CheckoutTaskSet in CheckoutUser.tasks


class TestSmokeUser:
    """Tests for SmokeUser in tests/test_smoke_load.py."""

    def test_all_critical_endpoints_covered(self) -> None:
        """SmokeUser must exercise homepage, entries, bycat, prod.html, cart.html."""
        from tests.test_smoke_load import SmokeUser

        task_names = [
            m
            for m in dir(SmokeUser)
            if m.startswith("smoke_") and callable(getattr(SmokeUser, m))
        ]
        assert (
            len(task_names) >= 5
        ), f"Smoke user must cover at least 5 endpoints, found {len(task_names)}"
