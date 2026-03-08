# Load Test Fix Implementation Guide

**Status:** 🔴 CRITICAL - Tests cannot run  
**Created:** March 8, 2026  
**Priority:** HIGH - Complete within 1 hour

---

## 📋 Quick Summary

Your load tests are failing with **2,162 errors**:
- **407 Login Failures** → Invalid credentials (`deltest@test.com` doesn't exist or has wrong password)
- **1,755 HTTP 405 Errors** → `/entries` endpoint being called incorrectly

---

## ✅ Step-by-Step Fix (15 minutes)

### **Step 1: Investigate API Endpoints (3 minutes)**

Open PowerShell and run the investigation script:

```powershell
cd d:\Automation\automation_locust_load
python investigate_api.py
```

**This will tell you:**
- ✓ If Demoblaze API is up and running
- ✓ What credentials work (if any)
- ✓ Whether `/entries` expects GET or POST
- ✓ What other endpoints are working

**Expected output:**
```
✓ API is reachable: HTTP 200
✓ Login successful! Token: eyJhbGc...
✓ Endpoint accepts GET
```

---

### **Step 2: Create Valid Test Credentials (3 minutes)**

**Option A: Use the public demo account** (Easiest, if it works)
```powershell
# Just create .env with public credentials
@"
TEST_USERNAME=demo@demoblaze.com
TEST_PASSWORD=demo
"@ | Out-File -Encoding UTF8 .env
```

**Option B: Create your own test account** (Recommended for reliability)
1. Go to: https://demoblaze.com/index.html#signup
2. Create account:
   - Email: `loadtest_$(date +%s)@example.com`
   - Password: Any string (e.g., `LoadTest123!`)
3. Save to `.env`:
   ```powershell
   @"
   TEST_USERNAME=your_email@example.com
   TEST_PASSWORD=your_password
   "@ | Out-File -Encoding UTF8 .env
   ```

**Verify:**
```powershell
# Check .env was created
cat .env

# Output should show:
# TEST_USERNAME=your_email@example.com
# TEST_PASSWORD=your_password
```

---

### **Step 3: Fix /entries Endpoint (5 minutes)**

Based on the investigation script output, apply one fix:

#### **If GET works (most likely):**

Replace all `POST /entries` with `GET /entries`:

**File: `d:\Automation\automation_locust_load\tests\locustfile.py`**

```python
# CHANGE THIS (Line 152-157):
@task(3)
def get_product_entries(self) -> None:
    """POST /entries — retrieve all product listings."""
    with self.client.post(
        f"{target.api_host}/entries",
        catch_response=True,
        name="POST /entries",
    ) as r:

# TO THIS:
@task(3)
def get_product_entries(self) -> None:
    """GET /entries — retrieve all product listings."""
    with self.client.get(
        f"{target.api_host}/entries",
        catch_response=True,
        name="GET /entries",
    ) as r:
```

**Also in: `d:\Automation\automation_locust_load\tests\test_smoke_load.py`**

```python
# CHANGE (lines 91-101):
def smoke_entries(self) -> None:
    """Smoke: POST /entries — fetch product listings."""
    with self.client.post(
        f"{target.api_host}/entries",
        ...
        name="Smoke: POST /entries",
```

# TO THIS:
def smoke_entries(self) -> None:
    """Smoke: GET /entries — fetch product listings."""
    with self.client.get(
        f"{target.api_host}/entries",
        ...
        name="Smoke: GET /entries",
```

---

### **Step 4: Test Locally (3 minutes)**

```powershell
cd d:\Automation\automation_locust_load

# Install dependencies (1 time)
pip install -r requirements.txt
python -m playwright install

# Test 1: Run unit tests to verify auth works
python -m pytest tests/unit/test_auth.py -v

# Test 2: Run smoke test (5-20 users for 1 minute)
locust -f tests/test_smoke_load.py --headless -u 5 -r 1 --run-time 1m
```

**Expected result:**
```
Name                Status   Count
GET /               pass     23
POST /bycat         pass     18
GET /entries        pass     16    ← Changed from POST
POST /addtocart     pass     12
...
Failed:  0
```

---

## 🔍 If investigation script finds different issues

### **If Investigation Script shows:**

#### **"No valid credentials found"**
→ Go to https://demoblaze.com and manually create an account
→ Use those credentials in `.env`

#### **"POST_WITH_PARAMS works for /entries"**
→ Change POST calls to include empty JSON body:
```python
# Change this:
self.client.post(f"{target.api_host}/entries", catch_response=True)

# To this:
self.client.post(f"{target.api_host}/entries", json={}, catch_response=True)
```

#### **"Neither GET nor POST works for /entries"**
→ The endpoint may be removed or requires authentication
→ Option 1: Remove the `get_product_entries()` task
→ Option 2: Use different endpoint (e.g., `/bycat`)

---

## 📝 Important Files to Update

| File | Issue | Fix |
|------|-------|-----|
| `.env` | Create this file | Add TEST_USERNAME and TEST_PASSWORD |
| `tests/locustfile.py` | POST /entries | Change to GET /entries |
| `tests/test_smoke_load.py` | POST /entries | Change to GET /entries |
| `tests/test_api_performance.py` | POST /entries | Change to GET /entries (lines 90~) |
| `tests/test_endurance.py` | POST /entries | Change to GET /entries |

---

## 🚀 Quick Commands Reference

```powershell
# 1. Run investigation script
python investigate_api.py

# 2. Create .env file
@"
TEST_USERNAME=your_email@example.com
TEST_PASSWORD=your_password
"@ | Out-File -Encoding UTF8 .env

# 3. Test local smoke test (5 users, 1 minute)
locust -f tests/test_smoke_load.py --headless -u 5 -r 1 --run-time 1m

# 4. Run unit tests
python -m pytest tests/unit/test_auth.py -v

# 5. Run full test suite once fixed
python -m pytest tests/ -v

# 6. Commit fixes
git add .
git commit -m "fix: update test credentials and fix /entries endpoint"
git push origin main
```

---

## ❓ Troubleshooting

### **Investigation script hangs**
- Check internet connection
- Check if demoblaze.com is up (try in browser)
- Increase timeout: Edit investigate_api.py timeout=10

### **Login test fails with "Wrong password"**
- Credentials don't work
- Create new test account via https://demoblaze.com/index.html#signup
- Update .env with new credentials

### **Tests still fail after fixing /entries**
- Check if other endpoints changed (POST /bycat, etc.)
- Run investigation script to test all endpoints
- Check Demoblaze status page

### **Can't find test files to edit**
```powershell
# Find files to update
grep -r "POST /entries" tests/
grep -r "get_product_entries" tests/
```

---

## ✅ Verification Checklist

Before committing fixes:

- [ ] .env file exists with TEST_USERNAME and TEST_PASSWORD
- [ ] .env is NOT committed to git (check .gitignore)
- [ ] `/entries` endpoint calls changed to GET
- [ ] Unit tests pass: `pytest tests/unit/test_auth.py -v`
- [ ] Smoke test passes: `locust -f tests/test_smoke_load.py ...`
- [ ] No 407 errors in test output
- [ ] No 405 errors in test output
- [ ] Ready to commit: `git status` shows only modified python files
- [ ] Commit message is clear: "fix: update test credentials and fix /entries endpoint"

---

## 📞 Next Steps

1. **NOW:** Run `python investigate_api.py`
2. **THEN:** Create `.env` file with valid credentials
3. **THEN:** Fix `/entries` endpoint based on investigation results
4. **THEN:** Test locally with smoke test
5. **THEN:** Commit and push
6. **THEN:** Verify CI passes

---

## 🎯 Success Criteria

After completing these steps:
- ✅ Zero login failures (407 errors gone)
- ✅ Zero HTTP 405 errors (405 errors gone)
- ✅ Smoke tests complete successfully
- ✅ Load tests run and complete with success exit code
- ✅ CI/CD pipeline is green ✓

---

**Estimated Time:** 15 minutes  
**Difficulty:** Easy (5/10)  
**Impact:** CRITICAL (enables all load testing)
