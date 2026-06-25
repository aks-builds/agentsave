# AgentSave Benchmarks

## Current results — 20-task benchmark set

| Metric | Value | Notes |
|---|---|---|
| Token reduction | 23.2% | 20-task set |
| Accuracy without AgentSave | 100.0% | Baseline |
| Accuracy with AgentSave | 100.0% | Supervised |
| Accuracy delta | +0.0% | 0% = no loss |

## Target

| Metric | Target | Status |
|---|---|---|
| Token reduction | ~30% | In progress (23.2%) |
| Accuracy loss | 0% | ✓ Met |

## Per-task results

| Task | Tokens before | Tokens after | Reduction | Answer correct (w/o) | Answer correct (with) |
|---|---|---|---|---|---|
| tokyo-population | 76 | 76 | 0.0% | ✓ | ✓ |
| telephone-inventor | 56 | 31 | 44.6% | ✓ | ✓ |
| python-creator | 53 | 53 | 0.0% | ✓ | ✓ |
| mount-everest-height | 82 | 67 | 18.3% | ✓ | ✓ |
| water-boiling-point | 50 | 28 | 44.0% | ✓ | ✓ |
| speed-of-light | 75 | 57 | 24.0% | ✓ | ✓ |
| french-capital | 66 | 49 | 25.8% | ✓ | ✓ |
| shakespeare-birth-year | 53 | 43 | 18.9% | ✓ | ✓ |
| amazon-river | 55 | 55 | 0.0% | ✓ | ✓ |
| dna-structure | 65 | 37 | 43.1% | ✓ | ✓ |
| gravity-constant | 70 | 22 | 68.6% | ✓ | ✓ |
| periodic-table-gold | 46 | 46 | 0.0% | ✓ | ✓ |
| wwii-end-year | 62 | 39 | 37.1% | ✓ | ✓ |
| human-chromosomes | 46 | 24 | 47.8% | ✓ | ✓ |
| moon-distance | 54 | 44 | 18.5% | ✓ | ✓ |
| titanic-sinking-year | 52 | 52 | 0.0% | ✓ | ✓ |
| carbon-symbol | 48 | 48 | 0.0% | ✓ | ✓ |
| pi-value | 67 | 54 | 19.4% | ✓ | ✓ |
| human-heart-chambers | 55 | 55 | 0.0% | ✓ | ✓ |
| internet-inventor | 74 | 46 | 37.8% | ✓ | ✓ |

## Methodology

Each task has a goal, 3–5 tool outputs (mix of relevant and noise), and a ground-truth answer.
The runner simulates two agents: one receiving all outputs, one supervised by AgentSave.
Accuracy is fuzzy-matched (substring or ≥0.6 sequence similarity).
_Run `python -m benchmarks.runner` to regenerate this file._
