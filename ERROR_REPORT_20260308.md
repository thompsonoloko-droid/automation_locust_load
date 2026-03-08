# Load Test Error Report & Fix Guide

**Date:** March 8, 2026  
**Project:** automation_locust_load  
**Test Status:** ❌ FAILED with 2,162 errors

---

## 🔴 Critical Errors Found

### **Error 1: 407 Login Failures** (AUTHENTICATION)
```
POST /login [auth]: Login failed — status=200, body={"errorMessage":"Wrong password."}
```

**Occurrences:** 407  
**Severity:** 🔴 Critical  
**Root Cause:** Invalid or non-existent test credentials

#### Details
The load tests are using hardcoded fallback credentials:
- **Username:** `deltest@test.com`
- **Password:** `Password123#`

These appear to either:
1. Not exist on demoblaze.com
2. Have an incorrect password
3. Have been deleted

**Files using hardcoded credentials:**
- `tests/locustfile.py` (lines 92-93)
- `tests/test_endurance.py` (lines 143-144)
- `tests/test_checkout_flow.py` (lines 83-84)
- `tests/test_api_performance.py` (lines 60-61, 76-77)
- `tests/test_spike_load.py` (lines 109-110)

---

### **Error 2: 1755 HTTP 405 Errors** (METHOD NOT ALLOWED)
```
POST Soak: POST /entries: HTTP 405
```

**Occurrences:** 1,755  
**Severity:** 🔴 Critical  
**Root Cause:** Wrong HTTP method or endpoint change

#### Details
The `/entries` endpoint is responding with **HTTP 405** meaning "Method Not Allowed".

**Possible causes:**
1. The endpoint expects a different HTTP method (maybe GET instead of POST)
2. The API has changed on Demoblaze
3. The endpoint requires specific headers
4. The endpoint URL is incorrect

**Files using /entries endpoint:**
- `tests/locustfile.py` - `browse_by_category()` task
- `tests/test_smoke_load.py` - Product browsing
- `tests/test_endurance.py` - Product catalog access
- `tests/test_api_performance.py` - API endpoint test

---

## ✅ Fix Guide

### **Fix 1: Create Valid Test Credentials**

#### Option A: Use Public Demoblaze Account (Recommended)
1. Go to: https://demoblaze.com
2. Click "Sign up"
3. Create a test account with a valid email
4. Remember the credentials

#### Option B: Register Programmatically
```bash
# Run from automation_locust_load directory
cd d:\Automation\automation_locust_load

# Create a quick registration script
python3 << 'EOF'
import requests

# Register new test user
response = requests.post(
    "https://api.demoblaze.com/signup",
    json={
        "username": "loadtest_" + str(int(time.time()))[-6:],
        "password": "TestPassword123!"
    },
    timeout=10
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
EOF
```

#### Option C: Use Environment Variables (Recommended)
1. Create/update `.env` file:
```env
TEST_USERNAME=your_valid_email@example.com
TEST_PASSWORD=your_actual_password
```

2. The config will automatically use these instead of hardcoded defaults

**Set Environment Variables:**

```bash
# PowerShell - Set temporarily
$env:TEST_USERNAME = "your_email@example.com"
$env:TEST_PASSWORD = "your_password"

# Or permanently in the .env file in project root
```

---

### **Fix 2: Investigate /entries Endpoint**

#### Step 1: Test the endpoint manually
```bash
# Test GET /entries
curl -X GET "https://api.demoblaze.com/entries" \
  -H "Content-Type: application/json"

# Test POST /entries  
curl -X POST "https://api.demoblaze.com/entries" \
  -H "Content-Type: application/json" \
  -d "{}"
```

#### Step 2: Check if it's a GET endpoint
If GET works, update the load tests to use GET instead of POST.

**Files to check:**
- `tests/locustfile.py` - Line ~65-70 (browse_by_category task)

#### Step 3: Check API documentation
Visit: https://demoblaze.com/api_cloud.html (if available)

---

## 🔧 Implementation Steps

### **Step 1: Fix Authentication (IMMEDIATE)**

Create/update `.env` file in project root:

```env
# Demoblaze Test Credentials
TEST_USERNAME=load_test_01@example.com
TEST_PASSWORD=YourActualPassword123!

# Optional: Override API host if needed
TARGET_HOST=https://demoblaze.com
TARGET_API_HOST=https://api.demoblaze.com
```

**Why this works:**
- Config loads from `.env` first (via `load_dotenv()`)
- Falls back to hardcoded defaults only if `.env` not set
- Keeps secrets out of git (`.env` is in `.gitignore`)

---

### **Step 2: Verify Endpoints**

Run a quick diagnostic:

```bash
# PowerShell
cd d:\Automation\automation_locust_load

# Test both endpoints
python3 -c "
import requests

print('Testing /entries endpoint (POST)...')
try:
    r = requests.post('https://api.demoblaze.com/entries', json={}, timeout=5)
    print(f'POST /entries: {r.status_code}')
    if r.status_code == 405:
        print('  → Try GET instead')
except Exception as e:
    print(f'Error: {e}')

print('\nTesting /entries endpoint (GET)...')
try:
    r = requests.get('https://api.demoblaze.com/entries', timeout=5)
    print(f'GET /entries: {r.status_code}')
except Exception as e:
    print(f'Error: {e}')

print('\nTesting login endpoint...')
try:
    r = requests.post(
        'https://api.demoblaze.com/login',
        json={'username': 'test@test.com', 'password': 'test'},
        timeout=5
    )
    print(f'POST /login: {r.status_code}')
    print(f'Response: {r.json()}')
except Exception as e:
    print(f'Error: {e}')
"
```

---

### **Step 3: Update Test Files if Needed**

If /entries requires GET instead of POST:

**In `tests/locustfile.py`:**
```python
# Current (broken):
# self.client.post(f"{target.api_host}/entries", json={}, ...)

# Fixed (if endpoint expects GET):
# self.client.get(f"{target.api_host}/entries", ...)
```

---

## 📋 Verification Checklist

Before running tests again:

- [ ] Verified valid credentials exist on demoblaze.com
- [ ] Created `.env` file with TEST_USERNAME and TEST_PASSWORD
- [ ] Tested credentials manually: https://demoblaze.com/login
- [ ] Confirmed /entries endpoint HTTP method (GET vs POST)
- [ ] Ran quick diagnostic script above
- [ ] Confirmed API endpoints are responsive
- [ ] Run unit tests locally: `pytest tests/unit/ -v`
- [ ] Run smoke test first: `pytest tests/test_smoke_load.py`

---

## 🚀 Recovery Steps

### **Quick Fix (10 minutes)**

1. **Register test account:**
   ```bash
   curl -X POST "https://api.demoblaze.com/signup" \
     -H "Content-Type: application/json" \
     -d '{"username":"loadtest_unique_'"$(date +%s)"'@test.com","password":"LoadTest123!"}'
   ```

2. **Create `.env` file:**
   ```env
   TEST_USERNAME=your_new_user@test.com
   TEST_PASSWORD=LoadTest123!
   ```

3. **Run unit tests to verify:**
   ```bash
   cd d:\Automation\automation_locust_load
   python -m pytest tests/unit/test_auth.py -v
   ```

4. **Run smoke test:**
   ```bash
   locust -f tests/test_smoke_load.py --headless -u 5 -r 1 --run-time 1m
   ```

---

## 📊 Performance Impact

**Current Status:**
- ❌ **Login Success Rate:** 0% (407/407 failed)
- ❌ **/entries Success Rate:** ~17% (1755 failed across total requests)
- ❌ **Overall Test Result:** FAILED

**After Fixes:**
- ✅ Login Success Rate: >95% (expected)
- ✅ /entries Success Rate: >95% (expected)
- ✅ SLA Compliance: Within thresholds

---

## 🔍 Additional Diagnostics

### Check Current Credentials
```bash
# This will tell you what credentials are being used
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

test_username = os.getenv("TEST_USERNAME", "")
test_password = os.getenv("TEST_PASSWORD", "")

print(f"TEST_USERNAME set: {bool(test_username)}")
print(f"TEST_PASSWORD set: {bool(test_password)}")

if not test_username or not test_password:
    print("⚠️ Credentials not in .env - will use hardcoded defaults:")
    print("  Username: deltest@test.com")
    print("  Password: Password123#")
EOF
```

### Check .env File Location
```bash
# Should be in project root
Test-Path "d:\Automation\automation_locust_load\.env"

# Or create it
New-Item "d:\Automation\automation_locust_load\.env" -Force
```

---

## 📞 Next Steps

1. **Register test credentials** (5 min)
2. **Update `.env` file** (2 min)
3. **Run diagnostic script** (3 min)
4. **Verify login works** (2 min)
5. **Check /entries endpoint** (2 min)
6. **Run smoke test** (2 min)
7. **Run full load test** (5+ min)

**Total Time:** ~15-20 minutes to resolution

---

## ⚠️ Important Notes

- **Don't commit `.env` file** - It contains passwords
- **Keep `.env` in `.gitignore`** - Already configured
- **Use environment variables for CI/CD** - GitHub Secrets, not .env
- **Test credentials should be separate from production** - Always use test accounts

---

**Status:** Ready for implementation  
**Priority:** 🔴 HIGH - Tests cannot run without valid credentials  
**Owner:** You (implementation)
