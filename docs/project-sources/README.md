---
title: README
type: note
permalink: ai-for-interviewer/docs/project-sources/readme
---

# Project Sources

`docs/project-sources/**` is the active Project source pack for controller / Codex windows. It records target architecture, governance rules, source-of-truth policy, acceptance gates, risk / decision anchors, and execution window protocol for the Project source hierarchy.

`docs/goals/**` is execution evidence only. Goal records, closeout reports, backfill deltas, and validation notes do not become active source of truth unless a later authorized window writes the corresponding fact into active Project source docs, active delivery docs, ADR, or code.

GitHub current code describes the current implementation. `docs/project-sources/**` describes target architecture and governance intent. When current code, active docs, Project source docs, or goal evidence disagree, the conflict must be recorded as an explicit gap instead of silently overwriting one source with another.

## Boundary

- Do not copy `docs/goals/**` evidence reports into `docs/project-sources/**`.
- Do not reconstruct Project source files from condensed excerpts.
- Do not treat `archive/**` as active Project source.
- Do not use this directory to authorize implementation outside the active `BACKLOG.md`, `DELIVERY_PLAN.md`, ADR, and current window allowlist.
