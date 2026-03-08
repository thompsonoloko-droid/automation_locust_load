#!/usr/bin/env python
"""Debug: check exact password value and format."""

import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("TEST_PASSWORD")
username = os.getenv("TEST_USERNAME")

# Show exact bytes
print("Username:")
print(f"  Value: {repr(username)}")
print(f"  Bytes: {username.encode() if username else 'None'}")

print("\nPassword:")
print(f"  Value: {repr(password)}")
print(f"  Bytes: {password.encode() if password else 'None'}")
print(f"  Length: {len(password) if password else 'N/A'}")
print(f"  Ends with: {repr(password[-1]) if password else 'N/A'}")

# Try login
import requests

print("\n" + "=" * 60)
print("Testing API login...")
print("=" * 60)

try:
    response = requests.post(
        "https://api.demoblaze.com/login",
        json={"username": username, "password": password},
        timeout=10,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
