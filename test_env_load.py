#!/usr/bin/env python
"""Quick API test to verify current .env credentials."""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

email = os.getenv("TEST_USERNAME")
password = os.getenv("TEST_PASSWORD")

print(f"Testing credentials from .env:")
print(f"  Email:    {email}")
print(f"  Password: {repr(password)}")

try:
    response = requests.post(
        "https://api.demoblaze.com/login",
        json={"username": email, "password": password},
        timeout=10,
    )

    print(f"\nAPI Response Status: {response.status_code}")
    print(f"API Response Body: {response.text}")

    if response.status_code == 200 and "Auth_token" in response.text:
        print("\n✅ LOGIN SUCCESSFUL!")
    else:
        print("\n❌ LOGIN FAILED!")

except Exception as e:
    print(f"\n❌ Error: {e}")
