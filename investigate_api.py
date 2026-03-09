#!/usr/bin/env python3
"""
Investigate Demoblaze API endpoints to debug load test failures.

This script tests the exact endpoints used in load tests to identify:
1. Which credentials format is correct
2. What HTTP methods each endpoint expects
3. Whether API endpoints are working correctly

Run: python investigate_api.py
"""

import sys
from typing import Any

import requests

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a colored header."""
    print(f"\n{BOLD}{CYAN}{'=' * 70}{RESET}")
    print(f"{BOLD}{CYAN}{text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 70}{RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{CYAN}ℹ {text}{RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")


def test_api_health() -> bool:
    """Test if Demoblaze API is reachable."""
    print_header("1. API HEALTH CHECK")
    try:
        response = requests.get("https://api.demoblaze.com/", timeout=5)
        print_success(f"API is reachable: HTTP {response.status_code}")
        return True
    except Exception as e:
        print_error(f"API is unreachable: {e}")
        print_warning("Check your internet connection and whether demoblaze.com is up")
        return False


def test_login() -> dict[str, Any] | None:
    """Test login endpoint with various credential formats."""
    print_header("2. LOGIN ENDPOINT TEST")

    # Test credentials to try
    test_creds = [
        ("deltest@test.com", "Password123#", "Original hardcoded (from code)"),
        ("demo@demoblaze.com", "demo", "Demoblaze public demo account"),
        ("testuser@example.com", "TestPassword123!", "Generic test format"),
    ]

    for username, password, label in test_creds:
        print_info(f"Testing: {label}")
        print(f"  Username: {username}")
        print(f"  Password: {'*' * len(password)}")

        try:
            response = requests.post(
                "https://api.demoblaze.com/login",
                json={"username": username, "password": password},
                timeout=5,
            )

            print(f"  Status: HTTP {response.status_code}")
            body = (
                response.json()
                if response.headers.get("content-type") == "application/json"
                else response.text
            )

            if response.status_code == 200:
                if isinstance(body, dict) and "Auth_token" in body:
                    print_success(
                        f"Login successful! Token: {body['Auth_token'][:20]}..."
                    )
                    return {
                        "username": username,
                        "password": password,
                        "token": body.get("Auth_token"),
                        "response": body,
                    }
                elif isinstance(body, dict) and "errorMessage" in body:
                    print_error(f"Login rejected: {body['errorMessage']}")
                else:
                    print_warning(f"Unexpected response: {body}")
            else:
                print_error(f"Request failed: {body}")

        except Exception as e:
            print_error(f"Exception: {e}")

        print()

    print_warning("No valid credentials found. Manual account creation required.")
    return None


def test_entries_endpoint(token: str | None = None) -> None:
    """Test /entries endpoint with different HTTP methods."""
    print_header("3. /ENTRIES ENDPOINT TEST")

    print_info("Testing different HTTP methods to /entries endpoint...")
    print()

    methods = [
        ("GET", "GET /entries (no body)"),
        ("POST_EMPTY", "POST /entries (no body)"),
        ("POST_WITH_PARAMS", "POST /entries (with parameters)"),
    ]

    for method_type, description in methods:
        print_info(f"Testing: {description}")

        try:
            if method_type == "GET":
                response = requests.get("https://api.demoblaze.com/entries", timeout=5)
            elif method_type == "POST_EMPTY":
                response = requests.post("https://api.demoblaze.com/entries", timeout=5)
            else:  # POST_WITH_PARAMS
                response = requests.post(
                    "https://api.demoblaze.com/entries", json={}, timeout=5
                )

            print(f"  Status: HTTP {response.status_code}")

            if response.status_code == 200:
                print_success(f"Endpoint accepts {method_type}")
                try:
                    data = response.json()
                    print(f"  Response (first 100 chars): {str(data)[:100]}...")
                except ValueError:
                    print(f"  Response: {response.text[:100]}...")
            elif response.status_code == 405:
                print_error("HTTP 405: Method Not Allowed — try a different method")
            else:
                print_warning(f"Unexpected status: HTTP {response.status_code}")

        except Exception as e:
            print_error(f"Exception: {e}")

        print()


def test_other_endpoints() -> None:
    """Test other common endpoints."""
    print_header("4. OTHER ENDPOINTS TEST")

    endpoints = [
        ("GET", "/", "Homepage (SPA)"),
        ("POST", "/bycat", {"cat": "phones"}, "Browse by category"),
        ("POST", "/getitem", {"id": 1}, "Get item details"),
        (
            "POST",
            "/addtocart",
            {"id": 1, "cookie": "test", "flag": False},
            "Add to cart",
        ),
    ]

    for method, path, *rest in endpoints:
        if rest:
            body = rest[0]
            description = rest[1]
        else:
            body = None
            description = rest[0] if rest else path

        print_info(f"Testing: {description}")
        print(f"  {method} {path}")

        try:
            url = f"https://api.demoblaze.com{path}" if path.startswith("/") else path
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=body, timeout=5)

            print(f"  Status: HTTP {response.status_code}")

            if response.status_code in [200, 405, 404, 400]:
                print_success(f"Endpoint reachable: HTTP {response.status_code}")
            else:
                print_warning(f"Unexpected status: HTTP {response.status_code}")

        except Exception as e:
            print_error(f"Exception: {e}")

        print()


def main() -> None:
    """Main investigation sequence."""
    print(f"\n{BOLD}{CYAN}Demoblaze Load Test Investigation Script{RESET}")
    print(f"{CYAN}Testing API endpoints to identify load test issues{RESET}\n")

    # 1. Check API health
    if not test_api_health():
        print_error("Cannot proceed without API access")
        sys.exit(1)

    # 2. Test login
    login_result = test_login()

    # 3. Test /entries endpoint
    test_entries_endpoint(token=login_result.get("token") if login_result else None)

    # 4. Test other endpoints
    test_other_endpoints()

    # 5. Recommendations
    print_header("RECOMMENDATIONS")

    if not login_result:
        print_warning("No valid credentials found")
        print("\nTo fix load test failures:")
        print("1. Register a test account at: https://demoblaze.com/index.html#signup")
        print("2. Create .env file in project root with:")
        print("   TEST_USERNAME=your_email@example.com")
        print("   TEST_PASSWORD=your_password")
        print("3. Re-run this investigation script")
    else:
        print_success("Valid credentials found!")
        print(f"\n  Username: {login_result['username']}")
        print("\nUpdate .env file with these credentials:")
        print(f"  TEST_USERNAME={login_result['username']}")
        print("  TEST_PASSWORD=<the password you used>")

    print("\nFor /entries endpoint:")
    print("  - If GET works: Change all POST /entries calls to GET")
    print("  - If POST_WITH_PARAMS works: Add { } as body to POST calls")
    print("  - If neither works: Endpoint may have been removed from Demoblaze API")
    print()


if __name__ == "__main__":
    main()
