---
title: 12_AGENT_C_RUNNER_CI_RECON
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/12-agent-c-runner-ci-recon
---

# Agent C — Runner, Report, and CI Recon

Role: read-only design/recon agent.

Goal: design the minimal eval runner, report format, and CI gate using current repo conventions.

Inspect:

- Python packaging and script conventions: `pyproject.toml`, `pytest.ini`, `Makefile`, `scripts/**`
- CI conventions: `.github/workflows/**`
- Existing reports under `docs/goals/**`
- Existing JSON/Markdown report patterns

Output file: `docs/goals/2026-06-06/P9_AGENT_C_RUNNER_CI_RECON.md`

Required report sections:

1. Existing Runner/Script Conventions
2. Recommended Runner Entrypoint
3. Recommended CLI Arguments
4. Report Schema
5. CI Job Design
6. Non-Secret Default Mode
7. Negative-Control Gate Design
8. Validation Commands
9. Minimal File Change Plan

Runner requirements:

- non-zero exit on blocking failure
- replay/fixture default mode
- optional real provider mode must be skipped by default
- report includes commit, suite, dataset digest, grader versions, mode, pass/fail/skip, blocking failures, deferred gaps, and non-claims

Rules:

- Do not patch.
- Do not propose default CI that requires provider secrets.
- Do not alter web frontend unless CI convention requires a package script; if needed, justify.