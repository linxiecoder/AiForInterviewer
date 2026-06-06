---
title: WINDOW_RESULT_DIGEST
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/templates/window-result-digest
---

# Window Result Digest Template

Use this for every window, even if the full Codex output is longer.

```md
## Window

Window ID:
Phase:
Capability IDs:

## Repository evidence

Branch:
Commit before:
Commit after:
Dirty status before:
Dirty status after:

## Decision

Result:
- GREEN / AMBER / RED / BLOCKED / FAILED / DONE-CANDIDATE

One-paragraph rationale:

## Files changed

- 

## Tests / evals

| Command | Result | Notes |
|---|---|---|
|  |  |  |

## Capability status changes proposed

| Capability ID | Previous | Proposed | Evidence | Confidence |
|---|---|---|---|---|
|  |  |  |  |  |

## Source backfill required

- Traceability Matrix:
- Decision Log:
- Risk Register:
- Acceptance Gates:
- Phase Roadmap:

## Stop condition triggered?

Yes / No

If yes, explain:

## Remaining risks

- 

## Next recommended window

Window ID:
Reason:
```