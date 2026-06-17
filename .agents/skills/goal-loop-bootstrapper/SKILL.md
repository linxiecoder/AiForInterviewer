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
GOAL_RESULT_ROOT: tmp/goal_for_refactor/260617_loop/goal_result
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
GOAL_RESULT_ROOT: tmp/goal-loop/goal_result
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
- 如果用户指定了独立的 `GOAL_RESULT_ROOT`，按用户路径生成 result metadata；不得把结果目录隐式压回 `OUTPUT_ROOT`。
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
${OUTPUT_ROOT}/scripts/update_goal_state.py
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
  "phase": "phase-01",
  "status": "READY",
  "depends_on": [],
  "goal_file": "tmp/goal_for_refactor/260617_loop/goals/goal-001.md",
  "prompt_path": "tmp/goal_for_refactor/26061703/goal/phase-01/goal-001/PROMPT.md",
  "spec_path": "tmp/goal_for_refactor/26061703/goal/phase-01/goal-001/GOAL.md",
  "goal_dir": "tmp/goal_for_refactor/26061703/goal/phase-01/goal-001",
  "result_dir": "tmp/goal_for_refactor/260617_loop/goal_result/phase-01/goal-001",
  "review_path": "tmp/goal_for_refactor/260617_loop/goal_result/phase-01/goal-001/REVIEW.md",
  "commit_info_path": "tmp/goal_for_refactor/260617_loop/goal_result/phase-01/goal-001/COMMIT_INFO.md",
  "source_files": [],
  "allowed_scope": [],
  "forbidden_scope": [],
  "validation": {
    "commands": []
  },
  "pass_criteria": [],
  "stop_conditions": [],
  "missing_fields": [],
  "result_report": "tmp/goal_for_refactor/260617_loop/goal_result/phase-01/goal-001/SUMMARY.md",
  "updated_at": null,
  "expected_result_files": [
    "SUMMARY.md",
    "EVIDENCE.md",
    "COMMANDS.md",
    "CHANGED_FILES.md",
    "REVIEW.md",
    "COMMIT_INFO.md"
  ]
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
  "goal_result_root": "tmp/goal_for_refactor/260617_loop/goal_result",
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
- 每个 goal 必须有 `phase`、`prompt_path`、`spec_path`、`goal_dir`、`result_dir`、`review_path`、`commit_info_path`、`expected_result_files`。
- `result_dir` 必须是每个 goal 独立目录：`${GOAL_RESULT_ROOT}/<phase>/<goal-id>/`。禁止使用 `${GOAL_RESULT_ROOT}/<phase>/` 作为 goal 的 `result_dir`。
- `review_path` 必须等于 `${result_dir}/REVIEW.md`。
- `commit_info_path` 必须等于 `${result_dir}/COMMIT_INFO.md`。
- `expected_result_files` 必须固定为：

```json
[
  "SUMMARY.md",
  "EVIDENCE.md",
  "COMMANDS.md",
  "CHANGED_FILES.md",
  "REVIEW.md",
  "COMMIT_INFO.md"
]
```

示例：

```text
tmp/aifi-runtime-state-contract-refactor/goal_result/phase-00/goal-00-fact-readback/
tmp/aifi-runtime-state-contract-refactor/goal_result/phase-06/goal-06a-question-final-write/
tmp/aifi-runtime-state-contract-refactor/goal_result/phase-06/goal-06b-progress-stale-guard/
tmp/aifi-runtime-state-contract-refactor/goal_result/phase-08/goal-08a-token-budget-unification/
tmp/aifi-runtime-state-contract-refactor/goal_result/phase-08/goal-08b-raw-dump-provider-eval-gate/
tmp/aifi-runtime-state-contract-refactor/goal_result/phase-08/goal-08c-sensitive-marker-regression/
```

### 5.1 PROMPT.md 扫描规则

扫描 goal prompt 时必须兼容两种布局：

优先布局：

```text
${GOAL_SOURCE_ROOT}/phase-*/goal-*/PROMPT.md
```

兼容布局：

```text
${GOAL_SOURCE_ROOT}/phase-*/*.PROMPT.md
```

匹配规则：
- 如果两种布局都存在，以实际存在且能唯一匹配 goal id 的 `PROMPT.md` 为准。
- 如果一个 goal 找到多个 `PROMPT.md`，不得猜测；该 goal 必须标记为 `NEEDS_HUMAN_DRAFT`，并在 `missing_fields` 中记录 `ambiguous_prompt_path`。
- 如果一个 goal 找不到 `PROMPT.md`，该 goal 必须标记为 `NEEDS_HUMAN_DRAFT`，并在 `missing_fields` 中记录 `prompt_path`。
- 不得为了消除歧义重命名、移动或重新生成用户已有 goal prompt。

---

## 6. 生成脚本规则

脚本生成到：

```text
${OUTPUT_ROOT}/scripts/
```

### 6.1 goal_gate.py 必须支持

```bash
python3 ${OUTPUT_ROOT}/scripts/goal_gate.py --state ${OUTPUT_ROOT}/state.json --check
python3 ${OUTPUT_ROOT}/scripts/goal_gate.py --state ${OUTPUT_ROOT}/state.json --promote
python3 ${OUTPUT_ROOT}/scripts/goal_gate.py --state ${OUTPUT_ROOT}/state.json --next
```

所有生成文档和脚本示例命令必须优先使用 `python3`。如果当前环境没有 `python3`，再尝试 `python`；如果两者都不存在，停止并输出原因。不得因为裸 `python` 不存在就判断 goal 失败。

### 6.2 validate_goal.py 必须支持

```bash
python3 ${OUTPUT_ROOT}/scripts/validate_goal.py --state ${OUTPUT_ROOT}/state.json <goal_id>
python3 ${OUTPUT_ROOT}/scripts/validate_goal.py --state ${OUTPUT_ROOT}/state.json <goal_id> --skip-commands
```

验证职责：
- 检查 git diff 是否超出 allowed_scope。
- 检查 forbidden_scope。
- 运行 validation.commands。
- 检查 report 是否存在。
- 防止递归调用自身。
- 按当前 goal 的独立 `result_dir` 验证 `expected_result_files` 全部存在。
- 检查 `result_dir` 必须等于 `${GOAL_RESULT_ROOT}/<phase>/<goal-id>/`，不得把 phase 目录当作 `result_dir`。
- 检查 `review_path` 和 `commit_info_path` 必须落在当前 goal 的独立 `result_dir` 下，避免同一 phase 多个 goal 的 `REVIEW.md` / `COMMIT_INFO.md` 互相覆盖或误判。
- 检查 `REVIEW.md` 中 `verdict = PASS`。
- 检查 `COMMIT_INFO.md` 记录 commit sha，或记录 no commit needed reason。
- 阻止 `git push` 作为 validation command。

### 6.3 goal_status.py 必须支持

```bash
python3 ${OUTPUT_ROOT}/scripts/goal_status.py --state ${OUTPUT_ROOT}/state.json
```

### 6.4 update_goal_state.py 必须支持

以后生成的 Loop 控制面必须生成：

```text
${OUTPUT_ROOT}/scripts/update_goal_state.py
```

脚本必须只更新同一控制面的 `${OUTPUT_ROOT}/state.json`，不得修改业务文件、测试文件、active docs、goal 输入包或 goal result 文件。支持命令：

```bash
python3 ${OUTPUT_ROOT}/scripts/update_goal_state.py --state ${OUTPUT_ROOT}/state.json --goal <goal-id> --status PASS --commit-sha <sha>
python3 ${OUTPUT_ROOT}/scripts/update_goal_state.py --state ${OUTPUT_ROOT}/state.json --goal <goal-id> --status FAIL --reason "<reason>"
python3 ${OUTPUT_ROOT}/scripts/update_goal_state.py --state ${OUTPUT_ROOT}/state.json --goal <goal-id> --status NEEDS_HUMAN --reason "<reason>"
```

`PASS` 前置检查：
- goal 存在。
- `result_dir` 存在，且是 `${GOAL_RESULT_ROOT}/<phase>/<goal-id>/`。
- `review_path` 存在，且 `REVIEW.md` 中可识别 `verdict = PASS`、`Review verdict: PASS` 或明确 `PASS`。
- `commit_info_path` 存在，且 `COMMIT_INFO.md` 中记录 commit sha 或 no commit needed reason。
- 如果提供 `--commit-sha`，写入当前 goal 的 `last_commit_sha`；如果未提供但 `COMMIT_INFO.md` 记录 no commit needed，也允许 `PASS`。
- `active_goal` 必须为当前 goal 或 `null`；如果是其它 goal，必须失败。

`FAIL` / `NEEDS_HUMAN`：
- 允许写入 `--reason` 到当前 goal 的 `last_state_update_reason`。
- 如果 `active_goal` 是当前 goal，必须更新为 `null`。
- 不要求 Review PASS，也不要求 `COMMIT_INFO.md` 完整。

只允许修改：
- 当前 goal 的 `status`、`last_commit_sha`、`updated_at`、`last_state_update_reason`、`last_completed_at`。
- 顶层 `active_goal`。
- 顶层 `last_run_id` 如果既有脚本需要且 state 已存在该字段；不得为此设计复杂结构。

禁止修改：
- `id`、`phase`、`depends_on`、`prompt_path`、`spec_path`、`goal_dir`、`result_dir`、`review_path`、`commit_info_path`、`expected_result_files`。
- `allowed_scope`、`forbidden_scope`、`validation.commands`。
- 后续 goal 定义或任何业务文件。

成功输出必须包含 `UPDATE_STATE PASS <goal-id>`、`UPDATE_STATE FAIL <goal-id>` 或 `UPDATE_STATE NEEDS_HUMAN <goal-id>`；失败时必须输出错误原因并使用非 0 exit code。

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
python3 ${LOOP_ROOT}/scripts/goal_gate.py --state ${LOOP_ROOT}/state.json --check
python3 ${LOOP_ROOT}/scripts/goal_gate.py --state ${LOOP_ROOT}/state.json --promote
python3 ${LOOP_ROOT}/scripts/goal_gate.py --state ${LOOP_ROOT}/state.json --next
python3 ${LOOP_ROOT}/scripts/validate_goal.py --state ${LOOP_ROOT}/state.json <goal_id>
python3 ${LOOP_ROOT}/scripts/goal_status.py --state ${LOOP_ROOT}/state.json
python3 ${LOOP_ROOT}/scripts/update_goal_state.py --state ${LOOP_ROOT}/state.json --goal <goal_id> --status PASS --commit-sha <sha>
```

不得硬编码 `docs/goal-loop` 或 `tmp/goal-loop`。
不得跳过 `--promote`；如果已有唯一 `READY` goal，`--promote` 应输出 skip/no-op 并返回成功。
执行器 Skill 必须固定执行顺序：解析 `LOOP_ROOT` / `STATE_PATH`，检测 `python3` / `python`，运行 `--check`、`--promote`、`--next`，只执行 `--next` 返回的唯一 `READY` goal，读取该 goal 的 `prompt_path`，执行 `PROMPT.md`，检查 `REVIEW.md`，检查 `COMMIT_INFO.md`，运行 `validate_goal.py`，调用 `update_goal_state.py` 回写 `PASS` / `FAIL` / `NEEDS_HUMAN`，再运行 `--check`、`--promote`、`--next` 只报告下一个 goal，然后停止。
状态回写属于 Loop 控制面职责，不属于业务 goal 的 `allowed_scope`；但只能修改 `STATE_PATH` 中当前 goal 的状态字段，不得修改业务文件或后续 goal 定义。
执行器 Skill 必须明确不得 `push`。
执行器 Skill 的最终输出必须包含 `Goal`、`Prompt path`、`Status`、`Result directory`、`Review verdict`、`Commit`、`State update`、`Validation`、`Next`。

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
- 必须先按固定顺序运行 gate：`--check`、`--promote`、`--next`。
- 必须检查 `REVIEW.md`。
- 必须检查 `COMMIT_INFO.md`。
- 必须执行 `validate_goal.py`。
- 必须调用 `update_goal_state.py` 回写当前 goal 的 `PASS` / `FAIL` / `NEEDS_HUMAN`。
- 状态回写后必须再次运行 `--check`、`--promote`、`--next`。
- 只能报告 next，不得执行 next。
- FAIL / NEEDS_HUMAN / NEEDS_HUMAN_DRAFT 即停。
- 不得执行下一个 goal。
- 不得修改 allowed_scope 之外文件。
- 只能读取 `prompt_path` 指向的 `PROMPT.md`。
- 不得 push。

## 8.1 PASS 标记前置条件

`goal-loop-engineer` 标记当前 goal 为 `PASS` 前，必须同时满足：

- `result_dir` 是 `${goal_result_root}/<phase>/<goal-id>/`。
- `expected_result_files` 全部存在于该 `result_dir`。
- `REVIEW.md` 中 `verdict = PASS`。
- `COMMIT_INFO.md` 存在，并记录 commit sha 或 no commit needed reason。
- `validate_goal.py` 返回 `VALIDATE PASS`。
- 当前 goal 未越界修改。
- 未执行 `git push`。

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
python3 <OUTPUT_ROOT>/scripts/goal_gate.py --state <OUTPUT_ROOT>/state.json --check
python3 <OUTPUT_ROOT>/scripts/goal_gate.py --state <OUTPUT_ROOT>/state.json --promote
python3 <OUTPUT_ROOT>/scripts/goal_gate.py --state <OUTPUT_ROOT>/state.json --next
python3 <OUTPUT_ROOT>/scripts/goal_status.py --state <OUTPUT_ROOT>/state.json
```
