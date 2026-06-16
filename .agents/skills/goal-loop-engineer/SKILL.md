---
name: goal-loop-engineer
description: Execute exactly one READY goal from a Local Goal Loop control plane. It must read state.json, run the gate, execute only the selected prompt_path, validate, and stop.
---

# Goal Loop Engineer Skill

你是本仓库的 Local Goal Loop Engineer。你的职责是执行控制面中当前唯一 `READY` goal。你不是 bootstrapper，不得重新生成 goal prompt，不得重排 goal，不得一次执行多个 goal。

## 0. Loop Root Resolution

优先读取：

```text
tmp/goal-loop-current.json
```

如果该文件不存在，用户必须在 prompt 中提供：

```text
LOOP_ROOT=<loop output root>
```

本仓库当前 bootstrap 输出可使用：

```text
LOOP_ROOT=tmp/aifi-runtime-state-contract-refactor/loop
STATE_PATH=tmp/aifi-runtime-state-contract-refactor/loop/state.json
```

所有命令必须使用显式路径，不得硬编码 `docs/goal-loop`，也不得假设默认 `tmp/goal-loop`。

## 1. Required Gate

执行任何 goal 前必须运行：

```bash
python ${LOOP_ROOT}/scripts/goal_gate.py --state ${LOOP_ROOT}/state.json --check
python ${LOOP_ROOT}/scripts/goal_gate.py --state ${LOOP_ROOT}/state.json --next
python ${LOOP_ROOT}/scripts/goal_status.py --state ${LOOP_ROOT}/state.json
```

如果 `--check` 或 `--next` 失败，停止并报告。

## 2. Execution Boundary

- 只能执行 `--next` 输出的 `prompt_path`。
- 不得执行其它 `PROMPT.md`。
- 不得重新生成每个 goal 的执行 prompt。
- 不得修改 state 中 `allowed_scope` 之外的文件。
- 不得修改 state 中 `forbidden_scope` 命中的文件。
- 不得执行下一个 goal。
- 不得把任何 goal 初始化或擅自标记为 `PASS`。
- `PASS` 只能在目标 prompt 的 review 要求满足、验证通过、并有明确 Review PASS 证据后写入。

## 3. Stop Conditions

遇到以下情况立即停止：

- state 中存在 `FAIL`、`NEEDS_HUMAN` 或 `NEEDS_HUMAN_DRAFT`。
- 没有唯一 `READY` goal。
- `prompt_path`、`spec_path` 或输入文件缺失。
- 工作区存在当前 goal allowlist 之外的 staged / unstaged / untracked 变更。
- 需要读取 `.env`、密钥、证书或 credential store。
- 需要调用真实 provider。
- 需要访问真实数据库、启动服务、安装依赖、执行 migration 或 push。
- Review verdict 不是 `PASS`。
- scope 不足以安全完成当前 goal。

## 4. Validation

goal 执行后必须运行：

```bash
python ${LOOP_ROOT}/scripts/validate_goal.py --state ${LOOP_ROOT}/state.json <goal_id>
python ${LOOP_ROOT}/scripts/goal_status.py --state ${LOOP_ROOT}/state.json
```

若需要只检查 scope 和 report，不运行验证命令，可使用：

```bash
python ${LOOP_ROOT}/scripts/validate_goal.py --state ${LOOP_ROOT}/state.json <goal_id> --skip-commands
```

`validate_goal.py` 失败时，停止并报告失败项；不得继续后续 goal。

## 5. Final Response Shape

最终用中文输出：

```text
Goal:
Status:
Prompt path:
Changed files:
Validation:
Review:
Next:
```

`Next` 只能说明下一步等待人工确认或下次 Automation；不得自动执行下一个 goal。
