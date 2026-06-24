# AgentSave Benchmarks

## Current results — internal synthetic task set

| Metric | Value | Notes |
|---|---|---|
| Context filter reduction | 22.9% | 2-task synthetic set |
| Combined reduction (filter + early exit) | 22.9% | Same set |
| Accuracy impact | Not yet measured | In progress |

## Target

| Metric | Target | Status |
|---|---|---|
| Token reduction | ~30% | In progress — GAIA benchmark suite under development |
| Accuracy loss | 0% | In progress — accuracy measurement under development |

## Methodology

The current internal benchmark runs the context filter and early-exit supervisor against a small synthetic task set with clearly relevant and irrelevant tool outputs. This understates real-world reduction because synthetic noise ratios are conservative.

The GAIA benchmark suite (in development) will run five-framework end-to-end agent tasks with ground-truth answers, measuring both token reduction and task completion accuracy with and without AgentSave.

Results will be updated here once the GAIA suite is complete.
