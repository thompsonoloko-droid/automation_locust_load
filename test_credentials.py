"""Test registration on Demoblaze API"""

import requests
import time

# Create a unique test account
timestamp = int(time.time())
test_user = f"loadtest_{timestamp}@loadtest.com"
test_password = "LoadTest123!@#"

print(f"Attempting to register: {test_user}")

try:
    # Try signup
    resp = requests.post(
        "https://api.demoblaze.com/signup",
        json={"username": test_user, "password": test_password},
        timeout=5,
    )
    print(f"Signup status: {resp.status_code}")
    print(f"Signup response: {resp.json()}")

    # Try login
    print(f"\nAttempting to login...")
    login_resp = requests.post(
        "https://api.demoblaze.com/login",
        json={"username": test_user, "password": test_password},
        timeout=5,
    )
    print(f"Login status: {login_resp.status_code}")
    body = login_resp.json()
    print(f"Login response: {body}")

    if "Auth_token" in body:
        print("\n✓ SUCCESS! Login working!")
        print(f"\nUpdate your .env file with:")
        print(f"TEST_USERNAME={test_user}")
        print(f"TEST_PASSWORD={test_password}")
    elif "errorMessage" in body:
        print(f"\n✗ Login failed: {body['errorMessage']}")

except Exception as e:
    print(f"Error: {e}")
