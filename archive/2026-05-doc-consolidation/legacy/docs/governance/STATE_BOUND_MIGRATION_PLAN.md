---
title: state-bound 文档迁移计划
type: note
permalink: ai-for-interviewer/docs/governance/state-bound-migration-plan
Owner: 文档治理
Last Updated: 2026-05-02
Scope: state-bound 文档迁移、generated/temp 产物策略和后续归档前置条件
Depends On: docs/governance/DOC_STATE.yaml, docs/governance/ACTIVE_DOC_CANON.md
Supersedes: none
---

# state-bound 文档迁移计划

## 目的

本文档用于记录当前文档体系收敛后的 state-bound 迁移边界，明确哪些已被替代、生成或归档候选对象仍受 `DOC_STATE.yaml`、`source_doc`、`meta.path`、required doc slot、preview 或 packet 绑定，避免在未解除引用前移动、归档或删除文件。

本文档是治理迁移计划，不是当前需求、设计、规划、任务或状态事实源，不替代 `docs/governance/DOC_STATE.yaml`。

## 当前结论

- 本窗口不移动、不删除、不归档文件。
- `DOC_STATE.yaml` 是状态真值，不能在没有独立 state update 窗口时修改。
- state-bound 文档必须先解除引用，再 `git mv`。
- generated/temp 产物只有确认无 gate / Daily Check / state 依赖后才能删除。
- archive 中保留有历史证据价值的文件。
- active docs 中最终不应残留废弃文档，但迁移必须分步完成。

当前不允许直接移动或删除的核心对象包括：

- `docs/planning/2026-04-25-current-repo-execution-plan.md`
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`
- `docs/tasks/workbench-mvp/st13-task-packages/**`
- `docs/governance/previews/**`
- `docs/governance/packets/**`
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml`
- `docs/governance/BOOTSTRAP_REPORT.md`
- `docs/governance/DOC_GOVERNOR_REPORT.md`
- `docs/governance/DOC_QUALITY_GATE_REPORT.md`

## 输入来源

- `archive/governance/2026-05-02-doc-convergence-audit/00-executive-summary.md`
- `archive/governance/2026-05-02-doc-convergence-audit/02-canon-index-audit.md`
- `archive/governance/2026-05-02-doc-convergence-audit/03-fact-conflict-audit.md`
- `archive/governance/2026-05-02-doc-convergence-audit.md`
- `docs/governance/DOC_STATE.yaml`
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/ACTIVE_DOC_CANON.md`
- `PLAN_LATEST.md`
- `TASK_INDEX.md`
- `docs/planning/workbench-mvp/README.md`
- `docs/planning/2026-04-25-current-repo-execution-plan.md`
- `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md`
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`
- `docs/tasks/workbench-mvp/st13-task-packages/**`
- `docs/governance/previews/**`
- `docs/governance/packets/**`
- `archive/ARCHIVE_INDEX.md`
- `archive/governance/archive-ledger.md`

## 分类规则

| action type | 定义 |
| --- | --- |
| `keep-active` | 仍是当前有效入口或正式支持文档。 |
| `keep-state-bound` | 已过时或 delegated，但仍被 `DOC_STATE.yaml`、metadata、packet 或 preview 绑定，暂不可移动。 |
| `archive-after-state-migration` | 应归档，但必须先更新 state、metadata 或 `source_doc` 引用。 |
| `archive-now-candidate` | 理论上可归档，但本窗口不执行移动。 |
| `delete-generated-after-policy-check` | 可考虑删除的 generated/temp 产物，但必须先确认 gate、Daily Check 和 state 不依赖。 |
| `keep-archive-evidence` | 已在 archive 中或应作为历史证据保留。 |
| `needs-human-decision` | 归属不清或可能影响可追溯证据，需要人工决定。 |

## state-bound 迁移矩阵

| path | current role | binding evidence | proposed final state | action type | prerequisite | risk |
| ---- | ------------ | ---------------- | -------------------- | ----------- | ------------ | ---- |
| `PLAN_LATEST.md` | 当前执行计划入口 | `ACTIVE_DOC_CANON.md` 将 planning 主入口指向本文档 | 保持 active | `keep-active` | 持续记录当前窗口和阻断项 | 低 |
| `TASK_INDEX.md` | 当前任务索引入口 | `ACTIVE_DOC_CANON.md` 将 task 主入口指向本文档 | 保持 active | `keep-active` | 持续以 `DOC_STATE.yaml` 和 gate 为准 | 低 |
| `docs/governance/ACTIVE_DOC_CANON.md` | 有效文档白名单 | AGENTS、PLAN、TASK 强引用 | 保持 active | `keep-active` | 登记本迁移计划但不赋予事实源地位 | 低 |
| `docs/planning/workbench-mvp/README.md` | planning 目录索引 | `ACTIVE_DOC_CANON.md` 登记为 planning index | 保持 active | `keep-active` | 只提供导航，不承载当前计划 | 低 |
| `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md` | backlog / roadmap 当前维护入口 | PLAN 和 archive ledger 引用其精简版；历史明细已归档 | 保持 active backlog | `keep-active` | 继续限制旧阶段词为 source/trace | 中 |
| `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | R0/R1/R2 长期阶段实施计划 | PLAN 和 canon 将其登记为长期计划 | 保持 active subordinate plan | `keep-active` | 不得声明为当前执行计划主入口 | 中 |
| `docs/planning/2026-04-25-current-repo-execution-plan.md` | 已废弃的 delegated planning 文档 | `DOC_STATE.yaml.documents.DOC-PLAN-CURRENT-REPO-2026-04-25.meta.path` 指向该路径；previews 也引用该路径 | 后续归档到 archive 或保留历史副本 | `archive-after-state-migration` | 独立 state update 窗口迁移 document entity `meta.path` 并通过 validate/evaluate | 高：直接移动会破坏 state document scan |
| `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 已废弃的 delegated task remap / ST13 source_doc | `DOC_STATE.yaml` 中 `ST13_01~ST13_25` 多处 `meta.path` / `source_doc` 指向该路径；previews 同步引用 | 后续归档到 archive 或保留历史副本 | `archive-after-state-migration` | 独立 state/source_doc migration 先更新 `ST13_*` metadata 并通过 validate/evaluate | 高：直接移动会破坏 ST13 状态引用 |
| `docs/tasks/workbench-mvp/st13-task-packages/**` | ST13 required docs 和 historical task evidence | `DOC_STATE.yaml` required doc slot、packets 的 `design_doc` / `implementation_doc`、任务索引均引用 | 保持 state-bound task packages | `keep-state-bound` | 后续若重命名或归档，必须先解除 state、packet、implementation docs 引用 | 高：误把 `ST13_*` 当旧阶段词清理会破坏 required docs |
| `docs/governance/DOC_STATE.yaml` | official state truth | AGENTS、DOC_AUTOMATION、PLAN、TASK 均声明为唯一正式状态真值 | 保持 active | `keep-active` | 只能在独立 state update 窗口按规则修改 | 高：本窗口禁止修改 |
| `docs/governance/DOC_STATE.bootstrap.yaml` | bootstrap generated artifact | DOC_AUTOMATION 定义其为 bootstrap 输出；本窗口 required input 仍读取 | 后续删除或归档候选 | `delete-generated-after-policy-check` | 确认 bootstrap、Daily Check、测试、gate 不依赖 tracked snapshot | 中 |
| `docs/governance/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` | root-level preview YAML | 与 `docs/governance/previews/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` 不完全相同；仍含 state-bound 路径引用 | 后续归档或删除候选 | `needs-human-decision` | 比对 root-level 与 previews 版本、transition evidence 和 ledger 后决定 | 中 |
| `docs/governance/previews/**` | preview state artifacts | 多个 preview YAML 保留 `source_doc`、ST13 required doc、planning path 和 packet refs | 保留为历史证据或迁入 archive | `needs-human-decision` | 检查 transition refs、执行日志、backlog 和是否已有归档副本 | 中 |
| `docs/governance/packets/**` | implementation packet artifacts | packet JSON/Markdown 绑定 `ST13_*` design/implementation docs 与 allowed/forbidden paths | 保留为 packet evidence 或迁入 archive | `needs-human-decision` | 确认对应 task state、implementation docs 和历史验收是否仍需直接读取 | 高 |
| `docs/governance/BOOTSTRAP_REPORT.md` | bootstrap generated report | DOC_AUTOMATION 定义为解释性 generated report，不是 official state | 后续删除或重生候选 | `delete-generated-after-policy-check` | 确认 quality gate、Daily Check 和审计流程不依赖 tracked 快照 | 中 |
| `docs/governance/DOC_GOVERNOR_REPORT.md` | doc-governor generated report | DOC_AUTOMATION 定义为解释性报告；审计包指出可能与 official state 不同步 | 后续重生、归档或删除候选 | `delete-generated-after-policy-check` | 确认是否需要保留最新 gate 快照；若保留应由工具重生 | 高 |
| `docs/governance/DOC_QUALITY_GATE_REPORT.md` | doc-quality-gate generated report | DOC_AUTOMATION 定义为 gate 输出；本窗口允许由 gate 受控更新 | 保留最新 gate 输出或后续按策略处理 | `delete-generated-after-policy-check` | 先运行 doc-quality-gate 并确认 gate/Daily Check 依赖 | 中 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | 历史 P1 设计稿 | 审计包历史覆盖矩阵引用，明确只作 archive evidence | 保持归档证据 | `keep-archive-evidence` | 不恢复为当前事实源 | 低 |
| `archive/docs/superpowers/plans/**` | 历史计划材料 | 审计包和执行日志只作为历史追溯引用 | 保持归档证据 | `keep-archive-evidence` | 后续只修复误当 current source 的引用 | 低 |
| `archive/planning/workbench-mvp/**` | 规划历史快照 | archive ledger 记录 backlog 历史明细迁入该目录 | 保持归档证据 | `keep-archive-evidence` | 不替代当前 backlog 或 PLAN_LATEST | 低 |
| `archive/governance/2026-05-02-doc-convergence-audit/**` | 本轮治理审计包 | W01/W02A/W02B/W02M 审计证据 | 保持归档证据 | `keep-archive-evidence` | 不作为 current facts source | 低 |

## 不可直接移动或删除的文档

- `docs/planning/2026-04-25-current-repo-execution-plan.md`：仍被 `DOC_STATE.yaml` 的 document entity 和多个 preview 绑定。
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`：仍被 `ST13_*` 的 `meta.path` / `source_doc` 和多个 preview 绑定。
- `docs/tasks/workbench-mvp/st13-task-packages/**`：仍是 required doc slot、packet 和任务证据引用对象。
- `docs/governance/previews/**`：可能承载 transition evidence、state preview 或历史验证证据。
- `docs/governance/packets/**`：可能承载 implementation packet 授权边界和历史验证证据。
- `docs/governance/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml`：root-level preview 与 `previews/` 下同名文件不完全相同，需先人工判定归属。

## 可后续归档的文档

- `docs/planning/2026-04-25-current-repo-execution-plan.md`：仅在 document entity state migration 后归档。
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`：仅在 ST13 `source_doc` / `meta.path` migration 后归档。
- `docs/governance/previews/**`：仅在确认 transition refs、执行日志和归档台账可追溯后归档。
- `docs/governance/packets/**`：仅在确认 implementation docs、state 和后续窗口不再直接依赖后归档。

## 可后续删除的 generated/temp 产物

- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/BOOTSTRAP_REPORT.md`
- `docs/governance/DOC_GOVERNOR_REPORT.md`
- `docs/governance/DOC_QUALITY_GATE_REPORT.md`

上述对象只能在 generated artifact policy 明确后处理。若 gate、Daily Check、测试、审计或人工复核仍读取 tracked 快照，应优先重生或归档，而不是直接删除。

## 需要人工决定的项目

- root-level `docs/governance/DOC_STATE_W13_E13_8_CANDIDATE_FACTS_PREVIEW.yaml` 是否保留、归档或删除。
- `docs/governance/previews/**` 是否按 state update 批次迁入 archive，或继续保留在治理目录。
- `docs/governance/packets/**` 是否作为授权证据长期保留，或按已关闭窗口迁入 archive。
- generated report 是否保留 tracked 最新快照，还是改为按需生成。
- state-bound migration 后是否使用 `git mv` 保留历史追踪，还是保留原路径并只降级为 historical source。

## 后续窗口

建议后续拆为四类独立窗口：

1. state/source_doc migration 预演窗口：只生成影响分析和 preview，不修改正式 `DOC_STATE.yaml`。
2. state update 执行窗口：在用户确认后更新 `DOC_STATE.yaml` 中 document entity、ST13 `meta.path` 和 `source_doc`。
3. generated artifact policy 窗口：决定 bootstrap、report、preview、packet 的保留、归档、重生或删除策略。
4. archive cleanup 窗口：在 state/gate 验证通过后，用 `git mv` 迁移已解除绑定的历史文档。

任一窗口发现 validate/evaluate、doc-quality-gate、Daily Check 或引用审计失败，应停止迁移并回到治理修复。

## 验证记录

本窗口记录的预期验证项：

- `git diff --check`
- `validate-state --input docs/governance/DOC_STATE.yaml`
- `evaluate-state --input docs/governance/DOC_STATE.yaml`
- `doc-quality-gate --repo-root .`
- `.venv/bin/python -m pytest tests/doc_governor tests/api tests/basic_memory_guard tests/test_temp_artifact_policy.py -q`
- `npm run test --workspace apps/web`
- `npm run build --workspace apps/web`
- 旧阶段体系、archive 引用和技术事实残留审计

验证结果以 `EXECUTION_LOG.md` 中 `R0-W05-FINAL-GOVERNANCE-CLOSURE` 追加记录为准。
