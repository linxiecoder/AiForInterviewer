# 文档治理自动化规则

## 1. 目标与当前范围

- 本文档定义本地 `doc-governor` 的自动化边界。
- 当前最小闭环覆盖三条链路：
  - `bootstrap-state` 的白名单结构化扫描
  - `DOC_STATE.yaml` 的 validate / evaluate / render / confirm
  - 面向 `design/spec` 与 `plan/implementation` 文档的 round + Codex packet 工作流
- 当前不做：
  - 自动调用 Codex CLI 并自动应用变更
  - 自动批准文档状态
  - 从 Markdown 正文直接导入 confirmed state

## 2. 真值优先级

当前结构化真值优先级固定为：
1. `docs/governance/DOC_STATE.yaml`
2. `doc-governor` 的 diagnostics / evaluate / round / packet 结果
3. Markdown 正文叙述

注意：
- `docs/governance/DOC_STATE.bootstrap.yaml` 只是 bootstrap 输出，不是正式真值。
- bootstrap 文件不得被直接当成 readiness / candidate / maturity / document status 的最终结论。
- `documents[*].state.confirmed.*` 只能由 `confirm-transition` 或 round closeout 后的显式写回更新。

## 3. 白名单扫描来源

Phase 1A 的 `repo_scan` 仍只允许读取以下来源：
- 文件系统中的 `docs/modules/**`
- 根目录 `OPEN_QUESTIONS.md` 结构化表
- 根目录 `TASK_INDEX.md` 结构化表

Phase 1A 明确禁止：
- 从正文 prose 推断 maturity / readiness / candidate / review
- 从正文 prose 推断 `active_working_doc`
- 从非白名单 Markdown 段落导入共享契约真值

## 4. Official State 与 Document Entity 边界

- `documents` 一级治理对象只存在于 `docs/governance/DOC_STATE.yaml`。
- 当前只支持两类 document entity：
  - `design`
  - `plan`
- document entity 必须显式登记：
  - `meta.doc_type`
  - `meta.path`
  - `meta.required_sections`
  - `meta.relations`
- 允许从正文提取的事实仅包括：
  - heading 树
  - 必备章节命中情况
  - 显式 `OQ-*` / `Mxx` / 文档路径引用
  - `TODO/TBD/待确认/待补充` 等占位标记
- 不允许从正文直接导入：
  - `ready / blocked / approved / implementation-ready`
  - `candidate`
  - `maturity`
  - `active_round_id`
  - 任意 confirmed state

## 5. Bootstrap 输出与失败策略

默认输出固定为：
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/BOOTSTRAP_REPORT.md`

固定约束：
- 若输出文件已存在且未显式传 `--overwrite`，bootstrap 必须失败。
- bootstrap 无论如何不得写入或覆盖 `docs/governance/DOC_STATE.yaml`。
- 只要任意子任务命中 `implementation_doc.exists=true 且 template_like=false`，bootstrap 就必须整体失败，并且不得写出半可信的 `DOC_STATE.bootstrap.yaml`。

## 6. Evaluate Command Contract

Phase 2A `evaluate-state` 是只读命令：
- Command 只输出结构化 JSON，不写任何状态文件。
- 它不会修改 `DOC_STATE.bootstrap.yaml` 或 `DOC_STATE.yaml`。
- PyYAML 是读取 `DOC_STATE*.yaml` 的必需依赖。
- `delta_summary`（含 blocker 增减、review_required 变化、readiness 变化）仅用于本轮讨论优先级，不可替代人工确认与 `confirm-transition` 审核。
- `documents`、`governance_rounds`、`rounds_summary` 都属于 evaluate 输出的一部分，但仍然只是解释层，不是 confirmed state。

推荐主入口：

```powershell
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

## 7. Render Command Contract

- `render-report --evaluate-json <PATH>` 是主入口。
- `render-report --state <DOC_STATE.yaml>` 是 evaluate 的 wrapper，不得重写 evaluate 规则。
- 默认输出路径是 `docs/governance/DOC_GOVERNOR_REPORT.md`。
- `--report-path` 只允许写到 `docs/governance/` 下，且不得指向 `DOC_STATE.yaml` 或 `DOC_STATE.bootstrap.yaml`。
- `render-report` 只输出解释性 Markdown，不能直接驱动 `confirm-transition`。
- `## Next Round Agenda` 只输出建议性议程，不可直接替代审批与状态写回流程。

## 8. Round Lifecycle Contract

当前 round 生命周期固定为：

1. `plan-round`
2. `generate-round-template`
3. `generate-codex-packet`
4. 人工执行 Codex CLI
5. `update-round-status --status review`
6. `confirm-transition`
7. `update-round-status --status closed`

固定 round 状态：
- `open`
- `in_progress`
- `review`
- `closed`

固定 round 结构最少包括：
- `round_id`
- `workflow`
- `topic`
- `scope`
- `status`
- `opened_at`
- `opened_by`
- `decision_refs`
- `target_documents`
- `required_evidence_refs`
- `exit_criteria`
- `writeback_items`

## 9. Codex Packet Contract

Windows 本地统一使用：

```powershell
C:\Users\Administrator\AppData\Roaming\npm\codex.cmd exec
```

当前不支持 `codex.ps1`。

`generate-codex-packet` 固定生成三类产物：
- `docs/governance/packets/<round_id>.packet.json`
- `docs/governance/packets/<round_id>.prompt.md`
- `docs/governance/packets/<round_id>.exec.txt`

packet 必须至少包含：
- 本轮目标
- 目标文档
- 允许修改范围
- 禁止修改范围
- 治理约束
- 必须引用的 evidence / decision
- exit criteria
- 回写建议

## 10. confirm-transition Contract

- 默认输入文件是 `docs/governance/DOC_STATE.yaml`，若不存在直接失败。
- `confirm-transition` 只允许写入 `docs/governance/DOC_STATE.yaml`，禁止写入或覆盖 `DOC_STATE.bootstrap.yaml`。
- `module/subtask` 仍沿用原字段边界。
- `document` 当前只允许在 `--proposed-changes` 中提交：
  - `maturity`
  - `status`
  - `review_status`
  - `blocker_refs`
  - `active_round_id`
- `last_transition_id`、`last_confirmed_at`、`last_confirmed_by` 仅由系统在 approve 时写入，不允许在 proposed_changes 输入中携带。
- 当传入 `--round-id` 时，`--reason` 必须包含 `Decision:` 锚点。
- OQ `gate_policy_source=bootstrap_default` 不能作为自动通过 `candidate/readiness` 推进的充分依据；仅作为 review 依据之一。

## 11. 环境假设

- 当前 `doc-governor` 依赖本地 Python 环境可导入 `yaml`（PyYAML）。
- 当前不提供 YAML 解析/写入的自研 fallback。
- 若依赖缺失，CLI 必须 fail-fast。

检查命令：

```powershell
python -X utf8 -c "import yaml"
python -m tools.doc_governor.cli --help
```
