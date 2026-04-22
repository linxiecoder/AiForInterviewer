# 文档治理自动化规则

## 1. 目标与当前范围

- 本文档定义本地 `doc-governor` 的自动化边界。
- 当前仅覆盖 Phase 1A：结构化底座、白名单扫描、bootstrap 输出、模板/占位符识别。
- 当前不覆盖：`validate-state`、`evaluate`、`render`、`confirm-transition`、自动开窗。

## 2. 真值优先级

当前结构化真值优先级固定为：
1. `docs/governance/DOC_STATE.yaml`（正式真值，当前阶段保留）
2. `doc-governor` 的结构化 diagnostics / bootstrap 结果
3. Markdown 正文叙述

注意：
- `docs/governance/DOC_STATE.bootstrap.yaml` 只是 bootstrap 输出，不是正式真值。
- bootstrap 文件不得被直接当成 readiness / candidate / maturity 的最终结论。

## 3. 白名单扫描来源

Phase 1A 的 `repo_scan` 只允许读取以下来源：
- 文件系统中的 `docs/modules/**`
- 根目录 `OPEN_QUESTIONS.md` 结构化表
- 根目录 `TASK_INDEX.md` 结构化表

Phase 1A 明确禁止：
- 从正文 prose 推断 maturity / readiness / candidate / review
- 从正文 prose 推断 `active_working_doc`
- 从非白名单 Markdown 段落导入共享契约真值

## 4. Bootstrap 输出与失败策略

默认输出固定为：
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/BOOTSTRAP_REPORT.md`

固定约束：
- 若输出文件已存在且未显式传 `--overwrite`，bootstrap 必须失败。
- bootstrap 无论如何不得写入或覆盖 `docs/governance/DOC_STATE.yaml`。
- 只要任意子任务命中 `implementation_doc.exists=true 且 template_like=false`，bootstrap 就必须整体失败，并且不得写出半可信的 `DOC_STATE.bootstrap.yaml`。

## 5. 空模板与假信号

Phase 1A 当前必须识别并拦截以下假信号：
- 空 `SUBTASK_IMPLEMENTATION.md` 模板
- PowerShell / 变量占位符残留
- 明显统一模板骨架残留

这些信号只可用于“阻止假成熟度导入”，不能正向提升 readiness。

## 6. 环境假设

- 当前 `doc-governor` 依赖本地 Python 环境可导入 `yaml`（PyYAML）。
- 当前不提供 YAML 解析/写入的自研 fallback。
- 若依赖缺失，CLI 必须 fail-fast，并输出 `BOOTSTRAP_PYYAML_UNAVAILABLE`。

检查命令：

```powershell
python -X utf8 -c "import yaml"
```

## Evaluate Command Contract
Phase 2A evaluate-state is read-only report output.
- Command outputs structured JSON only and does not write any state files.
- It does not change DOC_STATE.bootstrap.yaml or DOC_STATE.yaml.
- PyYAML is required for reading DOC_STATE*.yaml inputs.

## OQ Bootstrap Defaults and Evaluate Boundary

- `bootstrap-state` must persist for every OQ entry: `gate_level`, `resolution_policy`, `status`, `affects`.
- Source priority is fixed:
  - explicit values from structured `OPEN_QUESTIONS.md` columns first;
  - fallback defaults only for missing OQ policy fields:
    - `gate_level = observe_only`
    - `resolution_policy = proposed_default_ok`
- Missing policy fields must emit only one aggregated warning `BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED` (not per-OQ warnings).
- `evaluate-state` is report-only and must not apply OQ policy defaults internally; missing policy fields should fail validation before evaluation.

## Render Command Contract

- `render-report --evaluate-json <PATH>` is the only primary render input.
- `render-report --state <DOC_STATE.bootstrap.yaml>` is an optional wrapper and must share the same evaluate path internally.
- `render-report` output is Markdown only and must only summarize fields in `summary/modules/subtasks/oqs/diagnostics`.
- `render-report` 的 `## Next Round Agenda` 仅输出建议性议程，不可直接替代 `confirm-transition` 的审批与状态写回流程。
- Default output path is `docs/governance/DOC_GOVERNOR_REPORT.md`.
- `--report-path` may only target files under `docs/governance/` and must not target official state files.
- The report must include fixed boundary notes stating it is report-only and not ready or ready-to-open status.

## init-official-state (Phase 3A.1) Contract

- Primary command: `python tools/doc_governor/cli.py init-official-state`.
- Default input file is `docs/governance/DOC_STATE.bootstrap.yaml`.
- Default output file is fixed to `docs/governance/DOC_STATE.yaml`; no alternate output paths are supported.
- `--force-overwrite` is disabled by default and required to replace an existing official state file.
- The official state copy includes:
  - `schema_version`
  - `global_policy`
  - `oqs` (with `gate_policy_source` preserved)
  - `modules[*].meta` / `modules[*].facts`
  - `subtasks[*].meta` / `subtasks[*].facts`
- `modules[*].state.confirmed` and `subtasks[*].state.confirmed` are initialized from factory defaults only (no auto-confirmed results import).
- `subtask.state.confirmed.implementation_doc_state` defaults to `missing`.
- `last_transition_id` / `last_confirmed_at` / `last_confirmed_by` are not imported from bootstrap.
- `init-official-state` does not write `transition_history.jsonl`.

## confirm-transition (Phase 3A) Contract
- 默认输入文件为 `docs/governance/DOC_STATE.yaml`，若不存在直接失败。
- `confirm-transition` 只允许写入 `docs/governance/DOC_STATE.yaml`，禁止写入/覆盖 `docs/governance/DOC_STATE.bootstrap.yaml`。
- `--proposed-changes` 仅允许 `maturity`、`candidate_status`、`review_status`、`readiness`、`blocker_refs`、`implementation_doc_state`。
- `last_transition_id`、`last_confirmed_at`、`last_confirmed_by` 仅由系统在 approve 时写入，不允许在 proposed_changes 输入中携带。
- `candidate_status` 提升到更高态（例如 none/observe -> candidate）必须提供至少一条 `--evidence-ref`。
- 当 OQ `gate_policy_source=bootstrap_default` 时，不能作为自动通过 `candidate/readiness` 推进的充分依据；仅作为 review 依据之一。
