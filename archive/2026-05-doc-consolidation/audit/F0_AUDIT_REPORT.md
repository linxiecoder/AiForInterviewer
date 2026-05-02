---
title: F0_DOC_GOVERNANCE_AUDIT_REPORT
type: note
permalink: ai-for-interviewer/archive/2026-05-doc-consolidation/audit/f0-doc-governance-audit-report-2
---

# F0 文档治理与需求继承审计报告

## 0. 输入边界

- 唯一输入：`aifi-docs-snapshot.zip`。
- 解包后扫描：`files/` 下 Markdown/MDX；历史 P1 另以 `target-history-p1-design.md` 核查。
- 未读取到的文件内容一律标记 UNKNOWN。特别是 `docs/governance/DOC_STATE.yaml` 只在 Markdown 中被引用，快照未包含其正文，因此 state/source_doc 绑定详情为 UNKNOWN。
- archive 只作为历史来源，不作为执行依据。

## 1. 结论

1. 当前文档体系未达到目标有效文档体系：目标 docs/00、docs/01、docs/02、docs/03、docs/04 目录和 `archive/MANIFEST.md` 均缺失。
2. 历史 P1 设计未被当前核心需求完整吸收；状态为“部分吸收”。
3. 旧推进体系仍是 active 文档事实源的一部分：非 archive/test 的 Markdown/MDX 中有旧术语的文件为 183 / 224。必须迁移到 F0-F8、M0-M8、AIFI-* 后才能宣布完成废弃。
4. 未发现 SHA-256 完全重复文件；去除 YAML front matter 后存在正文重复模板，尤其模块/子任务 `SUBTASK_IMPLEMENTATION.md`。
5. 本轮输出的是重构建议稿，未修改仓库文件。

## 2. Markdown/MDX 盘点

- 总数：265
- root：12
- docs：211
- archive：32
- tests：9
- infra：1

| family | count |
|---|---:|
| modules | 150 |
| archive | 32 |
| tasks | 21 |
| governance | 20 |
| root | 12 |
| test_fixture | 9 |
| design | 6 |
| planning | 5 |
| development | 4 |
| docs | 3 |
| requirements | 2 |
| infra | 1 |

完整清单见 `F0_MARKDOWN_MDX_INVENTORY.md`。

## 3. 目标文档体系缺口

| 路径 | 快照状态 |
|---|---|
| `README.md` | FOUND |
| `AGENTS.md` | FOUND |
| `CHANGELOG.md` | MISSING |
| `docs/README.md` | MISSING |
| `docs/00-governance/DOCS_INDEX.md` | MISSING |
| `docs/00-governance/DOCS_GOVERNANCE.md` | MISSING |
| `docs/00-governance/AI_WORKFLOW.md` | MISSING |
| `docs/01-product/PRD.md` | MISSING |
| `docs/01-product/REQUIREMENT_TRACEABILITY.md` | MISSING |
| `docs/02-design/UX_SPEC.md` | MISSING |
| `docs/02-design/UI_DESIGN_SYSTEM.md` | MISSING |
| `docs/02-design/TECH_DESIGN.md` | MISSING |
| `docs/02-design/API_SPEC.md` | MISSING |
| `docs/02-design/DATA_MODEL.md` | MISSING |
| `docs/02-design/PROMPT_SPEC.md` | MISSING |
| `docs/02-design/SECURITY_PRIVACY.md` | MISSING |
| `docs/03-delivery/DELIVERY_PLAN.md` | MISSING |
| `docs/03-delivery/BACKLOG.md` | MISSING |
| `docs/03-delivery/TEST_PLAN.md` | MISSING |
| `docs/03-delivery/RELEASE_CHECKLIST.md` | MISSING |
| `docs/04-decisions` | MISSING |
| `archive/README.md` | MISSING |
| `archive/MANIFEST.md` | MISSING |

## 4. 重复、废弃、冲突识别

- 完全重复：未发现 SHA-256 完全相同的 Markdown/MDX。
- 正文完全重复组：2 组（去除 YAML front matter 后）：28 个 `SUBTASK_IMPLEMENTATION.md` 占位模板、3 个 `MODULE_EXECUTION_LOG.md` 模板；完整文件 SHA 完全重复为 0。
- 同名多文件：`SUBTASK_DESIGN.md`、`SUBTASK_IMPLEMENTATION.md`、`MODULE_*` 等在模块体系中大量重复；结构上可存在，但不能替代全局唯一 PRD/设计/API/Data/Backlog。
- 废弃候选：`PLAN_LATEST.md`、`TASK_INDEX.md`、`docs/planning/workbench-mvp/**`、`docs/tasks/workbench-mvp/**`、旧归档台账、生成/packet/previews。受 state/source_doc 绑定影响的文件必须先解除引用。
- 冲突：当前 README/AGENTS/PLAN/TASK/MASTER plan 等仍把旧推进体系作为 active planning/task 规则，与本轮目标直接冲突。

详细清单见 `F0_DUPLICATE_DEPRECATED_CONFLICTS.md`。

## 5. 历史 P1 吸收审计

结论：未完整吸收。

| P1 主题 | 吸收状态 | 主要缺口 |
|---|---|---|
| 文本面试主闭环 | PARTIAL | 当前需求承接主闭环，但 PRD 目标文件缺失，资产/管理台/角色未统一 |
| 团队/用户/权限 | PARTIAL / NEEDS_DECISION | 团队管理员/成员、普通用户/管理员、team_id 策略未统一 |
| 题目生成与参考材料原则 | MISSING / PARTIAL | 未找到 active 文档明确写入“参考材料包不是题库”“考点规划→问题生成” |
| PDF/Markdown 简历 | PARTIAL | 模块文档承接，但全局 PRD/API/Data 未统一；复盘导出与简历 PDF 导出边界混淆 |
| 打磨/模拟/真实复盘 | PARTIAL | 模式存在但状态机、能力树、通过概率规则未冻结 |
| 技术方案 | REPLACED / NEEDS_DECISION | 历史 Next.js/pgvector/Redis/object storage 与当前 Vite+React/PostgreSQL+SQLite fallback 存在替代关系 |
| 数据模型 | PARTIAL | 对象模型分散，目标 DATA_MODEL.md 缺失 |
| 弱项/训练 | PARTIAL | 训练抽屉承接，状态与消减规则不完整 |
| 视觉/UI | PARTIAL / MISSING | 目标 UI_DESIGN_SYSTEM.md 缺失，现有低保真带旧阶段标签 |

完整矩阵见 `proposed/docs/01-product/REQUIREMENT_TRACEABILITY.md`。

## 6. 证据

- `SNAPSHOT_README.md` 说明快照包含 Markdown/MDX、repo-files、docs-files、risk-keywords 和目标历史 P1 文档。
- `README.md:15-30` 当前入口仍指向 `docs/requirements/workbench-mvp/**`、`docs/design/workbench-mvp/**`、`PLAN_LATEST.md`、`TASK_INDEX.md`、长期计划等旧入口。
- `ACTIVE_DOC_CANON.md:24-35` 将旧路径登记为当前唯一主入口；`ACTIVE_DOC_CANON.md:53-55` 同时声明 generated/archive 不是事实源。
- `PLAN_LATEST.md:16`、`PLAN_LATEST.md:56-58` 仍引用旧长期阶段和窗口。
- `TASK_INDEX.md:31-35` 将旧任务组登记为当前任务组；`TASK_INDEX.md:50-51` 固化旧阶段/任务命名规则。
- `AGENTS.md` 多处要求按旧交付切片推进，必须改写为本轮目标体系。
- `target-history-p1-design.md:62-75` 定义团队模型和参考材料原则；当前 active docs 未完整承接。
- `target-history-p1-design.md:77-83` 定义 PDF/Markdown 简历处理；M03 模块有承接，但目标 PRD/API/Data 缺失。
- `target-history-p1-design.md:218-245` 定义题目生成两步法和追问日志；active docs 搜索未命中该规则。
- `target-history-p1-design.md:415-460` 要求规则化评分和通过概率；当前评分设计强调可解释，但没有完整规则。
- `target-history-p1-design.md:557-652` 定义弱项状态和训练抽屉；当前设计只部分承接。
- `target-history-p1-design.md:1083-1125` 定义视觉风格；目标 UI 设计系统缺失。

## 7. 风险

1. `DOC_STATE.yaml` 正文缺失，不能确认哪些旧文件可安全移动或删除。
2. 旧 active 文档仍强引用旧推进体系，若直接删除会破坏 README/AGENTS/PLAN/TASK 的入口一致性。
3. 历史 P1 有大量仍有价值的产品/设计内容，若只归档不迁移，会造成需求丢失。
4. 模块文档数量大且模板重复，若不建立唯一 Backlog，后续 Codex 容易再次生成并行任务体系。
5. 当前技术栈事实与历史技术建议存在差异，必须用 ADR 固化，避免实现阶段来回摇摆。

## 8. 待处理文件

| 文件/目录 | 处理动作 | 阻断 |
|---|---|---|
| `README.md` | 重写入口到目标 docs 体系 | 需目标文件落地 |
| `AGENTS.md` | 改写 AI 工作流和防腐规则 | 需移除旧 active 推进规则 |
| `PLAN_LATEST.md` | 迁移到 DELIVERY_PLAN 后废弃 | `state/source_doc UNKNOWN` |
| `TASK_INDEX.md` | 迁移到 BACKLOG 后废弃 | `state/source_doc UNKNOWN` |
| `docs/requirements/workbench-mvp/**` | `迁入 PRD/Traceability 后归档` | 需逐条比对 |
| `docs/design/workbench-mvp/**` | `拆分迁入 UX/UI/TECH/API/DATA/PROMPT/SECURITY` | 需清理旧阶段标签 |
| `docs/planning/workbench-mvp/**` | `有效内容迁入 Delivery/Backlog；旧内容归档` | `state/source_doc UNKNOWN` |
| `docs/tasks/workbench-mvp/**` | 映射 AIFI-*；解除绑定后归档 | `state/source_doc UNKNOWN` |
| `docs/modules/**` | `抽取有效事实；重复模板归档/合并` | 需确认是否含执行事实 |
| `archive/ARCHIVE_INDEX.md + archive/governance/archive-ledger.md` | `合并到 archive/MANIFEST.md` | MANIFEST 生效 |
| `docs/governance/previews/** + packets/**` | `生成产物归档/删除策略` | 需确认 gate 依赖 |
| `docs/governance/DOC_STATE.yaml` | 状态绑定核查 | 快照未包含正文，UNKNOWN |

## 9. 下一步动作

1. 先落地 `docs/00-governance/DOCS_INDEX.md`、`docs/01-product/REQUIREMENT_TRACEABILITY.md`、`docs/03-delivery/DELIVERY_PLAN.md`、`docs/03-delivery/BACKLOG.md`、`archive/MANIFEST.md`。
2. 读取并核查 `docs/governance/DOC_STATE.yaml`，生成 state/source_doc 迁移清单；未解除绑定前不移动旧 task/planning 文件。
3. 编写 `docs/01-product/PRD.md`，把历史 P1 中 PARTIAL/MISSING 且决定保留的内容迁入。
4. 将旧 active 文档逐步标记 superseded，并按 `archive/MANIFEST.md` 归档到 `archive/2026-05-doc-consolidation/`。
5. 建立检查脚本：禁止新增临时路线图文件、禁止 archive 被 active docs 当执行依据、禁止任务绕过 Backlog。