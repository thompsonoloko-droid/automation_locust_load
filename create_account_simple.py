#!/usr/bin/env python
"""Automated account creation for demoblaze.com using Playwright."""

import string
import random
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright


def generate_credentials():
    """Generate unique email and password."""
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    email = f"testuser_{timestamp}@test.com"
    password = (
        "".join(random.choices(string.ascii_letters + string.digits, k=12)) + "#Aa1"
    )
    return email, password


def create_account(email, password):
    """Create a new account on demoblaze.com."""
    print(f"\n[*] Starting browser...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print(f"[*] Navigating to signup page...")
            page.goto("https://demoblaze.com/index.html")

            # Click signup link
            page.click("a#signin2")
            page.wait_for_selector("input#sign-username")

            print(f"[*] Filling form with email: {email}")
            page.fill("input#sign-username", email)
            page.fill("input#sign-password", password)

            # Click signup button
            page.click("button:has-text('Sign up')")

            # Wait for alert
            import time

            time.sleep(2)

            # Accept alert
            try:
                page.on("dialog", lambda dialog: dialog.accept())
                print(f"[✓] Account created successfully!")
            except:
                pass

            browser.close()
            return True

        except Exception as e:
            print(f"[✗] Error: {e}")
            browser.close()
            return False


def verify_login(email, password):
    """Verify login via API."""
    import requests

    print(f"[*] Verifying login via API...")
    try:
        response = requests.post(
            "https://api.demoblaze.com/login",
            json={"username": email, "password": password},
            timeout=10,
        )

        if response.status_code == 200 and "Auth_token" in response.text:
            print(f"[✓] Login successful!")
            return True
        else:
            print(f"[✗] Login failed: {response.json()}")
            return False
    except Exception as e:
        print(f"[✗] API error: {e}")
        return False


def update_env(email, password):
    """Update .env file."""
    env_path = Path(__file__).parent / ".env"
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
    print(f"[✓] .env file updated!")


def main():
    print("=" * 60)
    print("🤖 Demoblaze Account Creator")
    print("=" * 60)

    email, password = generate_credentials()
    print(f"\n[*] Generated credentials:")
    print(f"    Email:    {email}")
    print(f"    Password: {password}")

    print(f"\n[1] Creating account on demoblaze.com...")
    if not create_account(email, password):
        print("[✗] Account creation failed!")
        return

    print(f"\n[2] Verifying account login...")
    if not verify_login(email, password):
        print("[✗] Login verification failed!")
        return

    print(f"\n[3] Updating .env file...")
    update_env(email, password)

    print("\n" + "=" * 60)
    print("✅ Account creation completed successfully!")
    print("=" * 60)
    print(f"\nNew credentials in .env:")
    print(f"  TEST_USERNAME={email}")
    print(f'  TEST_PASSWORD="{password}"')


if __name__ == "__main__":
    main()
