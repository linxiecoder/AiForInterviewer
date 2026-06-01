---
title: README
type: entry
status: active-f0
permalink: ai-for-interviewer/readme
---

# AiForInterviewer

Open-source AI interview workbench and agentic AI reference implementation.

## Project Overview

AiForInterviewer is an AI interview workbench for real job preparation. It is built around resumes, job descriptions, job-match analysis, interview practice, scoring, review, weak-point training, and reusable interview assets.

It is not a generic chatbot, an applicant tracking system, or a recruiting management system. The product scope focuses on helping an interview candidate prepare, review, and improve against a specific resume and target job.

The current source of truth for active documentation is [`docs/00-governance/DOCS_INDEX.md`](docs/00-governance/DOCS_INDEX.md). Most active project documents are currently written in Chinese; this README is written in English for external OSS readers and review contexts.

## Why This Project Exists

Interview preparation is repetitive, difficult to personalize, and hard to evaluate consistently. Generic Q&A sessions often lose the connection between resume evidence, job requirements, prior answers, scoring rationale, weak points, and reusable materials.

AiForInterviewer aims to make interview preparation structured, traceable, reviewable, and reusable. The project treats resume/JD context, interview sessions, feedback, reports, reviews, weak points, and assets as connected product objects instead of disposable chat turns.

## Core Capabilities

The MVP scope and product design cover the following capabilities. Implementation status for each area is governed by [`docs/03-delivery/BACKLOG.md`](docs/03-delivery/BACKLOG.md) and [`docs/03-delivery/DELIVERY_PLAN.md`](docs/03-delivery/DELIVERY_PLAN.md).

- Resume and JD management, with Markdown resume input and manually entered job/JD records.
- Resume/JD matching analysis with 0-100 product-level scoring, match points, gaps, improvement points, evidence summaries, and weak-point suggestions.
- RAG-backed interview context using resume content, job requirements, assets, prior reports, reviews, weak points, and source availability rules.
- Polish mode for multi-round improvement across project experience, self-introduction, technical topics, soft skills, behavioral questions, and job-match gaps.
- Pressure interview mode for realistic continuous Q&A, follow-up pressure, session-level evaluation, and report handoff.
- 0-100 scoring and structured feedback for matching, polish rounds, interview reports, and review flows, with scoring governance handled by active design docs.
- Interview reports, mock interview reviews, real interview reviews, copyable report content, and review records.
- Weak-point extraction, evidence-backed training recommendations, and feedback loops into future interview sessions.
- Asset library for reusable interview preparation materials derived from polish sessions, reports, reviews, weak points, and user-curated content.
- User-visible states for low confidence, source unavailable, validation failed, generation failed, partial availability, and insufficient material.

## OSS Reference Value

AiForInterviewer is also intended as a reference implementation for agentic AI products that need governance beyond a prompt-and-chat UI:

- Reference architecture for AI-assisted product workflows with clear business object boundaries.
- Prompt contract governance, prompt asset registry direction, and prompt evaluation planning.
- LLM trace, evidence, validation, redaction, and privacy boundary design.
- Candidate/suggestion objects separated from formal business objects.
- RAG evidence handling with source availability and owner/scope checks.
- Scoring governance with versioned rubric design and hidden scoring-rule boundaries.
- Staged LangGraph runtime migration with default-off execution, raw-off payload handling, checkpoint non-truth-source rules, and Core/AI Runtime separation.
- Codex-assisted maintainer workflow potential for PR review, issue triage, regression analysis, schema and prompt validation, test generation, release notes, and safe refactoring.

## Architecture And AI Runtime Direction

The documented architecture direction is a single backend service with two domains:

- Core Business Domain for authoritative business objects, commands, ownership, persistence, and user-confirmed writes.
- AI Agentic Workflow Domain for agent runs, runtime metadata, traces, interrupt/resume flow, graph descriptors, and AI workflow orchestration.

[`ADR-0005`](docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md) is currently `Proposed`, not `Accepted`. It documents Option C as the candidate long-term direction for PR2-PR8, while PR2 is limited to a conditional, default-off runtime foundation.

Key runtime boundaries:

- Core business code must not depend directly on LangGraph, graph node state, checkpoint schema, or provider payloads.
- AI Runtime should be reached through a facade or application port.
- LangGraph concrete imports belong under the AI Runtime infrastructure boundary, not the Core domain.
- Checkpoints are runtime recovery, resume, replay, and debug state; they are not business truth.
- Raw prompts, raw completions, provider request/response payloads, tokens, secrets, cookies, system prompts, and hidden scoring rules are not stored or exposed by default.
- AI nodes may produce structured results, candidates, suggestions, validations, low-confidence states, traces, or interrupts.
- Formal business objects require a Core command, explicit user confirmation, or another explicit business action.
- LangGraph migration is staged and guarded. PR2 is `CONDITIONAL GO` for inert runtime data/repository/tests only; runtime enablement, graph execution, real provider calls, frontend UI, and business graph migration require later explicit scope.

See the LangGraph implementation entry at [`docs/03-delivery/refactor-multiagent-langgraph-implementation/README.md`](docs/03-delivery/refactor-multiagent-langgraph-implementation/README.md) and the backend migration plan at [`docs/03-delivery/refactor-multiagent-langgraph-implementation/02_BACKEND_REFACTOR_MASTER_PLAN.md`](docs/03-delivery/refactor-multiagent-langgraph-implementation/02_BACKEND_REFACTOR_MASTER_PLAN.md).

## Current Status

This repository is public and has an active documentation/governance system. Product requirements and design docs define the MVP scope, non-goals, active object model, scoring boundaries, privacy boundaries, prompt contracts, and release handoff expectations.

As of the active delivery plan, F0-F3 are marked `DONE`, F4 is `ACCEPTED`, F5 is `READY_TO_START`, and F6-F8 are `NOT_STARTED`. Backend, frontend, test, and release readiness should always be read from [`BACKLOG.md`](docs/03-delivery/BACKLOG.md) and [`DELIVERY_PLAN.md`](docs/03-delivery/DELIVERY_PLAN.md), not inferred from README text.

Some AI Runtime and LangGraph work is documented as design, planning, accepted risk, or staged implementation direction depending on the active backlog entry. This README does not claim production readiness, full LangGraph integration, completed release status, enterprise adoption, security certification, or user-scale metrics.

## Repository Map And Documentation

Current active documentation is governed by [`docs/00-governance/DOCS_INDEX.md`](docs/00-governance/DOCS_INDEX.md). Archive content is historical evidence only and must not be used as current execution basis.

| Area | Entry |
|---|---|
| Active docs index | [`docs/00-governance/DOCS_INDEX.md`](docs/00-governance/DOCS_INDEX.md) |
| Collaboration rules | [`AGENTS.md`](AGENTS.md) |
| Documentation governance | [`docs/00-governance/DOCS_GOVERNANCE.md`](docs/00-governance/DOCS_GOVERNANCE.md) |
| AI workflow governance | [`docs/00-governance/AI_WORKFLOW.md`](docs/00-governance/AI_WORKFLOW.md) |
| Product requirements | [`docs/01-product/PRD.md`](docs/01-product/PRD.md) |
| Requirement traceability | [`docs/01-product/REQUIREMENT_TRACEABILITY.md`](docs/01-product/REQUIREMENT_TRACEABILITY.md) |
| Delivery plan | [`docs/03-delivery/DELIVERY_PLAN.md`](docs/03-delivery/DELIVERY_PLAN.md) |
| Backlog | [`docs/03-delivery/BACKLOG.md`](docs/03-delivery/BACKLOG.md) |
| LangGraph ADR | [`docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md`](docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md) |
| LangGraph implementation entry | [`docs/03-delivery/refactor-multiagent-langgraph-implementation/README.md`](docs/03-delivery/refactor-multiagent-langgraph-implementation/README.md) |
| Security and privacy design | [`docs/02-design/SECURITY_PRIVACY.md`](docs/02-design/SECURITY_PRIVACY.md) |
| Archive boundary | [`archive/README.md`](archive/README.md) |
| Archive manifest | [`archive/MANIFEST.md`](archive/MANIFEST.md) |

## Repository Governance

- [`docs/00-governance/DOCS_INDEX.md`](docs/00-governance/DOCS_INDEX.md) is the current active documentation entry.
- `archive/` is historical source material only; archive docs cannot be used as current execution basis.
- Current phases use only `F0` through `F8`.
- Current milestones use only `M0` through `M8`.
- Current task IDs use only `AIFI-*`.
- Current priorities use only `MUST`, `SHOULD`, `COULD`, and `LATER`.
- New work should enter the active backlog and delivery governance flow instead of creating parallel roadmaps, plan-v2 files, or temporary task systems.

## Getting Started

For project understanding:

1. Start with [`docs/00-governance/DOCS_INDEX.md`](docs/00-governance/DOCS_INDEX.md).
2. Read [`docs/01-product/PRD.md`](docs/01-product/PRD.md) for product scope, MVP success criteria, non-goals, and UNKNOWN handling.
3. Use [`docs/03-delivery/BACKLOG.md`](docs/03-delivery/BACKLOG.md) for current task state.
4. Use [`docs/03-delivery/DELIVERY_PLAN.md`](docs/03-delivery/DELIVERY_PLAN.md) for phase and milestone state.
5. Use [`ADR-0005`](docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md) and the LangGraph implementation docs for AI Runtime direction.

Local setup and verification commands are intentionally not expanded here. Follow [`AGENTS.md`](AGENTS.md), active delivery docs, and the current backlog before treating any local command as stable.

## Contributing

There is no `CONTRIBUTING.md` in the repository at the time of this README refresh. Contributions should follow:

- [`AGENTS.md`](AGENTS.md)
- [`docs/00-governance/DOCS_INDEX.md`](docs/00-governance/DOCS_INDEX.md)
- [`docs/00-governance/AI_WORKFLOW.md`](docs/00-governance/AI_WORKFLOW.md)
- [`docs/03-delivery/BACKLOG.md`](docs/03-delivery/BACKLOG.md)

Contribution boundaries:

- Respect active-doc source-of-truth boundaries.
- Do not use archive docs as current execution basis.
- Do not introduce raw prompt, raw completion, provider payload, token, secret, hidden scoring-rule, or personal resume/JD exposure.
- Keep candidate/suggestion and formal object handoff boundaries intact.
- Preserve owner, privacy, trace, source availability, low-confidence, and validation-failed semantics.
- Do not add recruiting management, ATS, voice/video, file export, exact pass-probability prediction, or enterprise governance features unless they are accepted into active docs and backlog scope.

## Security And Privacy

There is no root `SECURITY.md` in the repository at the time of this README refresh. The active design entry for security and privacy is [`docs/02-design/SECURITY_PRIVACY.md`](docs/02-design/SECURITY_PRIVACY.md).

Project principles:

- Do not commit secrets, provider keys, tokens, cookies, database credentials, real DSNs, or private personal data.
- Do not expose provider payloads, raw prompts, raw completions, system prompts, hidden scoring rules, or personal resume/JD data in logs, API responses, trace views, copy content, or public issues.
- Treat resume, JD, interview answers, reports, reviews, assets, weak points, RAG sources, and trace metadata as owner-scoped sensitive data.
- Report security concerns through the safest available project channel. If only public GitHub issues are available, avoid posting secrets, credentials, private resumes, JDs, provider payloads, or other personal data.

## Codex And Maintainer Workflow

AiForInterviewer is a good fit for Codex-assisted OSS maintenance because the repository already emphasizes explicit docs, traceability, task IDs, active/archive boundaries, and implementation gates.

Potential maintainer workflows include:

- PR review against active specs and architecture boundaries.
- Issue triage against PRD scope, non-goals, and backlog state.
- Large-scale refactoring with source-of-truth and scope-lock checks.
- Test generation for API, data, prompt, privacy, and regression boundaries.
- Prompt/schema evaluation and validation fixture updates.
- Release note and known-limitation drafting from active delivery docs.
- Architecture and documentation consistency checks across PRD, design docs, ADRs, backlog, and implementation plans.

This project has not been approved, sponsored, or endorsed by OpenAI unless a future active document says so explicitly.

## License

License: not specified yet.
