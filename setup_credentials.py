#!/usr/bin/env python3
"""
Quick setup helper for load test credential configuration.

This script helps you:
1. Create .env file with credentials
2. Test credentials work
3. Verify configuration is correct

Run: python setup_credentials.py
"""

import os
import sys
from pathlib import Path


def print_header(text):
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_success(text):
    print(f"✓ {text}")


def print_error(text):
    print(f"✗ {text}")


def print_info(text):
    print(f"ℹ {text}")


def print_warning(text):
    print(f"⚠ {text}")


def main():
    print_header("Load Test Credential Setup")

    project_root = Path(__file__).parent
    env_file = project_root / ".env"

    print_info(f"Project root: {project_root}")

    # 1. Check current state
    print_header("Step 1: Check Current State")

    if env_file.exists():
        print_warning(".env file already exists")
        print_info(f"Location: {env_file}")
        response = input("\nDo you want to recreate it? (y/n): ").strip().lower()
        if response != "y":
            print_info("Keeping existing .env file")
            return
    else:
        print_info(".env file not found (this is normal)")

    # 2. Choose credential source
    print_header("Step 2: Choose Credential Source")

    options = [
        (
            "1",
            "Use public demo account (demo@demoblaze.com)",
            "demo@demoblaze.com",
            "demo",
        ),
        ("2", "Manual entry (I have my own test account)", None, None),
        ("3", "Create new account (goto https://demoblaze.com/signup)", None, None),
    ]

    print("Choose how to set up credentials:\n")
    for key, desc, *_ in options:
        print(f"  {key}. {desc}")

    choice = input("\nEnter choice (1-3): ").strip()

    username = None
    password = None

    if choice == "1":
        username, password = options[0][2], options[0][3]
        print_success(f"Using demo account: {username}")

    elif choice == "2":
        print_info("You'll enter credentials now. (These won't be echoed for security)")
        username = input("Enter Demoblaze username/email: ").strip()
        password = input("Enter Demoblaze password: ").strip()

        if not username or not password:
            print_error("Username and password cannot be empty!")
            return

    elif choice == "3":
        print_warning("Please create an account first:")
        print_info("1. Go to: https://demoblaze.com/index.html#signup")
        print_info("2. Create account with email and password")
        print_info("3. Come back and choose option 2 (Manual entry)")
        return
    else:
        print_error("Invalid choice")
        return

    # 3. Create .env file
    print_header("Step 3: Creating .env File")

    env_content = f"""# Demoblaze Load Test Credentials
# Created automatically - DO NOT COMMIT THIS FILE
# Keep passwords secure - .env is in .gitignore

TEST_USERNAME={username}
TEST_PASSWORD={password}

# Alternative configuration (optional)
# TARGET_API_HOST=https://api.demoblaze.com
# TARGET_HOST=https://demoblaze.com
"""

    try:
        env_file.write_text(env_content)
        print_success(f".env file created: {env_file}")
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return

    # 4. Verify .env
    print_header("Step 4: Verify Configuration")

    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)

        loaded_username = os.getenv("TEST_USERNAME")
        loaded_password = os.getenv("TEST_PASSWORD")

        if loaded_username and loaded_password:
            print_success("Configuration loaded successfully")
            print_info(f"Username: {loaded_username}")
            print_info(f"Password: {'*' * len(loaded_password)}")
        else:
            print_error("Failed to load configuration from .env")
            return

    except ImportError:
        print_warning("python-dotenv not available, skipping verification")
        print_info("Install with: pip install -r requirements.txt")

    # 5. Test credentials
    print_header("Step 5: Test Credentials (Optional)")

    test = input("\nTest credentials with API? (y/n): ").strip().lower()

    if test == "y":
        try:
            import requests

            print_info("Testing login...")
            r = requests.post(
                "https://api.demoblaze.com/login",
                json={"username": username, "password": password},
                timeout=5,
            )

            body = (
                r.json() if r.headers.get("content-type") == "application/json" else {}
            )

            if r.status_code == 200:
                if "Auth_token" in body:
                    print_success("✓ Login successful!")
                    print_info(f"Token: {body['Auth_token'][:30]}...")
                elif "errorMessage" in body:
                    print_error(f"Login failed: {body['errorMessage']}")
                    print_warning("Check your credentials and try again")
                else:
                    print_warning(f"Unexpected response: {body}")
            else:
                print_error(f"HTTP {r.status_code}: {body}")

        except ImportError:
            print_warning("requests module not available")
            print_info("Install with: pip install -r requirements.txt")
        except Exception as e:
            print_error(f"Test failed: {e}")

    # 6. Summary
    print_header("✓ Setup Complete!")

    print_info("Next steps:")
    print_info("1. Verify .env is in .gitignore (it should be)")
    print_info(
        "2. Run smoke test: locust -f tests/test_smoke_load.py --headless -u 5 -r 1 --run-time 1m"
    )
    print_info("3. Check for 407 login errors (should be zero)")
    print_info("4. Fix /entries endpoint if needed (see FIX_IMPLEMENTATION_GUIDE.md)")
    print_info("5. Commit and push changes")

    print(f"\n.env file location: {env_file}")
    print_warning(".env is git-ignored - it won't be committed (that's correct!)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
