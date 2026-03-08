#!/usr/bin/env python
"""
Automated account creation for demoblaze.com

This script:
1. Opens demoblaze.com signup page
2. Creates a new account with random credentials
3. Updates .env file with the new credentials
4. Verifies login works
"""

import os
import string
import random
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright, expect


def generate_credentials() -> tuple[str, str]:
    """Generate unique email and password for test account.

    Returns:
        Tuple of (email, password)
    """
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    email = f"testuser_{timestamp}@test.com"

    # Generate strong password
    password = (
        "".join(random.choices(string.ascii_letters + string.digits, k=12)) + "#Aa1"
    )

    return email, password


def signup_account(email: str, password: str) -> bool:
    """Sign up a new account on demoblaze.com.

    Args:
        email: Email address for the new account
        password: Password for the new account

    Returns:
        True if signup successful, False otherwise
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Navigate to signup page
            print(f"[*] Navigating to demoblaze.com signup...")
            page.goto(
                "https://demoblaze.com/index.html#signup", wait_until="networkidle"
            )

            # Wait for signup form to load
            page.wait_for_selector("input#sign-username", timeout=10000)

            # Fill in signup form
            print(f"[*] Filling signup form with email: {email}")
            page.fill("input#sign-username", email)
            page.fill("input#sign-password", password)

            # Click signup button
            signup_button = page.locator("button:has-text('Sign up')")
            page.click("button:has-text('Sign up')")

            # Wait for success or error alert
            page.wait_for_selector(
                "text=/Sign up successful|This user already exist/", timeout=10000
            )

            # Check if signup was successful
            alert_text = page.locator("css=.modal-body").text_content()
            page.click("button:has-text('OK')")

            if "successful" in alert_text.lower():
                print(f"[✓] Signup successful!")
                return True
            else:
                print(f"[✗] Signup failed: {alert_text}")
                return False

        except Exception as e:
            print(f"[✗] Error during signup: {e}")
            return False
        finally:
            browser.close()


def verify_login(email: str, password: str) -> bool:
    """Verify the account can login successfully.

    Args:
        email: Email to login with
        password: Password to login with

    Returns:
        True if login successful, False otherwise
    """
    import requests
    import json

    try:
        print(f"[*] Verifying login via API...")
        payload = {"username": email, "password": password}
        response = requests.post(
            "https://api.demoblaze.com/login", json=payload, timeout=10
        )

        data = response.json()
        if response.status_code == 200 and "Auth_token" in data:
            print(f"[✓] Login verified! Auth token received.")
            return True
        else:
            print(f"[✗] Login failed: {data.get('errorMessage', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"[✗] Error verifying login: {e}")
        return False


def update_env_file(email: str, password: str) -> bool:
    """Update .env file with new credentials.

    Args:
        email: Email to store
        password: Password to store

    Returns:
        True if update successful, False otherwise
    """
    env_path = Path(__file__).parent / ".env"

    try:
        # Read current .env
        content = env_path.read_text()

        # Replace credentials
        lines = []
        for line in content.split("\n"):
            if line.startswith("TEST_USERNAME="):
                lines.append(f"TEST_USERNAME={email}")
            elif line.startswith("TEST_PASSWORD="):
                lines.append(f'TEST_PASSWORD="{password}"')
            else:
                lines.append(line)

        # Write updated .env
        env_path.write_text("\n".join(lines))
        print(f"[✓] .env file updated successfully!")
        return True

    except Exception as e:
        print(f"[✗] Error updating .env: {e}")
        return False


def main():
    """Main execution flow."""
    print("=" * 60)
    print("🤖 Demoblaze Account Creator")
    print("=" * 60)

    # Generate credentials
    email, password = generate_credentials()
    print(f"\n[*] Generated credentials:")
    print(f"    Email:    {email}")
    print(f"    Password: {password}")

    # Sign up account
    print(f"\n[*] Step 1: Creating account on demoblaze.com...")
    if not signup_account(email, password):
        print("[✗] Signup failed! Exiting.")
        return False

    # Verify login
    print(f"\n[*] Step 2: Verifying account login...")
    if not verify_login(email, password):
        print("[✗] Login verification failed! Exiting.")
        return False

    # Update .env
    print(f"\n[*] Step 3: Updating .env file...")
    if not update_env_file(email, password):
        print("[✗] .env update failed! Exiting.")
        return False

    # Success
    print("\n" + "=" * 60)
    print("✅ Account creation completed successfully!")
    print("=" * 60)
    print(f"\nNew credentials saved to .env:")
    print(f"  Email:    {email}")
    print(f"  Password: {password}")
    print(f"\nYou can now run tests with this new account.")
    return True


if __name__ == "__main__":
    main()
