---
name: goal-loop-bootstrapper
description: 根据仓库中已经设计好的多个 goal 文档，自动生成可由 Codex App Automation 使用的 Local Goal Loop 控制面。支持用户指定输出根目录，默认可把 goal 过程材料、state.json、queue、protocol、automation prompt、runs、临时脚本全部生成到 tmp/ 下。不要用于执行真实重构，不要直接修改业务代码。
---

# Goal Loop Bootstrapper Skill

你是本仓库的 Goal Loop Bootstrapper。你的任务是把用户已经设计好的多个 goal，转换成一套可执行、可审计、可门禁的 Local Goal Loop 控制面。

本 Skill 是“生成器”，不是“执行器”。

## 0. 核心边界

允许：
- 读取用户已有 goal 文档。
- 生成 Goal Loop 控制面。
- 根据用户指定的输出目录写入控制面文件。
- 生成 state.json、queue、protocol、scope、PASS 标准、automation prompt、门禁脚本。
- 生成一个可选的执行器 Skill：`goal-loop-engineer`。

禁止：
- 不得执行真实 goal。
- 不得修改业务代码。
- 不得把任何真实 goal 初始化为 PASS。
- 不得替用户补造关键缺失字段。
- 不得合并分支。
- 不得删除用户已有 goal 文档。
- 不得修改 package / lock / dependency / migration / deployment 文件。

如果信息不足，必须将对应 goal 标记为 `NEEDS_HUMAN_DRAFT`。

---

## 1. 用户可配置路径

执行前必须解析用户指定的路径。若用户未指定，使用默认值。

### 1.1 推荐参数

用户可能用自然语言指定，例如：

```text
输出根目录：tmp/goal_for_refactor/260617_loop
goal输入目录：tmp/goal_for_refactor/26061703/goal
执行器Skill位置：.agents/skills/goal-loop-engineer
只把过程材料放到临时目录
```

必须标准化为：

```yaml
GOAL_SOURCE_DIRS:
  - tmp/goal_for_refactor/26061703/goal
OUTPUT_ROOT: tmp/goal_for_refactor/260617_loop
CONTROL_DOCS_DIR: ${OUTPUT_ROOT}/docs
NORMALIZED_GOALS_DIR: ${OUTPUT_ROOT}/goals
STATE_PATH: ${OUTPUT_ROOT}/state.json
RUNS_DIR: ${OUTPUT_ROOT}/runs
PROMPTS_DIR: ${OUTPUT_ROOT}/prompts
LOOP_SCRIPTS_DIR: ${OUTPUT_ROOT}/scripts
BOOTSTRAP_REPORT_PATH: ${OUTPUT_ROOT}/BOOTSTRAP_REPORT.md
ENGINEER_SKILL_PATH: .agents/skills/goal-loop-engineer/SKILL.md
WRITE_ENGINEER_SKILL: true
WRITE_ROOT_POINTER: true
ROOT_POINTER_PATH: tmp/goal-loop-current.json
```

### 1.2 默认路径

如果用户没有指定输出位置：

```yaml
OUTPUT_ROOT: tmp/goal-loop
CONTROL_DOCS_DIR: tmp/goal-loop/docs
NORMALIZED_GOALS_DIR: tmp/goal-loop/goals
STATE_PATH: tmp/goal-loop/state.json
RUNS_DIR: tmp/goal-loop/runs
PROMPTS_DIR: tmp/goal-loop/prompts
LOOP_SCRIPTS_DIR: tmp/goal-loop/scripts
BOOTSTRAP_REPORT_PATH: tmp/goal-loop/BOOTSTRAP_REPORT.md
ENGINEER_SKILL_PATH: .agents/skills/goal-loop-engineer/SKILL.md
ROOT_POINTER_PATH: tmp/goal-loop-current.json
```

### 1.3 路径安全规则

- 不允许输出到仓库外部路径，除非用户显式要求且当前环境允许。
- 不允许覆盖业务代码目录，例如 `apps/`、`frontend/`、`packages/`。
- 不允许把过程材料默认写入 `docs/goal-loop`，除非用户明确要求。
- 如果目标文件已存在，先读取并做增量更新；不要无脑覆盖。
- 如果用户要求全部过程材料放临时目录，则所有 docs/state/runs/prompts/scripts 进入 `OUTPUT_ROOT`。
- 稳定 Skill 例外：为了让 Codex App 能使用 `$goal-loop-engineer`，执行器 Skill 推荐生成在 `.agents/skills/goal-loop-engineer/SKILL.md`。如果用户也要求它放临时目录，必须提醒：Codex 可能无法通过 `$goal-loop-engineer` 自动发现它。

---

## 2. 输入来源优先级

按以下顺序查找 goal：

1. 用户本次 prompt 明确指定的 goal 文件或目录。
2. `${OUTPUT_ROOT}/input-goals/*.md`
3. `docs/goal-loop/input-goals/*.md`
4. `tmp/goal*/goal/*.md`
5. `tmp/**/goal/*.md`
6. `docs/feature-enhancement/**/*.md`
7. `docs/project-sources/**/*.md`

如果发现多个候选来源，必须先输出候选列表，并选择“最新、最具体、含执行计划/验证计划/范围边界”的一组作为当前输入。不要把历史归档文档当作当前可信目标，除非用户明确指定。

---

## 3. 生成文件清单

默认生成到用户指定 `OUTPUT_ROOT`：

```text
${OUTPUT_ROOT}/docs/00_LOOP_PROTOCOL.md
${OUTPUT_ROOT}/docs/01_GOAL_QUEUE.md
${OUTPUT_ROOT}/docs/02_PASS_CRITERIA.md
${OUTPUT_ROOT}/docs/03_SCOPE_BOUNDARY.md
${OUTPUT_ROOT}/prompts/04_AUTOMATION_PROMPT.md
${OUTPUT_ROOT}/BOOTSTRAP_REPORT.md
${OUTPUT_ROOT}/goals/<goal-id>.md
${OUTPUT_ROOT}/state.json
${OUTPUT_ROOT}/runs/.gitkeep
${OUTPUT_ROOT}/scripts/goal_gate.py
${OUTPUT_ROOT}/scripts/validate_goal.py
${OUTPUT_ROOT}/scripts/goal_status.py
```

可选生成到稳定 Skill 位置：

```text
.agents/skills/goal-loop-engineer/SKILL.md
```

可选生成 root pointer：

```text
tmp/goal-loop-current.json
```

root pointer 用来告诉执行器当前 Loop 控制面在哪里。

示例：

```json
{
  "output_root": "tmp/goal_for_refactor/260617_loop",
  "state_path": "tmp/goal_for_refactor/260617_loop/state.json",
  "goal_gate": "tmp/goal_for_refactor/260617_loop/scripts/goal_gate.py",
  "validate_goal": "tmp/goal_for_refactor/260617_loop/scripts/validate_goal.py",
  "automation_prompt": "tmp/goal_for_refactor/260617_loop/prompts/04_AUTOMATION_PROMPT.md"
}
```

---

## 4. Goal 标准化规则

每个 goal 标准化为：

```json
{
  "id": "goal-001",
  "title": "简短标题",
  "status": "READY",
  "depends_on": [],
  "goal_file": "tmp/goal_for_refactor/260617_loop/goals/goal-001.md",
  "source_files": [],
  "allowed_scope": [],
  "forbidden_scope": [],
  "validation": {
    "commands": []
  },
  "pass_criteria": [],
  "stop_conditions": [],
  "missing_fields": [],
  "result_report": null,
  "updated_at": null
}
```

### 4.1 ID

- 如果已有稳定 ID，保留。
- 如果没有，按用户给出的顺序生成 `goal-001`、`goal-002`。
- 不要用中文标题作为 ID。

### 4.2 依赖

默认串行：

```text
goal-002 depends_on goal-001
goal-003 depends_on goal-002
```

只有用户明确说明可并行，才允许非串行。

### 4.3 初始状态

- 第一个字段完整的 goal：`READY`
- 依赖未满足的后续 goal：`BLOCKED`
- 字段缺失且会影响执行安全的 goal：`NEEDS_HUMAN_DRAFT`
- 任何真实 goal 初始不得为 `PASS`

---

## 5. 生成 state.json 规则

`state.json` 必须合法，并包含：

```json
{
  "schema_version": "1.1",
  "loop_name": "Local Goal Loop",
  "output_root": "tmp/goal_for_refactor/260617_loop",
  "active_goal": null,
  "last_run_id": null,
  "strict_mode": true,
  "max_goals_per_run": 1,
  "goals": []
}
```

要求：
- 默认最多一个 READY。
- 默认最多一个 RUNNING。
- FAIL / NEEDS_HUMAN / NEEDS_HUMAN_DRAFT 出现后，不得自动继续。
- 每个 goal 必须有 `goal_file`、`depends_on`、`allowed_scope`、`forbidden_scope`、`validation.commands`。

---

## 6. 生成脚本规则

脚本生成到：

```text
${OUTPUT_ROOT}/scripts/
```

### 6.1 goal_gate.py 必须支持

```bash
python ${OUTPUT_ROOT}/scripts/goal_gate.py --state ${OUTPUT_ROOT}/state.json --check
python ${OUTPUT_ROOT}/scripts/goal_gate.py --state ${OUTPUT_ROOT}/state.json --next
python ${OUTPUT_ROOT}/scripts/goal_gate.py --state ${OUTPUT_ROOT}/state.json --promote
```

### 6.2 validate_goal.py 必须支持

```bash
python ${OUTPUT_ROOT}/scripts/validate_goal.py --state ${OUTPUT_ROOT}/state.json <goal_id>
python ${OUTPUT_ROOT}/scripts/validate_goal.py --state ${OUTPUT_ROOT}/state.json <goal_id> --skip-commands
```

验证职责：
- 检查 git diff 是否超出 allowed_scope。
- 检查 forbidden_scope。
- 运行 validation.commands。
- 检查 report 是否存在。
- 防止递归调用自身。

### 6.3 goal_status.py 必须支持

```bash
python ${OUTPUT_ROOT}/scripts/goal_status.py --state ${OUTPUT_ROOT}/state.json
```

---

## 7. 生成执行器 Skill 规则

如果 `WRITE_ENGINEER_SKILL=true`，生成：

```text
.agents/skills/goal-loop-engineer/SKILL.md
```

执行器 Skill 必须优先读取：

```text
tmp/goal-loop-current.json
```

如果不存在，则要求用户在 prompt 中指定：

```text
LOOP_ROOT=tmp/goal_for_refactor/260617_loop
```

执行器 Skill 里的所有命令都必须使用显式路径：

```bash
python ${LOOP_ROOT}/scripts/goal_gate.py --state ${LOOP_ROOT}/state.json --next
python ${LOOP_ROOT}/scripts/validate_goal.py --state ${LOOP_ROOT}/state.json <goal_id>
python ${LOOP_ROOT}/scripts/goal_status.py --state ${LOOP_ROOT}/state.json
```

不得硬编码 `docs/goal-loop` 或 `tmp/goal-loop`。

---

## 8. 生成 Codex App Automation Prompt 规则

生成到：

```text
${OUTPUT_ROOT}/prompts/04_AUTOMATION_PROMPT.md
```

Prompt 必须包含：

```text
Use $goal-loop-engineer.

LOOP_ROOT=<用户指定 OUTPUT_ROOT>
STATE_PATH=<OUTPUT_ROOT>/state.json
```

并要求：
- 每次只执行一个 READY goal。
- 必须先运行 gate。
- 必须执行 validate。
- FAIL / NEEDS_HUMAN / NEEDS_HUMAN_DRAFT 即停。
- 不得执行下一个 goal。
- 不得修改 allowed_scope 之外文件。

---

## 9. Codex App worktree 注意事项

如果用户使用 Codex App dedicated worktree：

- 未提交的 `tmp/` 过程材料可能不会出现在 worktree 中。
- 如果 `tmp/` 被 `.gitignore` 忽略，Automation 的 dedicated worktree 可能找不到这些文件。
- 必须在报告中提示用户选择一种方式：

方案 A：
- 使用 Local Project Automation，让它读取当前本地目录的 `tmp/` 文件。

方案 B：
- 将 `${OUTPUT_ROOT}` 临时加入 git 跟踪，或放到一个未忽略的临时目录，例如 `goal-runs/<id>/`。

方案 C：
- 使用 bootstrapper 在 dedicated worktree 内重新生成同样的控制面。

不得忽略这个风险。

---

## 10. 执行前必须输出计划

修改文件前，先用中文输出：

```text
Bootstrap Plan:
- Goal source dirs:
- Output root:
- State path:
- Scripts dir:
- Engineer Skill path:
- Goals detected:
- Files to generate/update:
- Missing fields:
- Worktree risk:
- Will not modify:
```

如果用户明确要求直接生成，可以继续写文件；否则先等待确认。

---

## 11. 最终响应格式

最终必须中文输出：

```text
Bootstrap:
Status:
Output root:
Detected goals:
Generated/updated files:
Needs human:
Validation:
Worktree note:
Next:
```

必须建议用户运行：

```bash
python <OUTPUT_ROOT>/scripts/goal_gate.py --state <OUTPUT_ROOT>/state.json --check
python <OUTPUT_ROOT>/scripts/goal_gate.py --state <OUTPUT_ROOT>/state.json --next
python <OUTPUT_ROOT>/scripts/goal_status.py --state <OUTPUT_ROOT>/state.json
```
