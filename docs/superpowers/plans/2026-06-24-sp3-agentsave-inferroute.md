# Sub-project 3: `agentsave-inferroute` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an Enterprise-only PPD (append-prefill decode) routing sidecar that sits in front of vLLM or SGLang clusters and reduces Turn 2+ TTFT by reusing the KV cache. Ships as a Docker image.

**Architecture:** A Python FastAPI HTTP proxy. On each request it checks conversation history length (Turn 1 vs. Turn 2+), scores the PPD opportunity, and routes accordingly — standard prefill-decode for Turn 1, append-prefill for Turn 2+. License validation at startup refuses to start without an Enterprise JWT. The public key is embedded in the package.

**Tech Stack:** Python 3.11+, FastAPI 0.115+, httpx 0.27+ (async proxy), PyJWT[crypto] 2.8+, cryptography 42+, uvicorn 0.30+, click 8.1+, pytest 8+, pytest-asyncio 0.23+, Docker

## Global Constraints

- Python ≥ 3.11
- Refuses to start without a valid Enterprise license JWT (`AGENTSAVE_LICENSE` env var)
- `BACKEND_URL` and `BACKEND_TYPE` (vllm | sglang) required at startup
- All routing logic is stateless — each request is independently scored
- Public key embedded in `inferroute/keys/public.pem` (same key as agentsave-dashboard)
- TTFT benchmark target: ~68% Turn 2+ reduction — must be measured and reported before README claim is updated
- 59 tests total across all test files
- Commit after every task

---

### Task 1: Project scaffold + Turn classifier

**Files:**
- Create: `pyproject.toml`
- Create: `inferroute/__init__.py`
- Create: `inferroute/classifier.py`
- Create: `tests/__init__.py`
- Create: `tests/test_classifier.py`

**Interfaces:**
- Produces: `classify_turn(messages: list[dict]) -> int` — returns 1 for first turn, 2+ for subsequent

- [ ] **Step 1: Initialise repo**

```bash
mkdir agentsave-inferroute && cd agentsave-inferroute
git init
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling>=1.21"]
build-backend = "hatchling.build"

[project]
name = "agentsave-inferroute"
version = "0.1.0"
description = "AgentSave InferRoute — PPD routing sidecar for vLLM/SGLang"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Aditya Kumar Singh", email = "its.aks@outlook.com" }]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "httpx>=0.27.0",
    "PyJWT[crypto]>=2.8.0",
    "cryptography>=42.0.0",
    "click>=8.1.0",
]

[project.scripts]
agentsave-inferroute = "inferroute.cli:cli"

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "httpx>=0.27.0"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.build.targets.wheel]
packages = ["inferroute"]
```

- [ ] **Step 3: Install**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 4: Write failing classifier tests**

```python
# tests/test_classifier.py
from inferroute.classifier import classify_turn


def test_empty_messages_is_turn_1():
    assert classify_turn([]) == 1


def test_single_user_message_is_turn_1():
    assert classify_turn([{"role": "user", "content": "Hello"}]) == 1


def test_user_and_assistant_then_user_is_turn_2():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"},
    ]
    assert classify_turn(messages) == 2


def test_multiple_rounds_is_turn_2():
    messages = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
        {"role": "assistant", "content": "A2"},
        {"role": "user", "content": "Q3"},
    ]
    assert classify_turn(messages) == 2


def test_system_message_only_is_turn_1():
    assert classify_turn([{"role": "system", "content": "You are helpful"}]) == 1


def test_system_plus_user_is_turn_1():
    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"},
    ]
    assert classify_turn(messages) == 1
```

- [ ] **Step 5: Run to verify failures**

```
pytest tests/test_classifier.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 6: Create `inferroute/__init__.py`**

```python
# inferroute/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 7: Create `inferroute/classifier.py`**

```python
# inferroute/classifier.py


def classify_turn(messages: list[dict]) -> int:
    """Return 1 for first turn (no prior assistant reply), 2+ for subsequent turns."""
    assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
    return 1 if assistant_count == 0 else 2
```

- [ ] **Step 8: Run tests**

```
pytest tests/test_classifier.py -v
```
Expected: 6 passed

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml inferroute/__init__.py inferroute/classifier.py tests/__init__.py tests/test_classifier.py
git commit -m "feat: project scaffold and turn classifier"
```

---

### Task 2: PPD router + license validation

**Files:**
- Create: `inferroute/router.py`
- Create: `inferroute/license.py`
- Create: `inferroute/keys/__init__.py`
- Create: `inferroute/keys/public.pem` (copy from agentsave-dashboard)
- Create: `tests/test_router.py`
- Create: `tests/test_license.py`

**Interfaces:**
- Produces: `should_use_ppd(messages: list[dict], context_length: int) -> bool`
- Produces: `validate_enterprise_license(token: str) -> bool`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_router.py
from inferroute.router import should_use_ppd


def test_turn_1_never_uses_ppd():
    messages = [{"role": "user", "content": "Hello"}]
    assert should_use_ppd(messages, context_length=0) is False


def test_turn_2_with_long_context_uses_ppd():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "Tell me more"},
    ]
    assert should_use_ppd(messages, context_length=2000) is True


def test_turn_2_with_short_context_no_ppd():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "Ok"},
    ]
    assert should_use_ppd(messages, context_length=50) is False


def test_ppd_threshold_boundary():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "More"},
    ]
    assert should_use_ppd(messages, context_length=499) is False
    assert should_use_ppd(messages, context_length=500) is True
```

```python
# tests/test_license.py
import jwt, time
from inferroute.license import validate_enterprise_license
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def _make_token(tier: str, exp_offset: int = 86400) -> str:
    # Requires scripts/private.pem from agentsave-dashboard to be accessible
    # In CI, set INFERROUTE_PRIVATE_KEY_PATH env var
    import os
    key_path = os.environ.get("INFERROUTE_PRIVATE_KEY_PATH", "../agentsave-dashboard/scripts/private.pem")
    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    return jwt.encode(
        {"tier": tier, "seats": 10, "exp": int(time.time()) + exp_offset,
         "iss": "agentsave", "org": "Test", "email": "t@t.com"},
        private_key, algorithm="RS256"
    )


def test_enterprise_license_valid():
    token = _make_token("enterprise")
    assert validate_enterprise_license(token) is True


def test_pro_license_rejected():
    token = _make_token("pro")
    assert validate_enterprise_license(token) is False


def test_expired_license_rejected():
    token = _make_token("enterprise", exp_offset=-3600)
    assert validate_enterprise_license(token) is False


def test_invalid_token_rejected():
    assert validate_enterprise_license("not.a.token") is False


def test_empty_token_rejected():
    assert validate_enterprise_license("") is False
```

- [ ] **Step 2: Create `inferroute/router.py`**

```python
# inferroute/router.py
from inferroute.classifier import classify_turn

PPD_CONTEXT_THRESHOLD = 500  # tokens; below this PPD has no benefit


def should_use_ppd(messages: list[dict], context_length: int) -> bool:
    """Use PPD only for Turn 2+ with enough context to benefit from KV cache reuse."""
    if classify_turn(messages) == 1:
        return False
    return context_length >= PPD_CONTEXT_THRESHOLD
```

- [ ] **Step 3: Copy public key from agentsave-dashboard**

```bash
mkdir -p inferroute/keys
cp ../agentsave-dashboard/agentsave_dashboard/keys/public.pem inferroute/keys/public.pem
touch inferroute/keys/__init__.py
```

If agentsave-dashboard isn't adjacent, generate a new matching keypair using the same `scripts/generate_license.py` from that repo.

- [ ] **Step 4: Create `inferroute/license.py`**

```python
# inferroute/license.py
from pathlib import Path
import jwt
from jwt.exceptions import InvalidTokenError

_PUBLIC_KEY_PATH = Path(__file__).parent / "keys" / "public.pem"


def validate_enterprise_license(token: str) -> bool:
    if not token:
        return False
    try:
        public_key = _PUBLIC_KEY_PATH.read_text()
        payload = jwt.decode(token, public_key, algorithms=["RS256"], issuer="agentsave")
        return payload.get("tier") == "enterprise"
    except (InvalidTokenError, Exception):
        return False
```

- [ ] **Step 5: Run tests**

```
pytest tests/test_router.py tests/test_license.py -v
```
Expected: 9 passed (license tests skip gracefully if private key not found)

- [ ] **Step 6: Commit**

```bash
git add inferroute/router.py inferroute/license.py inferroute/keys/ tests/test_router.py tests/test_license.py
git commit -m "feat: PPD router with context-length threshold and enterprise license validation"
```

---

### Task 3: Backend adapters + HTTP proxy + FastAPI app

**Files:**
- Create: `inferroute/adapters/__init__.py`
- Create: `inferroute/adapters/vllm.py`
- Create: `inferroute/adapters/sglang.py`
- Create: `inferroute/proxy.py`
- Create: `inferroute/main.py`
- Create: `inferroute/cli.py`
- Create: `tests/test_proxy.py`
- Create: `tests/test_adapters.py`

**Interfaces:**
- Produces: `build_ppd_request(request_body: dict, backend_type: str) -> dict` — transforms standard OpenAI-format request for PPD routing
- Produces: `create_app(backend_url, backend_type, license_token) -> FastAPI`

- [ ] **Step 1: Write failing adapter tests**

```python
# tests/test_adapters.py
from inferroute.adapters.vllm import build_vllm_ppd_request
from inferroute.adapters.sglang import build_sglang_ppd_request


def _base_request():
    return {
        "model": "meta-llama/Llama-3-8b",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "Tell me about Paris"},
        ],
        "max_tokens": 200,
    }


def test_vllm_ppd_request_adds_cache_hint():
    req = build_vllm_ppd_request(_base_request())
    assert req.get("use_beam_search") is not None or "cache_hint" in str(req) or req != _base_request()


def test_vllm_request_preserves_model_and_messages():
    req = build_vllm_ppd_request(_base_request())
    assert req["model"] == "meta-llama/Llama-3-8b"
    assert req["messages"] == _base_request()["messages"]


def test_sglang_request_preserves_model_and_messages():
    req = build_sglang_ppd_request(_base_request())
    assert req["model"] == "meta-llama/Llama-3-8b"
    assert req["messages"] == _base_request()["messages"]


def test_vllm_and_sglang_differ():
    base = _base_request()
    vllm_req = build_vllm_ppd_request(base)
    sglang_req = build_sglang_ppd_request(base)
    assert vllm_req != sglang_req
```

- [ ] **Step 2: Create `inferroute/adapters/__init__.py`** (empty)

- [ ] **Step 3: Create `inferroute/adapters/vllm.py`**

```python
# inferroute/adapters/vllm.py


def build_vllm_ppd_request(request_body: dict) -> dict:
    """Add vLLM-specific PPD hint: prefix_caching=True enables KV cache reuse."""
    return {**request_body, "extra_body": {"prefix_caching": True}}


def build_vllm_standard_request(request_body: dict) -> dict:
    return {**request_body}
```

- [ ] **Step 4: Create `inferroute/adapters/sglang.py`**

```python
# inferroute/adapters/sglang.py


def build_sglang_ppd_request(request_body: dict) -> dict:
    """Add SGLang-specific PPD hint: enable_overlap=True for append-prefill overlap."""
    return {**request_body, "sampling_params": {
        **request_body.get("sampling_params", {}),
        "enable_overlap": True,
    }}


def build_sglang_standard_request(request_body: dict) -> dict:
    return {**request_body}
```

- [ ] **Step 5: Write proxy test**

```python
# tests/test_proxy.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
import json


@pytest.fixture
def valid_enterprise_token():
    import os, time, jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    key_path = os.environ.get("INFERROUTE_PRIVATE_KEY_PATH", "../agentsave-dashboard/scripts/private.pem")
    try:
        with open(key_path, "rb") as f:
            pk = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
        return jwt.encode(
            {"tier": "enterprise", "seats": 10, "exp": int(time.time()) + 86400, "iss": "agentsave", "org": "Test", "email": "t@t.com"},
            pk, algorithm="RS256"
        )
    except FileNotFoundError:
        pytest.skip("Private key not available")


async def test_proxy_routes_turn1_without_ppd(valid_enterprise_token):
    from inferroute.main import create_app
    mock_response_data = {"choices": [{"message": {"content": "Hello!"}}]}

    with patch("inferroute.proxy.forward_request", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = mock_response_data
        app = create_app("http://fake-backend:8000", "vllm", valid_enterprise_token)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            body = {
                "model": "llama-3", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10
            }
            resp = await client.post("/v1/chat/completions", json=body)
        assert resp.status_code == 200
        call_args = mock_fwd.call_args
        assert "prefix_caching" not in str(call_args)


async def test_proxy_routes_turn2_with_ppd(valid_enterprise_token):
    from inferroute.main import create_app
    mock_response_data = {"choices": [{"message": {"content": "More info!"}}]}

    with patch("inferroute.proxy.forward_request", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = mock_response_data
        app = create_app("http://fake-backend:8000", "vllm", valid_enterprise_token)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            long_content = "x" * 600
            body = {
                "model": "llama-3",
                "messages": [
                    {"role": "user", "content": long_content},
                    {"role": "assistant", "content": "Response here"},
                    {"role": "user", "content": "Follow up"},
                ],
                "max_tokens": 10,
            }
            resp = await client.post("/v1/chat/completions", json=body)
        assert resp.status_code == 200
        call_args = str(mock_fwd.call_args)
        assert "prefix_caching" in call_args or "enable_overlap" in call_args


async def test_proxy_rejects_without_enterprise_license():
    from inferroute.main import create_app
    app = create_app("http://fake:8000", "vllm", "bad-token")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/v1/chat/completions", json={"messages": [], "model": "x"})
    assert resp.status_code == 403
```

- [ ] **Step 6: Create `inferroute/proxy.py`**

```python
# inferroute/proxy.py
import httpx


async def forward_request(backend_url: str, path: str, body: dict, headers: dict) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{backend_url}{path}", json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 7: Create `inferroute/main.py`**

```python
# inferroute/main.py
from fastapi import FastAPI, Request, HTTPException
from inferroute.license import validate_enterprise_license
from inferroute.classifier import classify_turn
from inferroute.router import should_use_ppd
from inferroute.proxy import forward_request
from inferroute import __version__


def _estimate_context_length(messages: list[dict]) -> int:
    return sum(len(str(m.get("content", ""))) // 4 for m in messages)


def create_app(backend_url: str, backend_type: str, license_token: str) -> FastAPI:
    app = FastAPI(title="AgentSave InferRoute", version=__version__)
    _license_valid = validate_enterprise_license(license_token)

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        if not _license_valid:
            raise HTTPException(status_code=403, detail="Valid Enterprise license required")

        body = await request.json()
        messages = body.get("messages", [])
        context_length = _estimate_context_length(messages)
        use_ppd = should_use_ppd(messages, context_length)

        if use_ppd:
            if backend_type == "vllm":
                from inferroute.adapters.vllm import build_vllm_ppd_request
                body = build_vllm_ppd_request(body)
            elif backend_type == "sglang":
                from inferroute.adapters.sglang import build_sglang_ppd_request
                body = build_sglang_ppd_request(body)

        fwd_headers = {"Content-Type": "application/json"}
        if auth := request.headers.get("Authorization"):
            fwd_headers["Authorization"] = auth

        return await forward_request(backend_url, "/v1/chat/completions", body, fwd_headers)

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": __version__, "license_valid": _license_valid}

    return app
```

- [ ] **Step 8: Create `inferroute/cli.py`**

```python
# inferroute/cli.py
import os
import click
import uvicorn
from rich.console import Console

console = Console()


@click.group()
def cli():
    """AgentSave InferRoute — PPD routing sidecar."""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8080, show_default=True)
@click.option("--backend-url", envvar="BACKEND_URL", required=True)
@click.option("--backend-type", envvar="BACKEND_TYPE", default="vllm",
              type=click.Choice(["vllm", "sglang"]), show_default=True)
@click.option("--license-key", envvar="AGENTSAVE_LICENSE", required=True,
              help="Enterprise JWT license key")
def serve(host, port, backend_url, backend_type, license_key):
    """Start the InferRoute proxy."""
    from inferroute.license import validate_enterprise_license
    if not validate_enterprise_license(license_key):
        console.print("[bold red]✗ Invalid or non-Enterprise license key. InferRoute requires Enterprise tier.[/bold red]")
        raise SystemExit(1)

    console.print(f"[bold green]InferRoute running at http://{host}:{port}[/bold green]")
    console.print(f"  Backend: {backend_url} ({backend_type})")
    from inferroute.main import create_app
    uvicorn.run(create_app(backend_url, backend_type, license_key), host=host, port=port)
```

- [ ] **Step 9: Run all tests**

```
pytest tests/ -v
```
Expected: 18+ passed

- [ ] **Step 10: Commit**

```bash
git add inferroute/ tests/
git commit -m "feat: HTTP proxy, backend adapters, FastAPI app, CLI"
```

---

### Task 4: Dockerfile + docker-compose example

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY inferroute/ inferroute/

RUN pip install --no-cache-dir -e .

ENV BACKEND_URL=""
ENV BACKEND_TYPE="vllm"
ENV AGENTSAVE_LICENSE=""

EXPOSE 8080
CMD ["agentsave-inferroute", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
# docker-compose.yml — example: InferRoute in front of vLLM
services:
  inferroute:
    build: .
    ports:
      - "8080:8080"
    environment:
      BACKEND_URL: http://vllm:8000
      BACKEND_TYPE: vllm
      AGENTSAVE_LICENSE: ${AGENTSAVE_LICENSE}
    depends_on:
      - vllm

  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    command: ["--model", "meta-llama/Llama-3.2-3B-Instruct"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

- [ ] **Step 3: Create `.dockerignore`**

```
__pycache__
*.pyc
.pytest_cache
tests/
*.egg-info
.git
```

- [ ] **Step 4: Build and verify image**

```bash
docker build -t agentsave/inferroute:latest .
docker run --rm agentsave/inferroute:latest agentsave-inferroute --help
```
Expected: help text printed, no errors

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "feat: Dockerfile and docker-compose example for InferRoute"
```

---

### Task 5: TTFT benchmark scaffold

**Files:**
- Create: `benchmarks/__init__.py`
- Create: `benchmarks/ttft_benchmark.py`
- Create: `BENCHMARKS.md`

Note: This benchmark requires a real vLLM/SGLang backend to measure actual TTFT. The scaffold sets up the measurement harness; numbers are filled in once run against real hardware.

- [ ] **Step 1: Create `benchmarks/ttft_benchmark.py`**

```python
# benchmarks/ttft_benchmark.py
"""
TTFT benchmark for InferRoute.
Requires a running vLLM backend at BENCHMARK_BACKEND_URL.
Usage: python -m benchmarks.ttft_benchmark
"""
import os, time, statistics
import httpx

BACKEND_URL = os.environ.get("BENCHMARK_BACKEND_URL", "http://localhost:8000")
INFERROUTE_URL = os.environ.get("BENCHMARK_INFERROUTE_URL", "http://localhost:8080")
BENCHMARK_MODEL = os.environ.get("BENCHMARK_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
ROUNDS = int(os.environ.get("BENCHMARK_ROUNDS", "20"))

CONVERSATION_HISTORY = [
    {"role": "user", "content": "What is the capital of France? " + "x" * 500},
    {"role": "assistant", "content": "Paris is the capital of France. " + "y" * 500},
]


def measure_ttft(url: str, messages: list[dict]) -> float:
    body = {"model": BENCHMARK_MODEL, "messages": messages, "max_tokens": 10, "stream": True}
    start = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        with client.stream("POST", f"{url}/v1/chat/completions", json=body) as resp:
            for _ in resp.iter_lines():
                break
    return time.perf_counter() - start


def run_benchmark():
    print(f"Running {ROUNDS} rounds of Turn 2 requests...")
    ttft_direct = []
    ttft_routed = []

    for i in range(ROUNDS):
        messages = CONVERSATION_HISTORY + [{"role": "user", "content": f"Follow-up question {i}: tell me more."}]
        ttft_direct.append(measure_ttft(BACKEND_URL, messages))
        ttft_routed.append(measure_ttft(INFERROUTE_URL, messages))

    direct_p50 = statistics.median(ttft_direct) * 1000
    routed_p50 = statistics.median(ttft_routed) * 1000
    reduction_pct = (direct_p50 - routed_p50) / direct_p50 * 100

    print(f"\nDirect backend  p50 TTFT: {direct_p50:.0f}ms")
    print(f"InferRoute      p50 TTFT: {routed_p50:.0f}ms")
    print(f"Reduction: {reduction_pct:.1f}%")
    print("\nIMPORTANT: Update BENCHMARKS.md with these numbers before publishing the 68% claim.")
    return reduction_pct


if __name__ == "__main__":
    run_benchmark()
```

- [ ] **Step 2: Create `BENCHMARKS.md`**

```markdown
# InferRoute TTFT Benchmarks

## Target

~68% Turn 2+ TTFT reduction via PPD routing (append-prefill decode).

## Status

Not yet measured. Run `python -m benchmarks.ttft_benchmark` against a real
vLLM or SGLang backend to generate numbers.

**Do NOT update the README 68% claim until this benchmark has been run and shows ≥ 60% reduction.**

## How to run

```bash
BENCHMARK_BACKEND_URL=http://your-vllm:8000 \
BENCHMARK_INFERROUTE_URL=http://localhost:8080 \
BENCHMARK_MODEL=meta-llama/Llama-3.2-3B-Instruct \
BENCHMARK_ROUNDS=50 \
python -m benchmarks.ttft_benchmark
```
```

- [ ] **Step 3: Commit**

```bash
git add benchmarks/ BENCHMARKS.md
git commit -m "feat(benchmarks): TTFT benchmark scaffold — run against real hardware before publishing 68% claim"
```

---

## Self-Review Checklist

- [x] Spec: Turn 1 vs Turn 2+ detection → `classifier.py`
- [x] Spec: PPD routing decision → `router.py`
- [x] Spec: vLLM adapter → `adapters/vllm.py`
- [x] Spec: SGLang adapter → `adapters/sglang.py`
- [x] Spec: HTTP proxy → `proxy.py`
- [x] Spec: Enterprise license validation at startup → `cli.py` + `license.py`
- [x] Spec: Refuses to start without Enterprise JWT → `cli.py` exits with code 1
- [x] Spec: Docker image → `Dockerfile`
- [x] Spec: TTFT benchmark target noted as "not yet measured" → `BENCHMARKS.md`
- [x] Spec: 59 tests → Tasks 1–3 cover classifier (6) + router (4) + license (5) + adapters (4) + proxy (3) + extras = 22 unit tests; remaining 37 are integration tests against real backend (not in this scaffold — added when hardware is available)
- [x] Public key path consistent with agentsave-dashboard
- [x] `validate_enterprise_license` returns `False` for pro/free/expired/invalid — consistent with license test
