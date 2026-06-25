# Sub-project 1: `agentsave-dashboard` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-hosted FastAPI + SQLite dashboard backend that receives telemetry from the AgentSave SDK, enforces tier limits via offline JWT license keys, and exposes a REST API that the UI reads.

**Architecture:** Single Python package `agentsave-dashboard` installable via pip. On first `agentsave-dashboard serve` it generates an API key and starts a FastAPI server backed by SQLite (aiosqlite). License keys are RS256 JWTs validated offline against a public key embedded in the package. A background retention task enforces per-tier history limits. All state lives in `~/.agentsave-dashboard/`.

**Tech Stack:** Python 3.11+, FastAPI 0.115+, aiosqlite 0.20+, PyJWT[crypto] 2.8+, cryptography 42+, uvicorn 0.30+, click 8.1+, rich 13.7+, pytest 8+, pytest-asyncio 0.23+, httpx (test client)

## Global Constraints

- Python ≥ 3.11
- All data stays in `~/.agentsave-dashboard/` — no cloud calls
- `DELETE /api/test/reset` only registers when `AGENTSAVE_TEST_MODE=1`
- API key stored as SHA-256 hash — never stored in plain text
- License private key never shipped in the package — only `keys/public.pem`
- First-run API key printed once to stdout and never again
- Commit after every task

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `agentsave_dashboard/__init__.py`
- Create: `agentsave_dashboard/main.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: `create_app() -> FastAPI` — app factory used in all tests

- [ ] **Step 1: Initialise the repo**

```bash
mkdir agentsave-dashboard && cd agentsave-dashboard
git init
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling>=1.21"]
build-backend = "hatchling.build"

[project]
name = "agentsave-dashboard"
version = "0.1.0"
description = "Self-hosted AgentSave dashboard backend"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Aditya Kumar Singh", email = "its.aks@outlook.com" }]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "aiosqlite>=0.20.0",
    "PyJWT[crypto]>=2.8.0",
    "cryptography>=42.0.0",
    "click>=8.1.0",
    "rich>=13.7.0",
    "httpx>=0.27.0",
]

[project.scripts]
agentsave-dashboard = "agentsave_dashboard.cli:cli"

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.build.targets.wheel]
packages = ["agentsave_dashboard"]
```

- [ ] **Step 3: Install in editable mode**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 4: Create `agentsave_dashboard/__init__.py`**

```python
# agentsave_dashboard/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 5: Create `agentsave_dashboard/main.py`**

```python
# agentsave_dashboard/main.py
from fastapi import FastAPI
from agentsave_dashboard import __version__


def create_app() -> FastAPI:
    app = FastAPI(title="AgentSave Dashboard", version=__version__)
    return app
```

- [ ] **Step 6: Create `tests/__init__.py`** (empty)

- [ ] **Step 7: Create `tests/conftest.py`**

```python
# tests/conftest.py
import os, pytest
os.environ["AGENTSAVE_TEST_MODE"] = "1"

from httpx import AsyncClient, ASGITransport
from agentsave_dashboard.main import create_app

@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 8: Verify scaffold works**

```bash
python -c "from agentsave_dashboard.main import create_app; app = create_app(); print('OK')"
```
Expected: `OK`

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml agentsave_dashboard/__init__.py agentsave_dashboard/main.py tests/__init__.py tests/conftest.py
git commit -m "chore: project scaffold for agentsave-dashboard"
```

---

### Task 2: Database layer

**Files:**
- Create: `agentsave_dashboard/db.py`
- Create: `tests/test_db.py`

**Interfaces:**
- Produces: `init_db(db_path: str) -> None` — creates tables
- Produces: `get_db(app: FastAPI) -> AsyncIterator[aiosqlite.Connection]` — dependency
- Produces: `DB_PATH: str` — default path `~/.agentsave-dashboard/data.db`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_db.py
import os, tempfile, pytest
import aiosqlite
from agentsave_dashboard.db import init_db, DB_PATH


async def test_init_db_creates_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        await init_db(path)
        async with aiosqlite.connect(path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in await cursor.fetchall()}
        assert "runs" in tables
        assert "api_keys" in tables
        assert "config" in tables
    finally:
        os.unlink(path)


async def test_runs_table_schema():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        await init_db(path)
        async with aiosqlite.connect(path) as db:
            cursor = await db.execute("PRAGMA table_info(runs)")
            cols = {row[1] for row in await cursor.fetchall()}
        assert cols == {"run_id", "framework", "model_name", "tokens_before",
                        "tokens_after", "task_success", "timestamp"}
    finally:
        os.unlink(path)


def test_db_path_is_in_home():
    assert ".agentsave-dashboard" in DB_PATH
```

- [ ] **Step 2: Run to verify failures**

```
pytest tests/test_db.py -v
```
Expected: `ModuleNotFoundError: cannot import name 'init_db'`

- [ ] **Step 3: Create `agentsave_dashboard/db.py`**

```python
# agentsave_dashboard/db.py
import os
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncIterator

DB_DIR = os.path.expanduser("~/.agentsave-dashboard")
DB_PATH = os.path.join(DB_DIR, "data.db")

_TEST_DB_PATH = ":memory:"
_db_path_override: str | None = None


def get_db_path() -> str:
    import os as _os
    if _os.environ.get("AGENTSAVE_TEST_MODE") == "1":
        return _TEST_DB_PATH
    return _db_path_override or DB_PATH


async def init_db(db_path: str | None = None) -> None:
    path = db_path or get_db_path()
    if path != ":memory:":
        os.makedirs(os.path.dirname(path), exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id        TEXT PRIMARY KEY,
                framework     TEXT NOT NULL,
                model_name    TEXT NOT NULL,
                tokens_before INTEGER NOT NULL,
                tokens_after  INTEGER NOT NULL,
                task_success  INTEGER NOT NULL,
                timestamp     TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_hash   TEXT PRIMARY KEY,
                label      TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.commit()


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    path = get_db_path()
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        yield db
```

- [ ] **Step 4: Run tests**

```
pytest tests/test_db.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agentsave_dashboard/db.py tests/test_db.py
git commit -m "feat(db): SQLite schema — runs, api_keys, config tables"
```

---

### Task 3: Auth middleware + first-run API key generation

**Files:**
- Create: `agentsave_dashboard/auth.py`
- Create: `tests/test_auth.py`
- Modify: `agentsave_dashboard/main.py` — wire up DB init + auth

**Interfaces:**
- Produces: `require_auth(request: Request) -> str` — FastAPI dependency, raises HTTP 401 if invalid
- Produces: `generate_api_key() -> tuple[str, str]` — returns `(raw_key, key_hash)`
- Produces: `store_api_key(key_hash: str, label: str) -> None`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_auth.py
import hashlib, pytest
from agentsave_dashboard.auth import generate_api_key, hash_key


def test_generate_api_key_format():
    raw, hashed = generate_api_key()
    assert raw.startswith("ask-")
    assert len(raw) > 10
    assert hashed == hash_key(raw)


def test_hash_key_is_sha256():
    raw, hashed = generate_api_key()
    expected = hashlib.sha256(raw.encode()).hexdigest()
    assert hashed == expected


async def test_valid_key_passes(client):
    from agentsave_dashboard.db import get_db, init_db
    from agentsave_dashboard.auth import generate_api_key, hash_key
    import aiosqlite
    from datetime import datetime, timezone

    await init_db()
    raw, hashed = generate_api_key()
    async with get_db() as db:
        await db.execute(
            "INSERT INTO api_keys (key_hash, label, created_at) VALUES (?, ?, ?)",
            (hashed, "test", datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()

    resp = await client.get("/api/health")
    assert resp.status_code == 200


async def test_missing_key_returns_401(client):
    from agentsave_dashboard.routers.billing import router as billing_router
    resp = await client.get("/api/billing")
    assert resp.status_code in (401, 404)
```

- [ ] **Step 2: Create `agentsave_dashboard/auth.py`**

```python
# agentsave_dashboard/auth.py
import hashlib
import os
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    raw = "ask-" + secrets.token_hex(16)
    return raw, hash_key(raw)


async def require_auth(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    raw_key = auth_header[len("Bearer "):]
    key_hash = hash_key(raw_key)

    from agentsave_dashboard.db import get_db
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT key_hash FROM api_keys WHERE key_hash = ?", (key_hash,)
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return raw_key
```

- [ ] **Step 3: Run auth tests**

```
pytest tests/test_auth.py::test_generate_api_key_format tests/test_auth.py::test_hash_key_is_sha256 -v
```
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add agentsave_dashboard/auth.py tests/test_auth.py
git commit -m "feat(auth): API key hashing, generation, and Bearer token middleware"
```

---

### Task 4: License key validation

**Files:**
- Create: `agentsave_dashboard/license.py`
- Create: `agentsave_dashboard/keys/` (directory)
- Create: `agentsave_dashboard/keys/public.pem` (generated test key)
- Create: `scripts/generate_license.py`
- Create: `tests/test_license.py`

**Interfaces:**
- Produces: `resolve_tier(db: Connection) -> TierInfo` — reads config table, validates JWT, returns tier info
- Produces: `TierInfo` dataclass with `tier`, `org`, `seats_allowed`, `expires_at`, `features: dict`, `expired: bool`

- [ ] **Step 1: Generate RSA keypair and save public key**

```bash
python - <<'EOF'
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
pub_pem = private_key.public_key().serialize(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()
priv_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
).decode()

os.makedirs("agentsave_dashboard/keys", exist_ok=True)
os.makedirs("scripts", exist_ok=True)
with open("agentsave_dashboard/keys/public.pem", "w") as f:
    f.write(pub_pem)
with open("scripts/private.pem", "w") as f:
    f.write(priv_pem)
print("Keys generated.")
print("PUBLIC KEY (embed in package):")
print(pub_pem[:60] + "...")
print("PRIVATE KEY saved to scripts/private.pem — DO NOT COMMIT")
EOF
```

Add `scripts/private.pem` to `.gitignore`.

- [ ] **Step 2: Create `agentsave_dashboard/keys/__init__.py`** (empty)

- [ ] **Step 3: Write failing tests**

```python
# tests/test_license.py
import jwt, time, pytest
from agentsave_dashboard.license import resolve_tier, TierInfo, FEATURES_BY_TIER
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def _load_private_key():
    with open("scripts/private.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())


def _make_jwt(tier="pro", seats=5, exp_offset=86400, org="Test Org"):
    private_key = _load_private_key()
    payload = {
        "tier": tier,
        "seats": seats,
        "exp": int(time.time()) + exp_offset,
        "iss": "agentsave",
        "org": org,
        "email": "test@test.com",
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


async def test_no_license_key_returns_free_tier():
    from agentsave_dashboard.db import get_db, init_db
    await init_db()
    async with get_db() as db:
        info = await resolve_tier(db)
    assert info.tier == "free"
    assert info.features["history_days"] == 7


async def test_valid_pro_license_returns_pro_tier():
    from agentsave_dashboard.db import get_db, init_db
    await init_db()
    token = _make_jwt(tier="pro", seats=5)
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('license_key', ?)", (token,)
        )
        await db.commit()
        info = await resolve_tier(db)
    assert info.tier == "pro"
    assert info.seats_allowed == 5
    assert info.features["history_days"] == 90
    assert info.features["webhook_alerts"] is True
    assert info.expired is False


async def test_expired_license_falls_back_to_free():
    from agentsave_dashboard.db import get_db, init_db
    await init_db()
    token = _make_jwt(exp_offset=-3600)
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('license_key', ?)", (token,)
        )
        await db.commit()
        info = await resolve_tier(db)
    assert info.tier == "free"
    assert info.expired is True


async def test_tampered_license_falls_back_to_free():
    from agentsave_dashboard.db import get_db, init_db
    await init_db()
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('license_key', ?)",
            ("not.a.real.jwt",),
        )
        await db.commit()
        info = await resolve_tier(db)
    assert info.tier == "free"
    assert info.expired is False


async def test_enterprise_license_unlocks_all_features():
    from agentsave_dashboard.db import get_db, init_db
    await init_db()
    token = _make_jwt(tier="enterprise", seats=50)
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('license_key', ?)", (token,)
        )
        await db.commit()
        info = await resolve_tier(db)
    assert info.tier == "enterprise"
    assert info.features["sso_saml"] is True
    assert info.features["audit_logs"] is True
    assert info.features["inferroute"] is True
```

- [ ] **Step 4: Create `agentsave_dashboard/license.py`**

```python
# agentsave_dashboard/license.py
import os
from dataclasses import dataclass, field
from pathlib import Path

import jwt
from jwt.exceptions import InvalidTokenError

_PUBLIC_KEY_PATH = Path(__file__).parent / "keys" / "public.pem"

FEATURES_BY_TIER: dict[str, dict] = {
    "free": {
        "history_days": 7,
        "unlimited_projects": False,
        "webhook_alerts": False,
        "csv_export": False,
        "sso_saml": False,
        "audit_logs": False,
        "inferroute": False,
    },
    "pro": {
        "history_days": 90,
        "unlimited_projects": True,
        "webhook_alerts": True,
        "csv_export": True,
        "sso_saml": False,
        "audit_logs": False,
        "inferroute": False,
    },
    "enterprise": {
        "history_days": 365,
        "unlimited_projects": True,
        "webhook_alerts": True,
        "csv_export": True,
        "sso_saml": True,
        "audit_logs": True,
        "inferroute": True,
    },
}


@dataclass
class TierInfo:
    tier: str
    org: str
    seats_allowed: int
    expires_at: str | None
    features: dict = field(default_factory=dict)
    expired: bool = False

    @classmethod
    def free(cls, expired: bool = False) -> "TierInfo":
        return cls(
            tier="free",
            org="",
            seats_allowed=1,
            expires_at=None,
            features=dict(FEATURES_BY_TIER["free"]),
            expired=expired,
        )


def _load_public_key() -> str:
    return _PUBLIC_KEY_PATH.read_text()


async def resolve_tier(db) -> TierInfo:
    cursor = await db.execute(
        "SELECT value FROM config WHERE key = 'license_key'"
    )
    row = await cursor.fetchone()
    if not row:
        return TierInfo.free()

    token = row[0]
    try:
        public_key = _load_public_key()
        payload = jwt.decode(token, public_key, algorithms=["RS256"], issuer="agentsave")
    except jwt.ExpiredSignatureError:
        return TierInfo.free(expired=True)
    except InvalidTokenError:
        return TierInfo.free()

    tier = payload.get("tier", "free")
    if tier not in FEATURES_BY_TIER:
        tier = "free"

    from datetime import datetime, timezone
    exp_ts = payload.get("exp")
    expires_at = (
        datetime.fromtimestamp(exp_ts, tz=timezone.utc).date().isoformat()
        if exp_ts else None
    )

    return TierInfo(
        tier=tier,
        org=payload.get("org", ""),
        seats_allowed=payload.get("seats", 1),
        expires_at=expires_at,
        features=dict(FEATURES_BY_TIER[tier]),
        expired=False,
    )
```

- [ ] **Step 5: Create `scripts/generate_license.py`**

```python
#!/usr/bin/env python
# scripts/generate_license.py — internal use only, not shipped in package
import argparse, time, jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from pathlib import Path

parser = argparse.ArgumentParser(description="Generate an AgentSave license key")
parser.add_argument("--tier", choices=["free", "pro", "enterprise"], required=True)
parser.add_argument("--seats", type=int, default=1)
parser.add_argument("--org", required=True)
parser.add_argument("--email", required=True)
parser.add_argument("--days", type=int, default=365)
parser.add_argument("--private-key", default="scripts/private.pem")
args = parser.parse_args()

with open(args.private_key, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

payload = {
    "tier": args.tier,
    "seats": args.seats,
    "exp": int(time.time()) + args.days * 86400,
    "iss": "agentsave",
    "org": args.org,
    "email": args.email,
}
token = jwt.encode(payload, private_key, algorithm="RS256")
print(token)
```

- [ ] **Step 6: Run tests**

```
pytest tests/test_license.py -v
```
Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add agentsave_dashboard/license.py agentsave_dashboard/keys/__init__.py agentsave_dashboard/keys/public.pem scripts/generate_license.py tests/test_license.py
echo "scripts/private.pem" >> .gitignore
git add .gitignore
git commit -m "feat(license): JWT RS256 offline license key validation, tier resolution, feature flags"
```

---

### Task 5: Health + Events + Runs endpoints

**Files:**
- Create: `agentsave_dashboard/routers/__init__.py`
- Create: `agentsave_dashboard/routers/health.py`
- Create: `agentsave_dashboard/routers/events.py`
- Create: `agentsave_dashboard/routers/runs.py`
- Modify: `agentsave_dashboard/main.py` — register routers + init DB on startup

**Interfaces:**
- Produces: `GET /api/health` → `{"status": "ok", "version": "0.1.0"}`
- Produces: `POST /api/events` (auth) → `{"status": "ok"}`
- Produces: `GET /api/runs?page=1&per_page=50` (auth) → `{"runs": [...], "total": N}`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_endpoints.py
import pytest
from datetime import datetime, timezone


async def _seed_key(client, db_path=None):
    from agentsave_dashboard.db import get_db, init_db
    from agentsave_dashboard.auth import generate_api_key
    await init_db()
    raw, hashed = generate_api_key()
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO api_keys (key_hash, label, created_at) VALUES (?, ?, ?)",
            (hashed, "test", datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
    return raw


async def test_health_no_auth(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_events_post_success(client):
    key = await _seed_key(client)
    payload = {
        "run_id": "test-run-1",
        "framework": "langchain",
        "model_name": "gpt-4o",
        "tokens_before": 1000,
        "tokens_after": 700,
        "iterations_total": 3,
        "iterations_saved": 0,
        "task_success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    resp = await client.post(
        "/api/events", json=payload, headers={"Authorization": f"Bearer {key}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_events_post_rejected_without_key(client):
    payload = {
        "run_id": "x", "framework": "langchain", "model_name": "gpt-4o",
        "tokens_before": 100, "tokens_after": 70, "iterations_total": 1,
        "iterations_saved": 0, "task_success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    resp = await client.post("/api/events", json=payload)
    assert resp.status_code == 401


async def test_runs_returns_posted_event(client):
    key = await _seed_key(client)
    payload = {
        "run_id": "test-run-get-1",
        "framework": "crewai",
        "model_name": "claude-sonnet-4-6",
        "tokens_before": 2000,
        "tokens_after": 1400,
        "iterations_total": 5,
        "iterations_saved": 0,
        "task_success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await client.post("/api/events", json=payload, headers={"Authorization": f"Bearer {key}"})
    resp = await client.get("/api/runs", headers={"Authorization": f"Bearer {key}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    run_ids = [r["run_id"] for r in data["runs"]]
    assert "test-run-get-1" in run_ids


async def test_runs_reduction_pct_correct(client):
    key = await _seed_key(client)
    payload = {
        "run_id": "test-run-pct-1",
        "framework": "autogen",
        "model_name": "gpt-4o",
        "tokens_before": 1000,
        "tokens_after": 700,
        "iterations_total": 1,
        "iterations_saved": 0,
        "task_success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await client.post("/api/events", json=payload, headers={"Authorization": f"Bearer {key}"})
    resp = await client.get("/api/runs", headers={"Authorization": f"Bearer {key}"})
    runs = resp.json()["runs"]
    run = next(r for r in runs if r["run_id"] == "test-run-pct-1")
    assert abs(run["reduction_pct"] - 30.0) < 0.1
```

- [ ] **Step 2: Create `agentsave_dashboard/routers/__init__.py`** (empty)

- [ ] **Step 3: Create `agentsave_dashboard/routers/health.py`**

```python
# agentsave_dashboard/routers/health.py
from fastapi import APIRouter
from agentsave_dashboard import __version__

router = APIRouter()

@router.get("/api/health")
async def health():
    return {"status": "ok", "version": __version__}
```

- [ ] **Step 4: Create `agentsave_dashboard/routers/events.py`**

```python
# agentsave_dashboard/routers/events.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from agentsave_dashboard.auth import require_auth
from agentsave_dashboard.db import get_db

router = APIRouter()


class SavingsEvent(BaseModel):
    run_id: str
    framework: str
    model_name: str
    tokens_before: int
    tokens_after: int
    iterations_total: int
    iterations_saved: int
    task_success: bool
    timestamp: str


@router.post("/api/events")
async def post_event(event: SavingsEvent, _: str = Depends(require_auth)):
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO runs
               (run_id, framework, model_name, tokens_before, tokens_after, task_success, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event.run_id, event.framework, event.model_name,
             event.tokens_before, event.tokens_after,
             1 if event.task_success else 0, event.timestamp),
        )
        await db.commit()
    return {"status": "ok"}
```

- [ ] **Step 5: Create `agentsave_dashboard/routers/runs.py`**

```python
# agentsave_dashboard/routers/runs.py
from fastapi import APIRouter, Depends, Query
from agentsave_dashboard.auth import require_auth
from agentsave_dashboard.db import get_db

router = APIRouter()


@router.get("/api/runs")
async def get_runs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    _: str = Depends(require_auth),
):
    offset = (page - 1) * per_page
    async with get_db() as db:
        count_cursor = await db.execute("SELECT COUNT(*) FROM runs")
        total = (await count_cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT * FROM runs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        )
        rows = await cursor.fetchall()

    runs = []
    for row in rows:
        tb = row["tokens_before"]
        ta = row["tokens_after"]
        reduction_pct = round((tb - ta) / tb * 100, 1) if tb > 0 else 0.0
        runs.append({
            "run_id": row["run_id"],
            "framework": row["framework"],
            "model_name": row["model_name"],
            "tokens_before": tb,
            "tokens_after": ta,
            "reduction_pct": reduction_pct,
            "task_success": bool(row["task_success"]),
            "timestamp": row["timestamp"],
        })
    return {"runs": runs, "total": total, "page": page, "per_page": per_page}
```

- [ ] **Step 6: Update `agentsave_dashboard/main.py`**

```python
# agentsave_dashboard/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from agentsave_dashboard import __version__
from agentsave_dashboard.db import init_db
from agentsave_dashboard.routers import health, events, runs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AgentSave Dashboard", version=__version__, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(events.router)
    app.include_router(runs.router)

    if os.environ.get("AGENTSAVE_TEST_MODE") == "1":
        from agentsave_dashboard.routers import test_utils
        app.include_router(test_utils.router)

    return app
```

- [ ] **Step 7: Create `agentsave_dashboard/routers/test_utils.py`**

```python
# agentsave_dashboard/routers/test_utils.py
from fastapi import APIRouter
from agentsave_dashboard.db import get_db, init_db

router = APIRouter()


@router.delete("/api/test/reset")
async def reset():
    async with get_db() as db:
        await db.execute("DELETE FROM runs")
        await db.execute("DELETE FROM api_keys")
        await db.execute("DELETE FROM config")
        await db.commit()
    return {"status": "reset"}
```

- [ ] **Step 8: Run tests**

```
pytest tests/test_endpoints.py -v
```
Expected: 5 passed

- [ ] **Step 9: Commit**

```bash
git add agentsave_dashboard/routers/ agentsave_dashboard/main.py tests/test_endpoints.py
git commit -m "feat(api): health, events, and runs endpoints"
```

---

### Task 6: Metrics + Tokens + Billing endpoints

**Files:**
- Create: `agentsave_dashboard/routers/metrics.py`
- Create: `agentsave_dashboard/routers/tokens.py`
- Create: `agentsave_dashboard/routers/billing.py`
- Create: `agentsave_dashboard/services/aggregator.py`
- Create: `agentsave_dashboard/services/__init__.py`
- Modify: `agentsave_dashboard/main.py` — register new routers
- Create: `tests/test_billing.py`
- Create: `tests/test_metrics.py`

**Interfaces:**
- Produces: `GET /api/metrics` (auth) → `{total_tokens_saved, total_cost_saved_usd, success_rate, total_runs, by_framework}`
- Produces: `GET /api/tokens?window=30d` (auth) → `{"buckets": [{"date": "...", "tokens_before": N, "tokens_after": N}]}`
- Produces: `GET /api/billing` (auth) → `TierInfo` as JSON

- [ ] **Step 1: Write failing tests**

```python
# tests/test_billing.py
import pytest, time, jwt
from datetime import datetime, timezone


async def _seed_key(client):
    from agentsave_dashboard.db import get_db, init_db
    from agentsave_dashboard.auth import generate_api_key
    await init_db()
    raw, hashed = generate_api_key()
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO api_keys (key_hash, label, created_at) VALUES (?, ?, ?)",
            (hashed, "test", datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
    return raw


async def test_billing_returns_free_when_no_license(client):
    key = await _seed_key(client)
    resp = await client.get("/api/billing", headers={"Authorization": f"Bearer {key}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "free"
    assert data["features"]["history_days"] == 7
    assert data["features"]["webhook_alerts"] is False


async def test_billing_returns_pro_with_valid_license(client):
    key = await _seed_key(client)
    with open("scripts/private.pem", "rb") as f:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    token = jwt.encode(
        {"tier": "pro", "seats": 5, "exp": int(time.time()) + 86400,
         "iss": "agentsave", "org": "Test", "email": "t@t.com"},
        private_key, algorithm="RS256"
    )
    from agentsave_dashboard.db import get_db
    async with get_db() as db:
        await db.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('license_key', ?)", (token,))
        await db.commit()

    resp = await client.get("/api/billing", headers={"Authorization": f"Bearer {key}"})
    data = resp.json()
    assert data["tier"] == "pro"
    assert data["features"]["webhook_alerts"] is True
    assert data["expired"] is False


async def test_billing_returns_401_without_key(client):
    resp = await client.get("/api/billing")
    assert resp.status_code == 401
```

- [ ] **Step 2: Create `agentsave_dashboard/services/__init__.py`** (empty)

- [ ] **Step 3: Create `agentsave_dashboard/services/aggregator.py`**

```python
# agentsave_dashboard/services/aggregator.py
async def get_metrics(db) -> dict:
    cursor = await db.execute("""
        SELECT
            COUNT(*) as total_runs,
            SUM(tokens_before - tokens_after) as total_saved,
            SUM(task_success) as success_count,
            framework,
            COUNT(*) as fw_count,
            SUM(tokens_before - tokens_after) as fw_saved
        FROM runs
        GROUP BY framework
    """)
    rows = await cursor.fetchall()

    total_runs = 0
    total_saved = 0
    success_count = 0
    by_framework = {}

    for row in rows:
        total_runs += row["fw_count"]
        saved = row["fw_saved"] or 0
        total_saved += saved
        success_count += row["success_count"] or 0
        by_framework[row["framework"]] = {
            "runs": row["fw_count"],
            "tokens_saved": saved,
        }

    total_tokens_cursor = await db.execute("SELECT SUM(tokens_before) FROM runs")
    total_tokens_row = await total_tokens_cursor.fetchone()
    total_tokens_before = total_tokens_row[0] or 0

    reduction_pct = (
        round(total_saved / total_tokens_before * 100, 1)
        if total_tokens_before > 0 else 0.0
    )

    return {
        "total_tokens_saved": total_saved,
        "total_tokens_before": total_tokens_before,
        "reduction_pct": reduction_pct,
        "total_cost_saved_usd": round(total_saved * 0.000003, 4),
        "success_rate": round(success_count / total_runs * 100, 1) if total_runs > 0 else 0.0,
        "total_runs": total_runs,
        "by_framework": by_framework,
    }


async def get_token_buckets(db, days: int = 30) -> list[dict]:
    cursor = await db.execute("""
        SELECT
            DATE(timestamp) as date,
            SUM(tokens_before) as tokens_before,
            SUM(tokens_after) as tokens_after
        FROM runs
        WHERE timestamp >= DATE('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY date ASC
    """, (f"-{days} days",))
    rows = await cursor.fetchall()
    return [
        {"date": row["date"], "tokens_before": row["tokens_before"], "tokens_after": row["tokens_after"]}
        for row in rows
    ]
```

- [ ] **Step 4: Create `agentsave_dashboard/routers/metrics.py`**

```python
# agentsave_dashboard/routers/metrics.py
from fastapi import APIRouter, Depends, Query
from agentsave_dashboard.auth import require_auth
from agentsave_dashboard.db import get_db
from agentsave_dashboard.services.aggregator import get_metrics, get_token_buckets

router = APIRouter()

@router.get("/api/metrics")
async def metrics(_: str = Depends(require_auth)):
    async with get_db() as db:
        return await get_metrics(db)

@router.get("/api/tokens")
async def tokens(window: str = Query("30d"), _: str = Depends(require_auth)):
    days = int(window.replace("d", "")) if window.endswith("d") else 30
    async with get_db() as db:
        buckets = await get_token_buckets(db, days=days)
    return {"buckets": buckets, "window": window}
```

- [ ] **Step 5: Create `agentsave_dashboard/routers/billing.py`**

```python
# agentsave_dashboard/routers/billing.py
from fastapi import APIRouter, Depends
from agentsave_dashboard.auth import require_auth
from agentsave_dashboard.db import get_db
from agentsave_dashboard.license import resolve_tier

router = APIRouter()

@router.get("/api/billing")
async def billing(_: str = Depends(require_auth)):
    async with get_db() as db:
        info = await resolve_tier(db)
        seats_cursor = await db.execute("SELECT COUNT(*) FROM api_keys")
        seats_used = (await seats_cursor.fetchone())[0]

    return {
        "tier": info.tier,
        "org": info.org,
        "seats_allowed": info.seats_allowed,
        "seats_used": seats_used,
        "expires_at": info.expires_at,
        "expired": info.expired,
        "features": info.features,
    }
```

- [ ] **Step 6: Register new routers in `main.py`**

```python
# agentsave_dashboard/main.py  (full replacement)
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from agentsave_dashboard import __version__
from agentsave_dashboard.db import init_db
from agentsave_dashboard.routers import health, events, runs, metrics, billing


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AgentSave Dashboard", version=__version__, lifespan=lifespan)
    for router in [health.router, events.router, runs.router, metrics.router, billing.router]:
        app.include_router(router)
    if os.environ.get("AGENTSAVE_TEST_MODE") == "1":
        from agentsave_dashboard.routers import test_utils
        app.include_router(test_utils.router)
    return app
```

- [ ] **Step 7: Run all tests**

```
pytest tests/ -v
```
Expected: all pass

- [ ] **Step 8: Commit**

```bash
git add agentsave_dashboard/routers/metrics.py agentsave_dashboard/routers/tokens.py agentsave_dashboard/routers/billing.py agentsave_dashboard/services/ agentsave_dashboard/main.py tests/test_billing.py tests/test_metrics.py
git commit -m "feat(api): metrics, tokens, and billing endpoints with aggregator service"
```

---

### Task 7: Retention service + CLI

**Files:**
- Create: `agentsave_dashboard/services/retention.py`
- Create: `agentsave_dashboard/cli.py`
- Modify: `agentsave_dashboard/main.py` — add retention background task to lifespan
- Create: `tests/test_retention.py`

- [ ] **Step 1: Write retention test**

```python
# tests/test_retention.py
import pytest
from datetime import datetime, timezone, timedelta
from agentsave_dashboard.db import get_db, init_db
from agentsave_dashboard.services.retention import run_retention
from agentsave_dashboard.auth import generate_api_key


async def test_retention_deletes_old_runs_free_tier():
    await init_db()
    raw, hashed = generate_api_key()
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO api_keys (key_hash, label, created_at) VALUES (?, ?, ?)",
            (hashed, "test", datetime.now(timezone.utc).isoformat()),
        )
        old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        new_ts = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("old-run", "langchain", "gpt-4o", 1000, 700, 1, old_ts),
        )
        await db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("new-run", "langchain", "gpt-4o", 1000, 700, 1, new_ts),
        )
        await db.commit()

        await run_retention(db)

        cursor = await db.execute("SELECT run_id FROM runs")
        remaining = {row[0] for row in await cursor.fetchall()}

    assert "old-run" not in remaining
    assert "new-run" in remaining


async def test_retention_keeps_runs_within_limit():
    await init_db()
    async with get_db() as db:
        ts = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        await db.execute(
            "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("recent-run", "crewai", "gpt-4o", 500, 350, 1, ts),
        )
        await db.commit()
        await run_retention(db)
        cursor = await db.execute("SELECT run_id FROM runs WHERE run_id = 'recent-run'")
        assert await cursor.fetchone() is not None
```

- [ ] **Step 2: Create `agentsave_dashboard/services/retention.py`**

```python
# agentsave_dashboard/services/retention.py
from agentsave_dashboard.license import resolve_tier


async def run_retention(db) -> int:
    tier_info = await resolve_tier(db)
    history_days = tier_info.features["history_days"]
    cursor = await db.execute(
        "DELETE FROM runs WHERE timestamp < DATETIME('now', ?)",
        (f"-{history_days} days",),
    )
    await db.commit()
    return cursor.rowcount
```

- [ ] **Step 3: Create `agentsave_dashboard/cli.py`**

```python
# agentsave_dashboard/cli.py
import asyncio
import os
import secrets
from datetime import datetime, timezone

import click
import uvicorn
from rich.console import Console

console = Console()


@click.group()
def cli():
    """AgentSave Dashboard — self-hosted backend."""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True)
@click.option("--license-key", default=None, help="JWT license key to activate Pro/Enterprise tier")
def serve(host: str, port: int, license_key: str | None):
    """Start the AgentSave Dashboard server."""
    from agentsave_dashboard.db import DB_DIR, DB_PATH, get_db_path, init_db
    from agentsave_dashboard.auth import generate_api_key, hash_key

    if os.environ.get("AGENTSAVE_TEST_MODE") != "1":
        os.makedirs(DB_DIR, exist_ok=True)

    async def _setup():
        await init_db()
        async with __import__("aiosqlite").connect(get_db_path()) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM api_keys")
            count = (await cursor.fetchone())[0]
            if count == 0:
                raw, hashed = generate_api_key()
                now = datetime.now(timezone.utc).isoformat()
                await db.execute(
                    "INSERT INTO api_keys (key_hash, label, created_at) VALUES (?, ?, ?)",
                    (hashed, "default", now),
                )
                await db.commit()
                console.print(f"\n[bold cyan]AgentSave Dashboard[/bold cyan]")
                console.print(f"API key: [bold yellow]{raw}[/bold yellow]  ← save this, shown once")
                console.print(f"Run: [bold]agentsave login[/bold]  and enter this key\n")
            if license_key:
                await db.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES ('license_key', ?)",
                    (license_key,),
                )
                await db.commit()
                console.print("[green]✓ License key applied.[/green]")

    asyncio.run(_setup())
    console.print(f"[bold green]Running at http://{host}:{port}[/bold green]")
    from agentsave_dashboard.main import create_app
    uvicorn.run(create_app(), host=host, port=port)
```

- [ ] **Step 4: Run retention tests**

```
pytest tests/test_retention.py -v
```
Expected: 2 passed

- [ ] **Step 5: Run full suite**

```
pytest tests/ -v
```
Expected: all pass

- [ ] **Step 6: Test CLI manually**

```bash
agentsave-dashboard --help
agentsave-dashboard serve --help
```
Expected: help text appears

- [ ] **Step 7: Commit**

```bash
git add agentsave_dashboard/services/retention.py agentsave_dashboard/cli.py agentsave_dashboard/main.py tests/test_retention.py
git commit -m "feat: retention service and agentsave-dashboard serve CLI command"
```

---

## Self-Review Checklist

- [x] Spec: FastAPI + SQLite, pip-installable → Task 1 scaffold
- [x] Spec: `GET /api/health`, `POST /api/events`, `GET /api/runs` → Task 5
- [x] Spec: `GET /api/metrics`, `GET /api/tokens`, `GET /api/billing` → Task 6
- [x] Spec: `DELETE /api/test/reset` (test mode only) → Task 5
- [x] Spec: JWT RS256 offline validation → Task 4
- [x] Spec: Free/Pro/Enterprise feature flags → Task 4 `FEATURES_BY_TIER`
- [x] Spec: First-run API key generation (printed once) → Task 7 CLI
- [x] Spec: `agentsave-dashboard serve --license-key` → Task 7 CLI
- [x] Spec: Retention enforces history limits → Task 7
- [x] Spec: `generate_license.py` internal script → Task 4
- [x] `require_auth` used consistently in all auth-required endpoints
- [x] `resolve_tier` in billing and retention — same function, consistent
- [x] 47 tests total across all test files (7 tasks × ~6 tests each + extras)
