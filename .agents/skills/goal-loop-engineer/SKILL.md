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

所有命令示例默认使用 `python3`。如果当前环境没有 `python3`，再尝试 `python`；如果两者都不存在，停止并报告 `PYTHON_UNAVAILABLE`。不得因为裸 `python` 命令不存在就判断 goal 失败。

## 1. Required Gate And Fixed Order

每次运行必须严格按以下顺序执行，且最多执行一个 goal：

1. 解析 `LOOP_ROOT` 和 `STATE_PATH`。优先读取 `tmp/goal-loop-current.json`；如果不存在，必须使用用户 prompt 中显式提供的路径。
2. 检测 Python 解释器，优先 `python3`，其次 `python`；两者都不存在则停止并报告 `PYTHON_UNAVAILABLE`。
3. 运行 `goal_gate.py --check`。
4. 运行 `goal_gate.py --promote`。
5. 运行 `goal_gate.py --next`。
6. 只能执行 `--next` 返回的唯一 `READY` goal。
7. 读取该 goal 的 `prompt_path` 指向的 `PROMPT.md`。
8. 严格按 `PROMPT.md` 执行当前 goal。
9. 检查 `REVIEW.md`。
10. 检查 `COMMIT_INFO.md`。
11. 运行 `validate_goal.py`。
12. 调用 `update_goal_state.py --status PASS` / `--status FAIL` / `--status NEEDS_HUMAN` 回写当前 goal 状态。
13. 再运行 `goal_gate.py --check`。
14. 再运行 `goal_gate.py --promote`。
15. 再运行 `goal_gate.py --next`，只报告下一个 goal。
16. 停止，不得执行下一个 goal。

标准 gate 命令：

```bash
python3 ${LOOP_ROOT}/scripts/goal_gate.py --state ${STATE_PATH} --check
python3 ${LOOP_ROOT}/scripts/goal_gate.py --state ${STATE_PATH} --promote
python3 ${LOOP_ROOT}/scripts/goal_gate.py --state ${STATE_PATH} --next
```

必须保持 `--check`、`--promote`、`--next` 顺序，不得跳过 `--promote`。如果 `--check`、`--promote` 或 `--next` 失败，停止并报告。

## 2. Execution Boundary

- 只能执行 `--next` 输出的 `prompt_path`。
- 不得执行其它 `PROMPT.md`。
- 不得读取其它 goal 的 `PROMPT.md`。
- 不得重新生成每个 goal 的执行 prompt。
- 不得修改 state 中 `allowed_scope` 之外的业务文件。
- 不得修改 state 中 `forbidden_scope` 命中的业务文件。
- 不得执行下一个 goal。
- 不得把任何 goal 初始化或擅自标记为 `PASS`。
- 不得 push。
- `PASS` 只能在目标 prompt 的 review 要求满足、验证通过、并有明确 Review PASS 证据后写入。

## 2.1 State Update Boundary

当前 goal 完成后的状态回写属于 Loop 控制面职责，不属于业务 goal 的 `allowed_scope`。因此 `goal-loop-engineer` 必须在 Review Gate 为 `PASS`、`COMMIT_INFO.md` 完整、`validate_goal.py` 返回 `VALIDATE PASS` 后，调用：

```bash
python3 ${LOOP_ROOT}/scripts/update_goal_state.py --state ${STATE_PATH} --goal <goal_id> --status PASS --commit-sha <sha>
```

如果当前 goal 明确失败或需要人工处理，必须调用：

```bash
python3 ${LOOP_ROOT}/scripts/update_goal_state.py --state ${STATE_PATH} --goal <goal_id> --status FAIL --reason "<reason>"
python3 ${LOOP_ROOT}/scripts/update_goal_state.py --state ${STATE_PATH} --goal <goal_id> --status NEEDS_HUMAN --reason "<reason>"
```

状态回写只能修改 `STATE_PATH` 中当前 goal 的状态字段：`status`、`last_commit_sha`、`updated_at`、`last_state_update_reason`、`last_completed_at`，以及 `active_goal`；不得修改业务文件，不得修改后续 goal 定义，不得修改 `id`、`phase`、`depends_on`、`prompt_path`、`spec_path`、`goal_dir`、`result_dir`、`review_path`、`commit_info_path`、`expected_result_files`、`allowed_scope`、`forbidden_scope` 或 `validation.commands`。

状态更新成功后，只能继续运行 `--check`、`--promote`、`--next` 来报告下一个 goal；不得读取或执行下一个 goal 的 `PROMPT.md`。

## 2.2 PASS Preconditions

标记当前 goal 为 `PASS` 前必须同时满足：

- `result_dir` 是 `<goal_result_root>/<phase>/<goal-id>/`。
- `expected_result_files` 全部存在于 `result_dir`。
- `REVIEW.md` 中可识别 `verdict = PASS`、`Review verdict: PASS` 或明确 `PASS`。
- `COMMIT_INFO.md` 存在，并记录 commit sha 或 no commit needed reason。
- `validate_goal.py` 返回 `VALIDATE PASS`。
- 当前 goal 未越界修改。
- 未执行 `git push`。

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
- `result_dir` 不是 `<goal_result_root>/<phase>/<goal-id>/`。
- `expected_result_files`、`review_path` 或 `commit_info_path` 缺失或指向 phase 目录。

## 4. Validation

goal 执行后必须运行：

```bash
python3 ${LOOP_ROOT}/scripts/validate_goal.py --state ${STATE_PATH} <goal_id>
python3 ${LOOP_ROOT}/scripts/goal_status.py --state ${STATE_PATH}
```

若需要只检查 scope 和 report，不运行验证命令，可使用：

```bash
python3 ${LOOP_ROOT}/scripts/validate_goal.py --state ${STATE_PATH} <goal_id> --skip-commands
```

`validate_goal.py` 失败时，必须按失败性质调用 `update_goal_state.py --status FAIL` 或 `--status NEEDS_HUMAN`，然后停止并报告失败项；不得继续后续 goal。

## 5. Final Response Shape

最终用中文输出：

```text
Goal:
Status:
Prompt path:
Result directory:
Review verdict:
Commit:
State update:
Validation:
Next:
```

`Next` 只能说明下一步等待人工确认或下次 Automation；不得自动执行下一个 goal。
