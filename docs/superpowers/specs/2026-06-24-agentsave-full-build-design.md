# AgentSave — Full Build Design

**Date:** 2026-06-24
**Status:** Approved — ready for implementation planning
**Scope:** Four sub-projects that make every README claim true and provable

---

## Context

AgentSave v0.1.0 shipped to PyPI with a README that contained:
- Fake arXiv citations (removed in commit b9d35ea)
- Three companion repos referenced but not created (`agentsave-dashboard`, `agentsave-ui`, `agentsave-inferroute`)
- A 30% token reduction claim backed only by 2 synthetic benchmark tasks
- "Zero accuracy loss" with no measurement behind it
- E2E test badge claiming 30 tests that don't exist
- `app.agentsave.io` CLI references pointing to a service that doesn't exist

This design covers what to build so every claim is earned. All repos live under the `aks-builds` GitHub org. The product is **fully self-hosted** — customer data never leaves their environment.

---

## Build Order

| # | Sub-project | Repo | Unblocks |
|---|---|---|---|
| 0 | SDK benchmark suite + real framework tests | `agentsave` (this repo) | 30% claim, accuracy claim, real framework claims |
| 1 | Dashboard backend | `agentsave-dashboard` (new) | `agentsave login`, telemetry, UI |
| 2 | Dashboard UI | `agentsave-ui` (new) | screenshots, E2E badge |
| 3 | InferRoute | `agentsave-inferroute` (new) | Enterprise tier, 68% TTFT claim |

Sub-project 0 runs in parallel with Sub-project 1. Sub-project 2 requires Sub-project 1. Sub-project 3 is independent of all others.

---

## Sub-project 0 — SDK Benchmark Suite + Real Framework Tests

**Repo:** `agentsave` (additions to `benchmarks/` and `tests/adapters/`)

### Goal

Replace the 2-task synthetic benchmark with a proper suite that proves:
1. ~30% token reduction on representative multi-step agent tasks
2. Zero accuracy loss (correct answer rate is unchanged with vs. without AgentSave)
3. All five framework adapters work against real framework imports

### Benchmark Suite (`benchmarks/`)

```
benchmarks/
├── runner.py           ← CLI: python -m benchmarks.runner
├── tasks.py            ← 20+ tasks with goal, tool_outputs, ground_truth_answer
├── accuracy.py         ← compares agent answer to ground_truth (exact + fuzzy match)
├── report.py           ← writes results to BENCHMARKS.md
└── README.md           ← how to run, how to add tasks
```

**Task structure:**
```python
{
    "id": "tokyo-population",
    "goal": "What is the population of Tokyo?",
    "tool_outputs": [
        # relevant
        "Tokyo metropolitan area: 37.4 million people as of 2024.",
        # noise
        "Weather in Tokyo: sunny, 22°C.",
        "Current USDJPY rate: 149.3.",
        # relevant
        "Tokyo city proper: 13.96 million as of 2023.",
    ],
    "ground_truth": "37.4 million",   # fuzzy matched
}
```

**Runner flow:**
1. Run each task **without** AgentSave — record tokens used and answer
2. Run each task **with** AgentSave — record tokens used and answer
3. Compute: token reduction %, accuracy with/without (answers matching ground_truth)
4. Assert: token reduction ≥ 20% (CI floor — keeps the existing test passing), accuracy drop = 0% (hard gate — any accuracy regression fails the build). The 30% target is a tuning goal, not a CI gate; the runner reports the actual number so it can be tracked toward 30%.
5. Write results to `BENCHMARKS.md`

**Target:** ≥ 30% token reduction and 0% accuracy drop across the full task set. If the context filter threshold or early-exit parameters need tuning to hit 30%, tune them in `runner.py`'s default config — not in production defaults.

**Task set design (20+ tasks):**
- Mix of factual lookup, multi-hop reasoning, and tool-heavy tasks
- Each task has 3–6 tool outputs: 1–2 relevant, rest noise (realistic noise ratio)
- Ground truth answers are short strings (fuzzy-matched, case-insensitive)
- No API keys required — all tool outputs are pre-recorded

### Real Framework Integration Tests

**Replace** all mock-based adapter tests with tests that actually import the framework and use a deterministic fake LLM.

| Framework | Fake LLM approach |
|---|---|
| LangChain | `FakeListLLM` from `langchain_community.llms.fake` |
| LangGraph | Same `FakeListLLM`, real graph compilation via `StateGraph` |
| AutoGen | `UserProxyAgent` + `AssistantAgent` with `human_input_mode="NEVER"` and scripted replies |
| CrewAI | Real `Crew` + `Agent` with a local fake LLM backend |
| Smolagents | `FakeToolCallingModel` (built into smolagents test utilities) |

Each adapter test must:
- Import the real framework (no `MagicMock` for module/class names)
- Run a real invocation through the adapter
- Assert the supervisor callback actually fires (token counts increase, `last_run_state` populated)
- Assert the output matches what the fake LLM was scripted to return (proving no answer corruption)

These tests require the framework extras to be installed. They run in CI with `pip install "agentsave[all]"`.

### `agentsave login` — self-hosted connection

The current `login` command opens `https://app.agentsave.io/login`. Replace with self-hosted flow:

```
$ agentsave login
Dashboard URL [http://localhost:8000]: _
API key: _
✓ Connected. Telemetry enabled.
```

Implementation:
1. Prompt for URL (default `http://localhost:8000`) and API key
2. Hit `GET <url>/api/health` — confirm server is reachable (no auth)
3. Hit `GET <url>/api/billing` with `Authorization: Bearer <key>` — confirm auth works
4. On success: save `api_url` and `token` to `~/.agentsave/config.json`, set `telemetry: true`
5. On failure: print specific error (unreachable vs. auth rejected) and exit non-zero

Remove references to `app.agentsave.io` from `cli/main.py` entirely.

---

## Sub-project 1 — `agentsave-dashboard` (Backend)

**Repo:** `aks-builds/agentsave-dashboard` (new)
**Install:** `pip install agentsave-dashboard`
**Start:** `agentsave-dashboard serve [--host 0.0.0.0] [--port 8000]`

### Architecture

```
agentsave-dashboard/
├── agentsave_dashboard/
│   ├── main.py             ← FastAPI app factory
│   ├── db.py               ← SQLite init, aiosqlite, migrations
│   ├── auth.py             ← Bearer token middleware (SHA-256 key lookup)
│   ├── license.py          ← JWT RS256 validation, tier resolution, feature flags
│   ├── routers/
│   │   ├── events.py       ← POST /api/events
│   │   ├── metrics.py      ← GET  /api/metrics
│   │   ├── tokens.py       ← GET  /api/tokens
│   │   ├── runs.py         ← GET  /api/runs
│   │   ├── billing.py      ← GET  /api/billing
│   │   ├── health.py       ← GET  /api/health  (no auth)
│   │   └── test_utils.py   ← DELETE /api/test/reset (AGENTSAVE_TEST_MODE=1 only)
│   ├── services/
│   │   ├── aggregator.py   ← metrics queries over SQLite
│   │   └── retention.py    ← background task: delete runs past tier limit
│   └── cli.py              ← agentsave-dashboard serve command
├── scripts/
│   └── generate_license.py ← internal: issue license JWTs (not customer-facing)
├── tests/                  ← 47 tests
│   ├── test_events.py
│   ├── test_metrics.py
│   ├── test_billing.py
│   ├── test_license.py
│   ├── test_auth.py
│   ├── test_retention.py
│   └── test_health.py
└── pyproject.toml
```

### First-Run Flow

On first `agentsave-dashboard serve`:
1. Create `~/.agentsave-dashboard/` directory
2. Generate a random API key (`ask-` + 32 hex chars), store its SHA-256 hash in the `api_keys` table
3. Print to stdout:
   ```
   AgentSave Dashboard running at http://localhost:8000
   API key: ask-a1b2c3d4...  ← save this, shown once
   ```
4. On subsequent starts, the key is already in the DB — not re-printed

### Data Layer

**SQLite schema:**

```sql
CREATE TABLE runs (
    run_id        TEXT PRIMARY KEY,
    framework     TEXT NOT NULL,
    model_name    TEXT NOT NULL,
    tokens_before INTEGER NOT NULL,
    tokens_after  INTEGER NOT NULL,
    task_success  INTEGER NOT NULL,   -- 0 or 1
    timestamp     TEXT NOT NULL       -- ISO 8601 UTC
);

CREATE TABLE api_keys (
    key_hash   TEXT PRIMARY KEY,      -- SHA-256 of raw key
    label      TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL               -- license_key stored here
);
```

**Retention:** `retention.py` runs as a FastAPI `lifespan` background task, hourly. Deletes rows from `runs` where `timestamp < now - tier_history_days`. This is hard enforcement — rows are gone, not hidden.

**Test isolation:** When `AGENTSAVE_TEST_MODE=1`, the app uses an in-memory SQLite DB (`:memory:`) and registers `DELETE /api/test/reset`. This env var is never set in production — the endpoint does not exist otherwise.

### API Surface

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/health` | None | `{ "status": "ok", "version": "0.1.0" }` |
| `POST` | `/api/events` | Bearer | Receive `SavingsEvent` from SDK |
| `GET` | `/api/metrics` | Bearer | Aggregate stats (total savings, success rate, by-framework) |
| `GET` | `/api/tokens` | Bearer | Token trend data, time-bucketed, for charts |
| `GET` | `/api/runs` | Bearer | Paginated run history |
| `GET` | `/api/billing` | Bearer | Current tier, feature flags object |
| `DELETE` | `/api/test/reset` | None | Wipe DB — only when `AGENTSAVE_TEST_MODE=1` |

**`GET /api/billing` response:**
```json
{
  "tier": "pro",
  "org": "Acme Corp",
  "seats_allowed": 5,
  "seats_used": 2,
  "expires_at": "2027-06-23",
  "features": {
    "history_days": 90,
    "unlimited_projects": true,
    "webhook_alerts": true,
    "csv_export": true,
    "sso_saml": false,
    "audit_logs": false,
    "inferroute": false
  }
}
```

UI reads `features` to show/hide functionality. No enforcement logic in the frontend.

### License Key Model

**Format:** JWT signed with RS256 (RSA).

**Payload:**
```json
{
  "tier": "pro",
  "seats": 5,
  "exp": 1785000000,
  "iss": "agentsave",
  "org": "Acme Corp",
  "email": "admin@acme.com"
}
```

**Public key:** embedded in the package at `agentsave_dashboard/keys/public.pem` at build time. No network call for validation — fully offline.

**Tier resolution:**

| State | Result |
|---|---|
| No license key | Free tier |
| Valid, not expired | Tier from JWT payload |
| Expired | Free tier + warning banner via `/api/billing` `expired: true` |
| Invalid signature | Free tier, silent |

**Customer flow:** purchase → `scripts/generate_license.py --tier pro --seats 5 --org "Acme" --email admin@acme.com --days 365` → email JWT → customer pastes into dashboard Settings page or passes as `agentsave-dashboard serve --license-key <jwt>`.

**Feature gates by tier:**

| Feature | Free | Pro | Enterprise |
|---|---|---|---|
| History retention | 7 days | 90 days | 1 year |
| Seats (API keys) | 1 | 5 | Custom |
| Webhook alerts | ✗ | ✓ | ✓ |
| CSV export | ✗ | ✓ | ✓ |
| SSO / SAML | ✗ | ✗ | ✓ |
| Audit logs | ✗ | ✗ | ✓ |
| InferRoute sidecar | ✗ | ✗ | ✓ |

---

## Sub-project 2 — `agentsave-ui` (Dashboard UI)

**Repo:** `aks-builds/agentsave-ui` (new)
**Stack:** Next.js 16, TypeScript, Tailwind CSS
**Config:** `NEXT_PUBLIC_API_URL=http://localhost:8000` (env var pointing at Sub-project 1)

### Pages and Components

Matches the 8 screenshots in `docs/screenshots/` exactly:

| Route | Screenshot | Components |
|---|---|---|
| `/` | 01-overview.png | StatCard ×4, TokenSavingsChart, FrameworkBreakdown, RecentRuns, LiveActivity |
| `/analytics` | 02-analytics.png | TrendChart (area/line/bar toggle) |
| `/runs` | 03-runs.png | RunsTable (framework badges, reduction %) |
| `/cost` | 04-cost-projector.png | CostProjector (interactive sliders) |
| `/activity` | 05-activity-feed.png | ActivityFeed (real-time stream) |
| `/heatmap` | 06-heatmap.png | ActivityHeatmap (GitHub-style grid) |
| `⌘K` | 07-command-palette.png | CommandPalette (navigation + actions) |
| `/billing` | 08-billing.png | BillingTiers (reads `GET /api/billing`, shows current plan) |

### Playwright E2E Tests (`tests/e2e/`)

Three layers — all Playwright, no separate test framework:

**Layer 1 — API (no browser, `request` context):**
Tests the dashboard backend directly. Requires the backend running at `TEST_API_URL`.

- `POST /api/events` with valid key → 200, run appears in `GET /api/runs`
- `POST /api/events` with invalid key → 401
- Token reduction % is correctly computed from `tokens_before` / `tokens_after`
- `GET /api/billing` returns Free tier when no license key
- `GET /api/billing` returns Pro features with valid Pro license JWT
- `GET /api/billing` returns `expired: true` with expired JWT, features downgraded to Free
- `GET /api/billing` returns Free tier with tampered JWT (bad signature)
- Retention: seed runs older than 7 days → retention job runs → `GET /api/runs` excludes them (Free tier)
- Retention: same runs with Pro license → still present (90-day window)
- `GET /api/health` returns 200 with no auth
- `DELETE /api/test/reset` resets DB state between tests

**Layer 2 — Browser (full UI):**
Both backend and UI running. Uses `DELETE /api/test/reset` to seed known state before each test.

- Dashboard: stat cards show correct totals from seeded runs
- Dashboard: "23 runs · live" indicator present when backend is running
- Analytics: trend chart renders, area/line/bar toggle switches chart type
- Runs table: all seeded runs present, framework badge colour matches framework
- Runs table: reduction % column matches `(tokens_before - tokens_after) / tokens_before`
- Cost projector: moving sliders updates projected monthly savings
- Activity feed: posting a new run via API causes it to appear within 2s
- Heatmap: cells lit for seeded run timestamps, empty cells for days with no runs
- Command palette: `⌘K` opens palette, typing "analytics" navigates to `/analytics`
- Billing page: Free tier shows "Current plan" button disabled
- Billing page: Pro license JWT in backend → Pro card shows as current, Enterprise shows "Contact sales"
- Settings: adding a second API key (Pro tier) succeeds; Free tier rejects a second key with 403
- All pages: dark theme, no layout shift, no console errors

**Layer 3 — Full Stack (SDK → UI):**
Python subprocess runs real SDK code. Playwright verifies the result in the UI.

- `agentsave.loop()` raw run → event appears in runs table with `framework: raw`
- LangChain adapter run (fake LLM) → appears with `framework: langchain`, reduction % > 0
- CrewAI adapter run (fake LLM) → appears with `framework: crewai`
- AutoGen adapter run (fake LLM) → appears with `framework: autogen`
- LangGraph adapter run (fake LLM) → appears with `framework: langgraph`
- Smolagents adapter run (fake LLM) → appears with `framework: smolagents`
- Budget gate triggered (budget=1) → run shows `task_success: false` in UI
- Telemetry disabled (`agentsave config set telemetry off`) → no new run appears in UI

**Total target: ~70 tests.** README E2E badge updated to actual count once they pass.

---

## Sub-project 3 — `agentsave-inferroute` (Enterprise Sidecar)

**Repo:** `aks-builds/agentsave-inferroute` (new)
**Tier:** Enterprise only — feature-gated via `features.inferroute` from `/api/billing`
**Delivery:** Docker image `agentsave/inferroute:latest`

### Purpose

PPD (append-prefill decode) routing for multi-turn agent workloads. Sits in front of a customer's vLLM or SGLang cluster. Routes Turn 1 requests through standard prefill-decode, Turn 2+ through append-prefill to reuse the KV cache, reducing TTFT.

**Target: ~68% Turn 2+ TTFT reduction** — this is a design target based on the PPD technique, not yet measured. Will be benchmarked and reported in `BENCHMARKS.md` once built.

### Architecture

```
agentsave-inferroute/
├── inferroute/
│   ├── classifier.py     ← Turn 1 vs Turn 2+ detection (conversation history length)
│   ├── router.py         ← PPD scoring, route decision
│   ├── proxy.py          ← HTTP proxy: forward request to vLLM/SGLang
│   └── adapters/
│       ├── vllm.py       ← vLLM-specific request format
│       └── sglang.py     ← SGLang-specific request format
├── Dockerfile
├── docker-compose.yml    ← example: InferRoute + vLLM together
└── tests/                ← 59 tests
```

**Deploy:**
```bash
docker run -d -p 8080:8080 \
  -e BACKEND_URL=http://your-vllm:8000 \
  -e BACKEND_TYPE=vllm \
  -e AGENTSAVE_LICENSE=<enterprise-jwt> \
  agentsave/inferroute:latest
```

License JWT validated at startup — if not Enterprise tier, InferRoute refuses to start.

---

## Cross-cutting: README and Badge Updates

As each sub-project ships, update the README:

| Event | README change |
|---|---|
| Sub-project 0: benchmark hits 30% | Update `BENCHMARKS.md`, change "targeting ~30%" to "~30% measured on GAIA" |
| Sub-project 0: accuracy proven | Add "zero accuracy loss measured" to `BENCHMARKS.md` and tagline |
| Sub-project 0: real framework tests pass | Change "all tested" to "all integration-tested" |
| Sub-project 1 ships | Remove "in development" from dashboard section |
| Sub-project 2 ships + E2E pass | Update E2E badge to actual count |
| Sub-project 3 ships | Remove "in development" from InferRoute section, add TTFT benchmark result |

---

## What the Newbie Walkthrough Looks Like After All Four Ship

```bash
# 1. Install SDK
pip install agentsave

# 2. Wrap your agent
from agentsave import supervise
agent = supervise(your_agent)

# 3. Install + start dashboard
pip install agentsave-dashboard
agentsave-dashboard serve
# → API key: ask-a1b2c3...
# → running at http://localhost:8000

# 4. Connect SDK to dashboard
agentsave login
# → Dashboard URL [http://localhost:8000]: (enter)
# → API key: ask-a1b2c3...
# → ✓ Connected. Telemetry enabled.

# 5. Run your agent — savings tracked automatically
agent.invoke({"input": "Research the top 5 Python web frameworks"})

# 6. View dashboard
cd agentsave-ui && npm install && npm run dev
# → http://localhost:3000

# (Enterprise) 7. Deploy InferRoute
docker run -d -p 8080:8080 \
  -e BACKEND_URL=http://your-vllm:8000 \
  -e AGENTSAVE_LICENSE=<enterprise-jwt> \
  agentsave/inferroute:latest
```

Every step above either works today (steps 1–2) or will work once the corresponding sub-project ships. Nothing points to a non-existent hosted service.
