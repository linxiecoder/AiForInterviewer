---
name: large-refactor-goal-pack
description: Plan and execute large refactors through clarification, local inventory, approved Goals, bounded implementation, evidence validation, and human review before merge.
---

# Large Refactor Goal Pack

## Purpose

Use this skill for large refactors that require:

- demand clarification before coding
- structured local refactor inventory
- Goal decomposition
- bounded execution
- evidence-based validation
- human review before merge

This skill governs the refactor process. It does not replace repository governance, active product or delivery documents, tests, or human approval.

## Required Output Directory

For every refactor, create or update this local goal pack:

```text
.codex/refactors/<id>/
  00_context.md
  01_inventory.yaml
  02_goal.md
  03_validation.md
  04_execution_log.md
  05_review_notes.md
```

Use a stable, lowercase ASCII `<id>` slug. If the user does not provide an id, derive one from the refactor topic and record it in `00_context.md`.

## Hard Rules

1. Read `AGENTS.md` before planning or execution.
2. Do not modify production code during planning.
3. During inventory generation, only modify files under `.codex/refactors/<id>/`.
4. Every refactor item in `01_inventory.yaml` must contain all required item fields listed below.
5. Every Goal in `02_goal.md` must contain all required Goal sections listed below.
6. Do not execute a Goal until the inventory status is approved.
7. If scope is unclear, write `NEEDS_CONFIRMATION` and stop.
8. Completion must be backed by concrete evidence: tests, diffs, logs, generated artifacts, screenshots, or equivalent verifiable output.
9. Stop before merge and request human review. Do not commit, push, merge, release, or archive unless the user explicitly asks.

## Required Refactor Item Fields

Each item in `01_inventory.yaml` must include:

```yaml
id: RF-001
title: ""
status: proposed
problem: ""
target_state: ""
files:
  read: []
  modify: []
  do_not_touch: []
behavior_contract: []
implementation_plan: []
validation:
  baseline: []
  checkpoints: []
  final: []
risks: []
rollback: []
acceptance_criteria: []
```

The `files.read`, `files.modify`, and `files.do_not_touch` lists define the allowed inventory and execution boundary. Production edits are only allowed later for approved items and only within `files.modify`.

Recommended item statuses:

- `proposed`
- `needs_confirmation`
- `approved`
- `in_progress`
- `done`
- `blocked`
- `deferred`
- `rejected`

## Required Goal Sections

Every Goal in `02_goal.md` must include:

- Objective
- Source of truth
- Approved scope
- Non-goals
- Boundaries
- Checkpoints
- Validation commands
- Stop conditions
- Completion criteria
- Final report format

## Planning Mode

Use this mode when the user asks to plan, inventory, size, decompose, scope, or prepare a refactor.

Steps:

1. Read `AGENTS.md`.
2. Identify or create the refactor id.
3. Inspect relevant source and test files read-only.
4. Ask at most 5 blocking questions.
5. If a blocking question prevents safe planning, write `NEEDS_CONFIRMATION` in the local goal pack and stop.
6. Generate or update:
   - `.codex/refactors/<id>/00_context.md`
   - `.codex/refactors/<id>/01_inventory.yaml`
7. Stop before touching implementation files.

`00_context.md` should record:

- refactor id and title
- user request
- current repository and branch context
- source of truth documents or code paths
- relevant files inspected
- assumptions
- blocking questions
- out-of-scope areas
- planning status

`01_inventory.yaml` should record:

- refactor id and inventory status
- item list with complete required fields
- approval status for each item
- known dependencies between items
- scope questions and unresolved risks

If the inventory status is not approved, execution is forbidden.

## Goal Generation Mode

Use this mode when the user asks to generate a Goal from the inventory.

Steps:

1. Read `AGENTS.md`.
2. Read `.codex/refactors/<id>/01_inventory.yaml`.
3. Include only items with `status: approved`.
4. If no approved items exist, write `NEEDS_CONFIRMATION` and stop.
5. Generate or update:
   - `.codex/refactors/<id>/02_goal.md`
   - `.codex/refactors/<id>/03_validation.md`
6. Ensure the Goal is small enough to execute safely.
7. Split the Goal if approved items span unrelated modules, unrelated behavior, or unrelated validation surfaces.
8. Stop before touching implementation files unless the user explicitly asks to execute an approved Goal.

`02_goal.md` must use this structure:

```markdown
# Goal: <short title>

## Objective

## Source of Truth

## Approved Scope

## Non-goals

## Boundaries

## Checkpoints

## Validation Commands

## Stop Conditions

## Completion Criteria

## Final Report Format
```

`03_validation.md` should include:

- baseline validation commands
- checkpoint validation commands
- final validation commands
- expected evidence artifacts
- known test gaps
- environment assumptions
- risk-based manual checks

## Execution Mode

Use this mode only when the user asks to execute an approved Goal.

Preconditions:

- `01_inventory.yaml` exists.
- Inventory status is approved, or the specific target items are `status: approved`.
- `02_goal.md` and `03_validation.md` exist.
- The requested execution scope is inside the approved `files.modify` boundary.

Steps:

1. Read `AGENTS.md`.
2. Read `01_inventory.yaml`, `02_goal.md`, and `03_validation.md`.
3. Run baseline validation first.
4. Work item by item.
5. After each checkpoint, run the relevant tests or validation commands.
6. Update `.codex/refactors/<id>/04_execution_log.md` after each material action.
7. Update `.codex/refactors/<id>/05_review_notes.md` before the final response.
8. Stop before merge and request human review.

`04_execution_log.md` should record:

- timestamp or turn marker
- item id
- files changed
- commands run
- validation result
- evidence path or output summary
- decision made
- next checkpoint

`05_review_notes.md` should record:

- completed RF items
- changed files
- behavior changes
- tests run
- tests added or updated
- evidence summary
- risks and residual gaps
- rollback notes
- human review status

## Mandatory Stop Conditions

Stop and report before continuing if:

- public API change is needed but not approved
- tests fail for unclear reasons
- edit scope exceeds approved boundaries
- business rule is ambiguous
- dependency upgrade is required but not approved
- inventory status is not approved
- a required source of truth conflicts with the requested change
- generated evidence is missing or inconclusive

When stopped for unclear scope, write `NEEDS_CONFIRMATION` to the relevant goal pack files and do not edit implementation files.

## Final Response Format

At completion, report:

- completed RF items
- changed files
- tests run
- tests added or updated
- behavior changes
- risks
- follow-up work
- rollback notes

Also state whether human review is still required before merge.

## Forbidden Actions

- Do not treat the local goal pack as an active product, design, delivery, or roadmap source of truth.
- Do not create new roadmap, plan-v2, latest-plan, codex-plan, or parallel task-system documents.
- Do not modify production code while planning or generating inventory.
- Do not execute unapproved inventory items.
- Do not expand execution beyond `files.modify` without explicit user approval.
- Do not hide failed validation, skipped tests, or missing evidence.
