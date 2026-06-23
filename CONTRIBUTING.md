# Contributing to AgentSave

Thank you for your interest in contributing to AgentSave! This guide covers
everything you need to get set up and make your first contribution.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for InferRoute only — requires virtualization enabled in BIOS)
- Git

## Setup

Clone all three repos into the same parent directory:

```bash
git clone https://github.com/aks-builds/agentsave.git
git clone https://github.com/aks-builds/agentsave-dashboard.git
git clone https://github.com/aks-builds/agentsave-inferroute.git
git clone https://github.com/aks-builds/agentsave-ui.git
```

Install dependencies for each:

```bash
# SDK
cd agentsave
pip install -e ".[dev]"

# Dashboard backend
cd ../agentsave-dashboard
pip install -r requirements-dev.txt

# InferRoute
cd ../agentsave-inferroute
pip install -r requirements-dev.txt

# UI
cd ../agentsave-ui
npm install
```

## Development Workflow

1. Create a feature branch from `main`: `git checkout -b feat/your-feature`
2. Make your changes with tests
3. Run the relevant test suite (see below)
4. Push and open a pull request against `main`
5. Ensure all CI checks pass before requesting review

## Running Tests

**SDK tests:**
```bash
cd agentsave
pytest tests/ -v
```

**Dashboard backend tests:**
```bash
cd agentsave-dashboard
pytest tests/ -v
```

**InferRoute tests:**
```bash
cd agentsave-inferroute
pytest tests/ -v
```

**Playwright E2E tests** (requires UI running at http://localhost:3000 and dashboard at http://localhost:8000):
```bash
# Terminal 1 — start dashboard backend
cd agentsave-dashboard
uvicorn main:app --reload --port 8000

# Terminal 2 — start UI
cd agentsave-ui
npm run dev

# Terminal 3 — run E2E
cd agentsave-ui
npx playwright test
```

## Code Style

**Python:** Follow PEP 8. Use `black` for formatting and `ruff` for linting:
```bash
black agentsave/ tests/
ruff check agentsave/ tests/
```

**TypeScript/React:** Follow the ESLint config in `agentsave-ui/.eslintrc.json`. Run:
```bash
cd agentsave-ui
npm run lint
```

No `any` types in new TypeScript code. All new React components must have explicit prop types.

## PR Checklist

Before submitting a pull request, confirm all of the following:

- [ ] Tests added or updated for all changed behaviour
- [ ] All existing tests pass (`pytest tests/ -v` / `npm test`)
- [ ] No placeholder values (`TODO`, `FIXME`, `[placeholder]`) left in the diff
- [ ] Playwright E2E tests pass if any UI files were changed
- [ ] CHANGELOG.md updated under `[Unreleased]` with a one-line description of the change

## Commit Message Format

Use the Conventional Commits format:

```
<type>(<scope>): <short summary>

[optional body]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`

Examples:
```
feat(sdk): add SmolagentsAdapter with context filter support
fix(dashboard): correct token reduction calculation for zero-token runs
test(e2e): add Playwright test for command palette navigation
docs(readme): add InferRoute Docker quick-start instructions
```

Scope is optional but recommended: `sdk`, `dashboard`, `inferroute`, `ui`, `ci`, `docs`.
