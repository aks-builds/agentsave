# Changelog

All notable changes to AgentSave will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `supervise(agent)` drop-in wrapper for LangChain, LangGraph, AutoGen, CrewAI, and Smolagents
- TF-IDF cosine similarity context filter — removes redundant tool outputs before LLM call, <1ms overhead per observation
- Token reduction averaging ~29.68% on GAIA benchmark (arXiv:2510.26585, ICLR 2026)
- Five framework adapters: `LangChainAdapter`, `LangGraphAdapter`, `AutoGenAdapter`, `CrewAIAdapter`, `SmolagentsAdapter`
- Opt-in telemetry client — emits run_id, framework, model, token counts, success flag only; no PII
- `agentsave login` CLI command for dashboard authentication
- `agentsave status` CLI command to view current config and connection state
- Dashboard backend (FastAPI + SQLite) — receives telemetry events via `POST /api/events`
- Dashboard backend JWT authentication — `POST /api/auth/login`, `GET /api/auth/me`
- Dashboard backend API endpoints: runs, analytics, cost projections, framework breakdowns
- `GET /api/events/recent` endpoint — returns 10 most recent events ordered by timestamp DESC
- Real-time cost savings dashboard (Next.js 14, App Router)
- Stat cards: Tokens Saved, Cost Saved, Success Rate, Total Runs — with sparklines and animated counters
- Area chart — token savings over time, dual-series (Saved / Baseline), Area/Line/Bar tab toggle
- Framework donut chart — per-framework token savings breakdown
- Agent Runs table — paginated, with framework badges, status glow dots, reduction percentage
- Cost Projector — three interactive sliders (runs, tokens/run, cost/1M tokens), live calculation
- Live Activity Feed — polls `/api/events/recent` every 5 seconds, Framer Motion slide-in
- Hourly Heatmap — GitHub contribution-style grid, 4-week view, intensity by run count
- Command palette (cmdk, ⌘K / Ctrl+K) — navigate, actions, settings commands
- Toast notifications (Sonner) — run saved, run failed, token created, upgrade prompt
- Dark/Light mode toggle (next-themes) — dark default
- Responsive layout — full sidebar ≥1024px, icon-only 768–1024px, bottom tab bar <768px
- Billing page — Free / Pro / Team tier cards with upgrade CTAs
- API Keys page — token creation, masked display, copy to clipboard
- InferRoute Docker sidecar — PPD append-prefill decode routing, ~68% Turn 2+ TTFT reduction (arXiv:2603.13358, ICML 2026)
- 60 SDK unit tests, 44 dashboard tests, 59 InferRoute tests, 17 E2E Playwright tests
- MIT license, Contributor Covenant v2.1 Code of Conduct, SECURITY policy, CONTRIBUTING guide
- GitHub Actions CI: sdk-tests, dashboard-tests, inferroute-tests, playwright E2E
