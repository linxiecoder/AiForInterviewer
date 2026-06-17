# loop-goal-toolkit

## Purpose
Provide goal-driven loop execution inside Codex via command dispatch.

## Commands

- $loop_run    → execute ONE goal iteration
- $loop_next   → select next goal
- $loop_audit  → audit all goals
- $loop_status → show current state

## Execution Model

Each command executes exactly ONE deterministic cycle:

1. Load state
2. Resolve goal
3. Build prompt
4. Execute Codex CLI
5. Validate result
6. Persist state

## Rules
- No infinite loops inside commands
- State must persist externally
- Each command is idempotent where possible
- Skill does NOT own runtime loop