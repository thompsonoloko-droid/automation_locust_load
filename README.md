# automation_locust_load

[![CI Workflow ](https://github.com/thompsonoloko-droid/automation_locust_load/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/thompsonoloko-droid/automation_locust_load/actions/workflows/ci.yml)
[![Locust Version](https://img.shields.io/badge/Locust-2.43.3-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Production-ready Locust performance test framework** targeting the [Demoblaze](https://demoblaze.com) e-commerce platform. Covers smoke, API, spike, endurance and full checkout-flow load scenarios with SLA gating, CI/CD integration and comprehensive pytest unit/integration test coverage.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Test Scenarios](#test-scenarios)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [CI/CD Workflows](#cicd-workflows)
- [SLA Thresholds](#sla-thresholds)
- [Reporting](#reporting)
- [Security](#security)

---

## Project Structure

```
automation_locust_load/
├── common/                     # Shared modules
│   ├── __init__.py
│   ├── auth.py                 # AuthManager — handles login & session cookies
│   └── config.py               # Typed config via env vars (frozen dataclasses)
├── tests/
│   ├── locustfile.py           # Main browsing & cart flow (default)
│   ├── test_api_performance.py # Pure API endpoint performance tests
│   ├── test_spike_load.py      # Spike shape — sudden user surge
│   ├── test_endurance.py       # Soak / endurance shape (30–60 min)
│   ├── test_smoke_load.py      # Quick 5-user smoke pass
│   ├── test_checkout_flow.py   # Sequential full purchase funnel
│   ├── unit/                   # pytest unit tests (no network I/O)
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_config.py
│   │   └── test_locust_users.py
│   └── integration/            # pytest integration tests (real HTTP)
│       └── test_endpoint_smoke.py
├── reports/                    # Generated test artefacts (.gitignored)
├── .github/
│   └── workflows/
│       ├── ci.yml              # PR / push pipeline (lint + unit + smoke load)
│       ├── nightly-endurance.yml
│       └── manual-load-test.yml
├── locust.conf                 # Default Locust CLI configuration
├── pyproject.toml              # Project metadata, tool config
├── requirements.txt            # Pinned dependencies
└── .env.example                # Credential template
```

---

## Requirements

- **Python 3.11+** (tested on 3.11, 3.12, 3.14)
- **Locust 2.43.3+** (cross-browser performance testing framework)
- **pytest 9.0.2+** (unit + integration testing)

```bash
# Install all dependencies
pip install -r requirements.txt
```

---

## Quick Start

### 1 — Clone & install

```bash
git clone https://github.com/thompsonoloko-droid/automation_locust_load.git
cd automation_locust_load
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 2 — Configure credentials (optional for smoke tests)

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```.env
TARGET_HOST=https://demoblaze.com
TARGET_API_HOST=https://api.demoblaze.com
TEST_USERNAME=your-registered-email@example.com
TEST_PASSWORD=YourPassword123!
```

> **Never commit `.env`** — it is listed in `.gitignore`.
>
> **Note**: Smoke and API performance tests run even without credentials (informational only).
> For authenticated endpoints (add-to-cart, checkout), provide valid Demoblaze credentials.

### 3 — Run the default scenario (interactive UI)

```bash
locust -f tests/locustfile.py
# Open http://localhost:8089 in your browser
```

---

## Test Scenarios

| File | Scenario | Shape | Recommended Users |
|------|----------|-------|-------------------|
| `tests/locustfile.py` | Browse + cart + order | Constant | 20–100 |
| `tests/test_smoke_load.py` | Endpoint availability | Constant | 5 |
| `tests/test_api_performance.py` | API SLA validation | Constant | 10–50 |
| `tests/test_spike_load.py` | Sudden load spike | Custom (SpikeLoadShape) | auto |
| `tests/test_endurance.py` | Soak / memory leak | Custom (EnduranceLoadShape) | auto |
| `tests/test_checkout_flow.py` | Full purchase funnel | SequentialTaskSet | 5–20 |

---

## Configuration

All settings are driven by environment variables (see `common/config.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_HOST` | `https://demoblaze.com` | HTML SPA base URL (frontend pages) |
| `TARGET_API_HOST` | `https://api.demoblaze.com` | REST API base URL (POST /login, /entries, /bycat, etc.) |
| `TEST_USERNAME` | *(empty)* | Login username / email |
| `TEST_PASSWORD` | *(empty)* | Login password |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `CONNECT_TIMEOUT` | `10` | TCP connection timeout (seconds) |
| `LOCUST_USERS` | `50` | Default virtual user count |
| `LOCUST_SPAWN_RATE` | `5` | Users spawned per second |
| `LOCUST_RUN_TIME` | `5m` | Default test duration |

---

## Running Tests

### Load test scenarios

```bash
# Smoke test (5 users, 30s)
locust -f tests/test_smoke_load.py --headless -u 5 -r 1 --run-time 30s

# Main browsing flow (50 users, 3 min)
locust -f tests/locustfile.py --headless -u 50 -r 5 --run-time 3m

# API performance (20 users, 2 min)
locust -f tests/test_api_performance.py --headless -u 20 -r 2 --run-time 2m

# Spike test (auto-shaped, 4 min total)
locust -f tests/test_spike_load.py --headless --run-time 4m

# Checkout funnel (10 users, 3 min)
locust -f tests/test_checkout_flow.py --headless -u 10 -r 1 --run-time 3m

# Endurance / soak (20 users, 30 min)
locust -f tests/test_endurance.py --headless -u 20 -r 2 --run-time 30m
```

### Unit tests only (no network)

```bash
pytest tests/unit/ -v
```

### Integration smoke tests (real HTTP)

```bash
pytest tests/integration/ -m integration -v
```

### Full test suite

```bash
pytest tests/unit/ tests/integration/ -v --cov=common --cov-report=html
```

---

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push / PR / daily schedule | Lint → unit tests → smoke load |
| `nightly-endurance.yml` | Nightly 02:00 UTC | 10-minute soak test |
| `manual-load-test.yml` | Manual dispatch | On-demand load run with configurable params |

### Required GitHub Secrets

Set these under **Settings → Secrets and Variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `TEST_USERNAME` | Demoblaze login email |
| `TEST_PASSWORD` | Demoblaze password |

---

## SLA Thresholds

The test framework enforces SLAs via event hooks in each locustfile.
If thresholds are breached, `environment.process_exit_code = 1` is set.
In CI, **smoke and API performance tests are informational** (`continue-on-error: true`),
while **lint and unit tests are hard gates**.

### Smoke Load Test SLA

| Metric | Default SLA |
|--------|-------------|
| Max failure rate | ≤ 10 % |

*(Allows 10% tolerance: login fails without credentials, but endpoints are reachable)*

### API Performance & Production Tests

| Metric | Default SLA |
|--------|-------------|
| Max failure rate | ≤ 1 % |
| Max response time (p95) | ≤ 2000 ms |

Configure failures per test file (see `on_test_stop()` event hooks).

---

## Reporting

Locust generates reports automatically:

```bash
# With HTML + CSV output
locust -f tests/locustfile.py --headless -u 20 -r 2 --run-time 2m \
  --html reports/report.html \
  --csv reports/results
```

Reports are stored in `reports/` (git-ignored). CI artefacts are uploaded
to GitHub Actions with 14–30 day retention.

---

## Architecture Notes

### Dual Host Configuration

Demoblaze exposes two distinct origins:

- **`TARGET_HOST` = `https://demoblaze.com`**
  - Serves HTML SPA pages (`/`, `/index.html`, `/prod.html`, `/cart.html`)
  - Used for page load and rendering tests

- **`TARGET_API_HOST` = `https://api.demoblaze.com`**
  - Serves REST API endpoints (`/login`, `/entries`, `/bycat`, `/addtocart`, etc.)
  - All Locust `POST` calls to API endpoints use the API host
  - Authentication (`POST /login`) requires the API host

### Authentication Flow

1. `AuthManager.login()` sends `POST {api_host}/login` with username/password
2. Server responds with `Auth_token` in JSON payload
3. Browser automatically receives `user` session cookie (HTTP-Only)
4. Subsequent cart operations use the `user` cookie

### Load Test Scenarios

Each test file targets a different load profile:

- **Locustfile (Default)**: Realistic browsing mix (homepage, categories, products, cart)
- **Smoke Load**: Quick validation of endpoint reachability (5 users, 30s)
- **API Performance**: Isolated REST API SLA validation (10–50 users)
- **Spike Load**: Sudden surge from 10 → 100 → 25 users (resilience test)
- **Endurance**: Sustained soak test (20 users, 30 min) for memory leaks
- **Checkout Flow**: Sequential full purchase funnel (login → browse → add → pay)

---

## Security

- **Credentials** stored in `.env` file (git-ignored, never committed)
- **CI secrets** injected via GitHub Secrets at runtime
- **No sensitive data** in `pyproject.toml`, code, or version control
- **Test card numbers** are well-known public test values only
- **Environment variable parsing** via `python-dotenv` at module load time

---

## Code Quality

All code is validated before merge:

```bash
# Format with Black (line length 88)
black .

# Lint with Ruff (E, F, W, I, N, UP, B rules)
ruff check .

# Sort imports with isort (Black-compatible profile)
isort .

# Type hints with mypy (strict mode)
mypy .

# Unit tests with pytest (≥80% coverage required)
pytest tests/unit/ --cov=common --cov-fail-under=80
```

All checks pass in CI before merging to `main`.
