#!/usr/bin/env python
"""Create a new test account on demoblaze.com with Playwright."""

import time
from datetime import datetime
from playwright.sync_api import sync_playwright


def create_and_test_account():
    """Create account and immediately test it."""

    # Generate unique credentials
    timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
    email = f"test_{timestamp}@test.com"
    password = "TestPass123"  # Simple password

    print(f"Creating account:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Go to demoblaze
            print("\n[1] Navigating to demoblaze.com...")
            page.goto("https://demoblaze.com/index.html", wait_until="domcontentloaded")
            page.click("a#signin2")
            page.wait_for_selector("input#sign-username", timeout=5000)

            # Fill in signup form
            print("[3] Filling signup form...")
            page.fill("input#sign-username", email)
            page.fill("input#sign-password", password)

            # Click signup button
            print("[4] Clicking signup button...")
            page.click("button#signupBtn")

            # Wait for response
            time.sleep(3)

            # Check for alert
            def handle_alert(dialog):
                msg = dialog.message
                print(f"[*] Alert message: {msg}")
                dialog.accept()

            page.once("dialog", handle_alert)
            time.sleep(1)

            print("[5] Signup appears complete!")

            browser.close()

            # Now test if we can login with API
            print("\n[6] Testing API login...")
            time.sleep(2)  # Wait for account to register

            import requests

            response = requests.post(
                "https://api.demoblaze.com/login",
                json={"username": email, "password": password},
                timeout=10,
            )

            print(f"    Status: {response.status_code}")
            print(f"    Response: {response.text}")

            if response.status_code == 200 and "Auth_token" in response.text:
                print(f"\n✅ SUCCESS! Login worked!")
                print(f"\nUpdate your .env with:")
                print(f"  TEST_USERNAME={email}")
                print(f'  TEST_PASSWORD="{password}"')
                return email, password
            else:
                print(f"\n❌ Login failed via API")
                return None, None

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
            browser.close()
            return None, None


if __name__ == "__main__":
    email, password = create_and_test_account()

    if email and password:
        # Update .env file
        from pathlib import Path

        env_path = Path(".env")
        content = env_path.read_text()

        lines = []
        for line in content.split("\n"):
            if line.startswith("TEST_USERNAME="):
                lines.append(f"TEST_USERNAME={email}")
            elif line.startswith("TEST_PASSWORD="):
                lines.append(f'TEST_PASSWORD="{password}"')
            else:
                lines.append(line)

        env_path.write_text("\n".join(lines))
        print(f"\n✅ .env file updated!")
