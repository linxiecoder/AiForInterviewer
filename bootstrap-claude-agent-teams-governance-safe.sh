#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d%H%M%S)"
BACKUPS=()
WRITTEN=()
WARNINGS=()

die() {
  echo "ERROR: $*" >&2
  exit 1
}

note_backup() {
  BACKUPS+=("$1")
}

note_written() {
  WRITTEN+=("$1")
}

backup_file() {
  local file="$1"
  if [[ -e "$file" ]]; then
    local backup="${file}.bak.${TS}"
    cp -p "$file" "$backup"
    note_backup "$backup"
  fi
}

install_file() {
  local target="$1"
  mkdir -p "$(dirname "$target")"
  if [[ -e "$target" ]]; then
    backup_file "$target"
  fi
  cat > "$target"
  note_written "$target"
}

ensure_repo_root() {
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    cd "$(git rev-parse --show-toplevel)"
  else
    die "当前目录不是 git 仓库。请在 AiForInterviewer 仓库内执行。"
  fi
}

detect_prd() {
  if [[ -f "docs/01-product/PRD.md" ]]; then
    echo "docs/01-product/PRD.md"
  elif [[ -f "PRD.md" ]]; then
    echo "PRD.md"
  else
    WARNINGS+=("未找到 docs/01-product/PRD.md 或 PRD.md；脚本仍会安装配置，但后续 Agent Team 启动前应先确认 PRD 位置。")
    echo "docs/01-product/PRD.md"
  fi
}

ensure_gitignore_lines() {
  local file=".gitignore"
  touch "$file"

  local before
  before="$(cat "$file")"

  local lines=(
    ".claude/worktrees/"
    "!.claude/settings.json"
    "!.claude/agents/"
    "!.claude/agents/*.md"
    "!.claude/skills/"
    "!.claude/skills/**"
    "!.claude/hooks/"
    "!.claude/hooks/*.sh"
  )

  local changed=0
  for line in "${lines[@]}"; do
    if ! grep -qxF "$line" "$file"; then
      changed=1
    fi
  done

  if [[ "$changed" -eq 1 ]]; then
    backup_file "$file"
    {
      printf "\n# Claude Code Agent Teams\n"
      for line in "${lines[@]}"; do
        if ! grep -qxF "$line" "$file"; then
          printf "%s\n" "$line"
        fi
      done
    } >> "$file"
    note_written "$file"
  fi

  if [[ "$before" == "$(cat "$file")" ]]; then
    :
  fi
}

merge_settings_json() {
  mkdir -p .claude
  touch .claude/settings.json

  if [[ -s ".claude/settings.json" ]]; then
    python3 -m json.tool .claude/settings.json >/dev/null || die ".claude/settings.json 不是合法 JSON。请先修复后再运行。"
  else
    printf "{}\n" > .claude/settings.json
  fi

  backup_file ".claude/settings.json"

  python3 - <<'PY'
import json
from pathlib import Path

path = Path(".claude/settings.json")
data = json.loads(path.read_text(encoding="utf-8") or "{}")

def ensure_dict(parent, key):
    value = parent.get(key)
    if not isinstance(value, dict):
        value = {}
        parent[key] = value
    return value

def ensure_list(parent, key):
    value = parent.get(key)
    if not isinstance(value, list):
        value = []
        parent[key] = value
    return value

def merge_unique_list(parent, key, items):
    arr = ensure_list(parent, key)
    seen = set(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in arr)
    for item in items:
        encoded = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if encoded not in seen:
            arr.append(item)
            seen.add(encoded)

env = ensure_dict(data, "env")
env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"

# 用户要求固定 in-process；如果当前 Claude Code 版本不识别该字段，可启动时继续使用 --teammate-mode in-process。
data["teammateMode"] = "in-process"

permissions = ensure_dict(data, "permissions")
permissions["defaultMode"] = "plan"

merge_unique_list(permissions, "allow", [
    "Bash(pwd)",
    "Bash(git status)",
    "Bash(git status *)",
    "Bash(git diff *)",
    "Bash(git log *)",
    "Bash(git branch *)",
    "Bash(git grep *)",
    "Bash(npm run lint *)",
    "Bash(npm run test *)",
    "Bash(npm run typecheck *)",
    "Bash(npm run build *)",
    "Bash(pnpm lint *)",
    "Bash(pnpm test *)",
    "Bash(pnpm typecheck *)",
    "Bash(pnpm build *)",
    "Bash(yarn lint *)",
    "Bash(yarn test *)",
    "Bash(yarn typecheck *)",
    "Bash(yarn build *)"
])

merge_unique_list(permissions, "ask", [
    "Bash(git checkout *)",
    "Bash(git switch *)",
    "Bash(git commit *)",
    "Bash(git merge *)",
    "Bash(git rebase *)",
    "Bash(git reset *)",
    "Bash(git restore *)"
])

merge_unique_list(permissions, "deny", [
    "Read(.env)",
    "Read(.env.*)",
    "Read(secrets/**)",
    "Read(**/secrets/**)",
    "Read(credentials)",
    "Read(**/credentials)",
    "Read(**/credentials.json)",
    "Read(**/*.pem)",
    "Read(**/*.key)",
    "Read(**/*.p12)",
    "Read(**/*.pfx)",
    "Bash(git push *)",
    "Bash(git reset --hard *)",
    "Bash(git clean -fd *)",
    "Bash(rm -rf *)",
    "Bash(kubectl delete *)",
    "Bash(terraform apply *)",
    "Bash(pulumi up *)",
    "Bash(aws * delete *)",
    "Bash(gcloud * delete *)",
    "Bash(az * delete *)",
    "Bash(chmod -R 777 *)",
    "Bash(sudo *)"
])

hooks = ensure_dict(data, "hooks")

pre_hooks = hooks.get("PreToolUse")
if not isinstance(pre_hooks, list):
    pre_hooks = []
    hooks["PreToolUse"] = pre_hooks

new_pre_hooks = [
    {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": "\"${CLAUDE_PROJECT_DIR}/.claude/hooks/block-dangerous-bash.sh\""
            }
        ]
    },
    {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
            {
                "type": "command",
                "command": "\"${CLAUDE_PROJECT_DIR}/.claude/hooks/protect-files.sh\""
            }
        ]
    }
]

seen = set(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in pre_hooks)
for item in new_pre_hooks:
    encoded = json.dumps(item, ensure_ascii=False, sort_keys=True)
    if encoded not in seen:
        pre_hooks.append(item)
        seen.add(encoded)

path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  note_written ".claude/settings.json"
}

update_claude_md() {
  local prd_path="$1"
  touch CLAUDE.md

  python3 - "$TS" "$prd_path" <<'PY'
import re
import sys
from pathlib import Path

ts = sys.argv[1]
prd_path = sys.argv[2]

path = Path("CLAUDE.md")
old = path.read_text(encoding="utf-8") if path.exists() else ""

start = "<!-- BEGIN CLAUDE_AGENT_TEAMS_GOVERNANCE_SAFE -->"
end = "<!-- END CLAUDE_AGENT_TEAMS_GOVERNANCE_SAFE -->"

section = f"""{start}

# Claude Code Agent Teams Policy

本节为 Claude Code Agent Teams 的项目级执行补充规则。它不得覆盖 `AGENTS.md`、`docs/00-governance/DOCS_INDEX.md` 或仓库已有治理规则。

## Source of truth

当前项目事实源优先级：

1. `AGENTS.md`
2. `docs/00-governance/DOCS_INDEX.md`
3. `{prd_path}`
4. `docs/03-delivery/DELIVERY_PLAN.md`
5. `docs/03-delivery/BACKLOG.md`
6. `docs/01-product/REQUIREMENT_TRACEABILITY.md`
7. `docs/04-decisions/ADR-*.md`

禁止把 `archive/` 下内容作为当前执行依据。若历史内容仍有效，必须先迁入 active docs 并登记。

## Default workflow

对于任何非平凡任务：

1. 先读取 `AGENTS.md`、`docs/00-governance/DOCS_INDEX.md` 和当前任务相关 active docs。
2. 修改前说明影响范围、将修改的文件、不会修改的文件、风险点、验证方式。
3. 默认使用 `plan` 模式先探索和给计划。
4. 不创建新的并行 roadmap、plan、task、phase 体系。
5. 阶段类内容进入 `docs/03-delivery/DELIVERY_PLAN.md`。
6. 任务类内容进入 `docs/03-delivery/BACKLOG.md`。
7. 需求追踪进入 `docs/01-product/REQUIREMENT_TRACEABILITY.md`。
8. 长期架构或治理决策才进入 `docs/04-decisions/ADR-*.md`。
9. 完成后输出 `git status --short`、`git diff --stat`、新增/修改清单、验证结果和仍需确认项。

## Agent Teams usage

可以使用 Agent Teams 处理：

- PRD 拆解和需求澄清
- API contract 设计
- 后端架构设计
- 前端流程和高保真实现计划
- QA / E2E / contract test 策略
- security / privacy review
- devops / CI / release gate 设计
- 集成一致性审查
- bounded implementation slice 的并行计划和复审

不得使用 Agent Teams 做：

- 多个 teammates 同时编辑同一文件
- 无边界全仓库重写
- 生产操作
- secrets / credentials / 私钥读取或编辑
- destructive database / infra / deployment 操作
- 绕过 `DELIVERY_PLAN.md` 和 `BACKLOG.md` 的并行计划体系

## High-risk areas requiring human approval

以下区域必须人工批准后才能修改：

- database migration
- authentication / authorization
- billing / payment
- deployment configuration
- production data
- secrets / credentials
- infrastructure as code
- destructive command
- git push / release / publish

## Definition of done

任务完成必须包含：

- scope summary
- changed files
- validation commands and results
- risk summary
- open questions
- next recommended task
- old-system / parallel-plan residue check when documentation is touched

{end}
"""

if start in old and end in old:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    new = pattern.sub(section, old)
else:
    new = old.rstrip() + "\n\n" + section + "\n"

if new != old:
    backup = Path(f"CLAUDE.md.bak.{ts}")
    backup.write_text(old, encoding="utf-8")
    path.write_text(new, encoding="utf-8")
    print(str(backup))
PY
}

create_hooks() {
  install_file ".claude/hooks/block-dangerous-bash.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"

INPUT_JSON="$INPUT" python3 - <<'PY'
import json
import os
import re
import sys

try:
    payload = json.loads(os.environ.get("INPUT_JSON", "") or "{}")
except Exception:
    sys.exit(0)

cmd = payload.get("tool_input", {}).get("command", "")
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

normalized = " ".join(cmd.split())

patterns = [
    r"(^|[;&|]\s*)rm\s+-(?=[A-Za-z-]*r)(?=[A-Za-z-]*f)[A-Za-z-]*\b",
    r"(^|[;&|]\s*)kubectl\s+delete\b",
    r"(^|[;&|]\s*)terraform\s+apply\b",
    r"(^|[;&|]\s*)pulumi\s+up\b",
    r"(^|[;&|]\s*)aws\b.*\bdelete\b",
    r"(^|[;&|]\s*)gcloud\b.*\bdelete\b",
    r"(^|[;&|]\s*)az\b.*\bdelete\b",
    r"\b(drop|truncate)\s+(database|table)\b",
    r"(^|[;&|]\s*)git\s+push\b",
    r"(^|[;&|]\s*)git\s+reset\s+--hard\b",
    r"(^|[;&|]\s*)git\s+clean\s+-fd\b",
]

for pattern in patterns:
    if re.search(pattern, normalized, flags=re.IGNORECASE):
        print(f"Blocked dangerous command: {normalized}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
PY
SH

  install_file ".claude/hooks/protect-files.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"

INPUT_JSON="$INPUT" python3 - <<'PY'
import json
import os
import re
import sys

try:
    payload = json.loads(os.environ.get("INPUT_JSON", "") or "{}")
except Exception:
    sys.exit(0)

tool_input = payload.get("tool_input", {})
paths = []

for key in ("file_path", "path"):
    value = tool_input.get(key)
    if isinstance(value, str):
        paths.append(value)

# MultiEdit usually still uses file_path, but keep this defensive for future payload shapes.
for key in ("file_paths", "paths"):
    value = tool_input.get(key)
    if isinstance(value, list):
        paths.extend(x for x in value if isinstance(x, str))

protected = re.compile(
    r"(^|/)(\.env|\.env\..*|secrets|secret|credentials|id_rsa|id_ed25519|.*\.pem|.*\.key|.*\.p12|.*\.pfx)$"
    r"|(^|/)\.git(/|$)",
    flags=re.IGNORECASE,
)

for p in paths:
    normalized = p.replace("\\", "/")
    if protected.search(normalized):
        print(f"Blocked protected file operation: {p}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
PY
SH

  chmod +x .claude/hooks/block-dangerous-bash.sh .claude/hooks/protect-files.sh
}

create_agents() {
  install_file ".claude/agents/product-agent.md" <<'MD'
---
name: product-agent
description: Reads PRD and active governance docs to extract scope, user stories, acceptance criteria, non-goals, and open questions.
tools:
  - Read
  - Grep
  - Glob
model: inherit
---

You are the Product Agent for AiForInterviewer.

Repository governance rules:
- `AGENTS.md` and `docs/00-governance/DOCS_INDEX.md` are the governing sources.
- Do not create parallel roadmap, plan, task, or phase systems.
- Do not treat `archive/` as current execution source.
- Use Chinese for project documentation unless identifiers, commands, paths, APIs, or library names require original text.

Responsibilities:
- Read the active PRD: prefer `docs/01-product/PRD.md`; fallback to `PRD.md` only if that is the active source in this repo.
- Extract product goals, personas, user stories, core flows, non-goals, constraints, and acceptance criteria.
- Identify ambiguity and missing requirements.
- Propose updates for:
  - `docs/01-product/REQUIREMENT_TRACEABILITY.md`
  - `docs/03-delivery/BACKLOG.md`
  - `docs/03-delivery/DELIVERY_PLAN.md`

Rules:
- Do not edit business code.
- Do not create `docs/plans/roadmap.md`, `docs/plans/task-graph.md`, or any new parallel planning entry.
- Mark assumptions explicitly.
MD

  install_file ".claude/agents/api-contract-agent.md" <<'MD'
---
name: api-contract-agent
description: Designs API contracts, DTOs, error models, auth requirements, and state machines under existing governance constraints.
tools:
  - Read
  - Grep
  - Glob
model: inherit
---

You are the API Contract Agent for AiForInterviewer.

Responsibilities:
- Read `AGENTS.md`, `docs/00-governance/DOCS_INDEX.md`, and active product/delivery docs.
- Identify frontend/backend integration points.
- Define API endpoints, request/response DTOs, error codes, auth requirements, pagination, idempotency, and state transitions.
- Keep API contract as the coordination center for frontend and backend.

Governance constraints:
- Do not create a new parallel contract entry if an active contract location already exists.
- If a long-lived architectural decision is needed, propose an ADR under `docs/04-decisions/ADR-*.md`.
- If tasks are needed, propose entries for `docs/03-delivery/BACKLOG.md`.

Rules:
- Do not edit business code during design tasks.
- Do not invent backend capabilities without marking assumptions.
MD

  install_file ".claude/agents/backend-architect.md" <<'MD'
---
name: backend-architect
description: Designs backend modules, service boundaries, data model, transactions, idempotency, observability, and rollout strategy.
tools:
  - Read
  - Grep
  - Glob
  - Bash
model: inherit
---

You are the Backend Architect for AiForInterviewer.

Responsibilities:
- Analyze existing backend structure.
- Design domain model, service boundaries, data model, transaction boundaries, idempotency, authorization, observability, and rollout strategy.
- Identify migration, rollout, and rollback risks.
- Propose backlog items only through `docs/03-delivery/BACKLOG.md`.

Rules:
- Prefer the simplest architecture that satisfies the active PRD.
- Do not edit business code during design tasks.
- Do not apply database migrations.
- Do not modify deployment configuration.
- Always list tradeoffs and operational risks.
MD

  install_file ".claude/agents/frontend-architect.md" <<'MD'
---
name: frontend-architect
description: Designs frontend routes, page flows, component hierarchy, state management, accessibility, and design-system alignment.
tools:
  - Read
  - Grep
  - Glob
model: inherit
---

You are the Frontend Architect for AiForInterviewer.

Responsibilities:
- Analyze existing frontend structure and design system.
- Design routes, page flows, component hierarchy, state management, cache strategy, loading/empty/error/retry states, responsive behavior, and accessibility.
- Coordinate with `api-contract-agent` rather than assuming API fields.

Governance constraints:
- Do not create new parallel planning docs.
- If implementation tasks are needed, propose entries for `docs/03-delivery/BACKLOG.md`.
- If a long-lived frontend architecture decision is needed, propose an ADR under `docs/04-decisions/ADR-*.md`.

Rules:
- Do not edit business code during design tasks.
- Explicitly list design-system gaps and high-fidelity design requirements.
MD

  install_file ".claude/agents/qa-agent.md" <<'MD'
---
name: qa-agent
description: Designs test strategy, acceptance mapping, contract tests, integration tests, E2E tests, and regression gates.
tools:
  - Read
  - Grep
  - Glob
  - Bash
model: inherit
---

You are the QA Agent for AiForInterviewer.

Responsibilities:
- Map active PRD acceptance criteria to tests.
- Design unit, integration, contract, E2E, negative, and regression tests.
- Identify missing test infrastructure and CI gates.
- Propose test tasks through `docs/03-delivery/BACKLOG.md`.

Rules:
- Do not create a parallel test plan entry if the repository already has an active test governance location.
- Validation must be explicit and executable.
- Do not mark a workstream complete without test evidence or a documented reason.
MD

  install_file ".claude/agents/security-reviewer.md" <<'MD'
---
name: security-reviewer
description: Reviews auth, authorization, data exposure, secrets handling, input validation, abuse cases, and deployment risks.
tools:
  - Read
  - Grep
  - Glob
model: inherit
---

You are the Security Reviewer for AiForInterviewer.

Responsibilities:
- Review authentication, authorization, data boundaries, secrets, input validation, injection risk, audit logging, abuse cases, and sensitive operations.
- Identify blocking and non-blocking risks.
- Recommend no-go when risks are unresolved.

Rules:
- Never approve production deployment automatically.
- Never read or edit `.env`, secrets, credentials, or private keys.
- Treat auth, billing, migration, infra, and production data as high risk.
- Put proposed tasks into `docs/03-delivery/BACKLOG.md`; do not create parallel risk/task systems.
MD

  install_file ".claude/agents/devops-agent.md" <<'MD'
---
name: devops-agent
description: Designs CI, preview environments, release gates, deployment sequence, rollback, and observability.
tools:
  - Read
  - Grep
  - Glob
  - Bash
model: inherit
---

You are the DevOps Agent for AiForInterviewer.

Responsibilities:
- Analyze current CI/build/test/deploy setup.
- Design lint, typecheck, unit, integration, E2E, preview environment, release, rollback, and observability gates.
- Propose delivery tasks through `docs/03-delivery/BACKLOG.md`.

Rules:
- Do not modify deployment configuration unless explicitly approved.
- Do not run production operations.
- Do not run destructive commands.
- Prefer reversible rollout and explicit rollback.
MD

  install_file ".claude/agents/integration-reviewer.md" <<'MD'
---
name: integration-reviewer
description: Reviews consistency across PRD, delivery plan, backlog, API contract, backend, frontend, QA, security, and devops.
tools:
  - Read
  - Grep
  - Glob
  - Bash
model: inherit
---

You are the Integration Reviewer for AiForInterviewer.

Responsibilities:
- Compare active PRD, delivery plan, backlog, API contract, frontend flow, backend architecture, test strategy, and risk notes.
- Identify contradictions, missing dependencies, overengineering, and untestable assumptions.
- Produce a go/no-go recommendation.

Rules:
- Do not edit business code.
- Do not create new roadmap, task graph, or parallel phase system.
- Every blocking issue must identify the affected active document or workstream.
MD

  install_file ".claude/agents/implementation-slice-agent.md" <<'MD'
---
name: implementation-slice-agent
description: Implements one bounded workstream slice after explicit approval, with small diffs, tests, and risk summary.
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Edit
  - Write
  - MultiEdit
model: inherit
---

You are the Implementation Slice Agent for AiForInterviewer.

Use only after:
- The active PRD and delivery/backlog entries are clear.
- The slice has explicit acceptance criteria.
- The user or lead has approved implementation.

Responsibilities:
- Implement exactly one bounded slice.
- Keep diffs small and reviewable.
- Add or update tests.
- Run relevant validation commands.
- Report files changed, tests run, risks, and next steps.

Rules:
- Before editing, state the plan, affected files, validation commands, and risk level.
- Do not modify unrelated files.
- Do not create parallel planning or task documents.
- Do not modify database migrations, auth-critical code, billing, deployment config, secrets, or infra without explicit approval.
- Do not mark complete if tests fail.
MD
}

create_skills() {
  install_file ".claude/skills/prd-to-roadmap/SKILL.md" <<'MD'
---
description: Governance-safe PRD decomposition for AiForInterviewer; uses existing delivery/backlog/traceability entries instead of creating parallel roadmap or task graph docs.
allowed-tools: Read Grep Glob Bash
---

# Governance-safe PRD Decomposition

Use this skill when starting from the active PRD.

## Governing rules

Before doing anything, read:

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD, usually `docs/01-product/PRD.md`

Do not create:

- `docs/plans/roadmap.md`
- `docs/plans/task-graph.md`
- `roadmap-v2.md`
- `latest-plan.md`
- any new parallel roadmap, task, phase, or plan entry

## Allowed target entries

Use existing governance locations:

- Stage/milestone proposals: `docs/03-delivery/DELIVERY_PLAN.md`
- Task proposals: `docs/03-delivery/BACKLOG.md`
- Requirement mapping: `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- Long-lived decisions only when needed: `docs/04-decisions/ADR-*.md`

## Output

Produce a governance-safe proposal in the conversation first:

1. PRD summary
2. open questions
3. proposed DELIVERY_PLAN changes
4. proposed BACKLOG changes
5. proposed REQUIREMENT_TRACEABILITY changes
6. risks
7. validation method
8. files that would be touched if user approves

Do not edit active delivery/backlog/traceability files unless the user explicitly approves.
MD

  install_file ".claude/skills/design-review/SKILL.md" <<'MD'
---
description: Review architecture, API contract, frontend flow, backend plan, QA strategy, and risks under AiForInterviewer governance rules.
allowed-tools: Read Grep Glob Bash
---

# Governance-safe Design Review

Use this skill after PRD decomposition and before implementation.

## Read first

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- relevant ADRs under `docs/04-decisions/`, if present

## Checks

1. PRD coverage
2. missing requirements
3. API/frontend mismatch
4. backend feasibility
5. data and migration risk
6. security risk
7. test coverage
8. overengineering
9. implementation sequencing
10. go / no-go recommendation

## Governance-safe output

Return a proposed review report in the conversation. If persistent documentation is needed:

- decision: propose an ADR under `docs/04-decisions/ADR-*.md`
- stage changes: propose edits to `docs/03-delivery/DELIVERY_PLAN.md`
- task changes: propose edits to `docs/03-delivery/BACKLOG.md`
- requirement mapping: propose edits to `docs/01-product/REQUIREMENT_TRACEABILITY.md`

Do not create `docs/plans/*` or any parallel plan/task entry.
Do not edit files without explicit user approval.
MD

  install_file ".claude/skills/implementation-slice/SKILL.md" <<'MD'
---
description: Implement one bounded AiForInterviewer slice from active backlog/delivery entries with small diff, tests, and risk summary.
allowed-tools: Read Grep Glob Bash Edit Write MultiEdit
---

# Governance-safe Implementation Slice

Use this skill only after the relevant active backlog/delivery entries are approved.

## Read first

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- relevant ADRs

## Rules

1. Implement only one bounded slice.
2. Before editing, produce:
   - backlog item or delivery phase reference
   - scope
   - files likely affected
   - tests to run
   - risk level
3. Keep diff small.
4. Do not modify protected areas without explicit approval:
   - database migrations
   - auth-critical code
   - billing
   - deployment config
   - secrets
   - infra
5. Do not create parallel planning docs.
6. After editing, run relevant tests.
7. Final response must include:
   - files changed
   - tests run
   - failing tests, if any
   - risks
   - next step
   - governance residue check
MD

  install_file ".claude/skills/agent-team-kickoff/SKILL.md" <<'MD'
---
description: Kick off an Agent Team from the active PRD while respecting AiForInterviewer governance and avoiding parallel planning systems.
allowed-tools: Read Grep Glob Bash
---

# Governance-safe Agent Team Kickoff

Use this skill to start project-level Agent Teams from the active PRD.

## Required pre-read

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD, usually `docs/01-product/PRD.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`, if present

## Recommended team

Ask Claude Code to create a team with:

1. `product-agent`
2. `api-contract-agent`
3. `backend-architect`
4. `frontend-architect`
5. `qa-agent`
6. `security-reviewer`
7. `devops-agent`
8. `integration-reviewer`

## Global constraints

- Current phase is design and decomposition unless the user explicitly approves implementation.
- Do not implement business code.
- Do not modify migration, deployment config, secrets, credentials, private keys, or production data.
- Do not create new parallel roadmap, plan, task, or phase systems.
- API contract is the center of backend/frontend coordination.
- Every proposed task must map to active PRD acceptance criteria or an explicit engineering prerequisite.
- Security reviewer can issue no-go.
- Integration reviewer must resolve contradictions.

## Required output

Return a consolidated proposal in conversation:

- PRD interpretation
- open questions
- proposed API contract direction
- backend architecture direction
- frontend flow direction
- QA/test strategy direction
- security risks
- devops/release gate direction
- proposed updates to existing governance docs:
  - `docs/03-delivery/DELIVERY_PLAN.md`
  - `docs/03-delivery/BACKLOG.md`
  - `docs/01-product/REQUIREMENT_TRACEABILITY.md`
  - `docs/04-decisions/ADR-*.md` only if needed

Do not write these docs unless the user explicitly approves.
MD
}

validate_scope() {
  python3 -m json.tool .claude/settings.json >/dev/null
  bash -n .claude/hooks/block-dangerous-bash.sh
  bash -n .claude/hooks/protect-files.sh

  local bad=0

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    # git status --short format:
    # XY path
    # XY old -> new
    local path="${line:3}"
    path="${path#\"}"
    path="${path%\"}"

    if [[ "$path" == *" -> "* ]]; then
      path="${path##* -> }"
    fi

    case "$path" in
      .claude/settings.json|\
      .claude/agents/*.md|\
      .claude/skills/*/SKILL.md|\
      .claude/hooks/*.sh|\
      CLAUDE.md|\
      .gitignore|\
      .claude/settings.json.bak.*|\
      .claude/agents/*.md.bak.*|\
      .claude/skills/*/SKILL.md.bak.*|\
      .claude/hooks/*.sh.bak.*|\
      CLAUDE.md.bak.*|\
      .gitignore.bak.*|\
      bootstrap-claude-agent-teams-governance-safe.sh)
        ;;
      *)
        echo "WARNING: git status contains path outside expected install scope: $path" >&2
        bad=1
        ;;
    esac
  done < <(git status --short -uall)

  if [[ "$bad" -eq 1 ]]; then
    die "检测到安装范围外的文件变更。请检查 git status。"
  fi
}

print_report() {
  echo
  echo "Installation completed."
  echo
  echo "Created/modified files:"
  if [[ "${#WRITTEN[@]}" -eq 0 ]]; then
    echo "  - None"
  else
    printf "  - %s\n" "${WRITTEN[@]}"
  fi

  echo
  echo "Backups:"
  if [[ "${#BACKUPS[@]}" -eq 0 ]]; then
    echo "  - None"
  else
    printf "  - %s\n" "${BACKUPS[@]}"
  fi

  echo
  echo "Validation:"
  echo "  - python3 -m json.tool .claude/settings.json"
  echo "  - bash -n .claude/hooks/block-dangerous-bash.sh"
  echo "  - bash -n .claude/hooks/protect-files.sh"
  echo "  - git status --short scope check"
  echo

  if [[ "${#WARNINGS[@]}" -gt 0 ]]; then
    echo "Warnings:"
    printf "  - %s\n" "${WARNINGS[@]}"
    echo
  fi

  echo "git status --short:"
  git status --short

  echo
  echo "git diff --stat:"
  git diff --stat || true

  echo
  echo "Next recommended command:"
  echo "  CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude --permission-mode plan --teammate-mode in-process"
  echo
  echo "Then inside Claude Code:"
  echo "  /agent-team-kickoff"
}

main() {
  ensure_repo_root

  local prd_path
  prd_path="$(detect_prd)"

  mkdir -p \
    .claude/agents \
    .claude/skills/prd-to-roadmap \
    .claude/skills/design-review \
    .claude/skills/implementation-slice \
    .claude/skills/agent-team-kickoff \
    .claude/hooks

  merge_settings_json
  ensure_gitignore_lines
  create_hooks
  create_agents
  create_skills

  local claude_backup
  claude_backup="$(update_claude_md "$prd_path" || true)"
  if [[ -n "${claude_backup:-}" ]]; then
    BACKUPS+=("$claude_backup")
    WRITTEN+=("CLAUDE.md")
  fi

  validate_scope
  print_report
}

main "$@"
