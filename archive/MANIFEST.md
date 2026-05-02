---
title: MANIFEST
type: archive-manifest
status: active-f0
owner: 文档治理
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/archive/manifest
---

# archive/MANIFEST

> 本文件是唯一归档台账。archive 只保存历史来源、证据和废弃文档；不得作为当前执行依据。任何 archive 内容如仍有效，必须迁移到 active docs，并在 `docs/01-product/REQUIREMENT_TRACEABILITY.md` 登记。

## 1. 归档登记规则

| 字段 | 说明 |
|---|---|
| 原路径 | 文件归档前路径 |
| 归档路径 | archive 中的新路径 |
| 类型 | historical-source / superseded-doc / generated-artifact / evidence / template |
| 归档原因 | 为什么不再作为 active 文档 |
| 替代路径 | 当前 active 替代文档；没有则写 none |
| 状态 | proposed / archived / blocked / unknown |
| 前置条件 | state/source_doc/引用迁移要求 |
| 证据 | 本轮审计中的路径或行号摘要 |
| 归档日期 | 执行归档的日期，按 `YYYY-MM-DD` 记录 |

## 2. 已在 archive 中的历史来源

| 原路径 | 归档路径 | 类型 | 归档原因 | 替代路径 | 状态 | 前置条件 | 证据 |
|---|---|---|---|---|---|---|---|
| `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | historical-source | 历史 P1 设计，不是当前执行依据 | `docs/01-product/REQUIREMENT_TRACEABILITY.md`、`docs/01-product/PRD.md` | archived | 有效内容需迁移 | 快照 target-history-p1-design.md |
| `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | historical-source | 历史实施计划 | `docs/03-delivery/DELIVERY_PLAN.md`、`BACKLOG.md` | archived | 有效任务需映射到 AIFI-* | archive 目录存在 |
| `docs/superpowers/plans/2026-04-25/**` | `archive/docs/superpowers/plans/2026-04-25/**` | historical-source | 历史设计/计划包 | 目标 docs 体系 | archived | 逐项提取有效事实 | archive 目录存在 |
| `archive/governance/2026-05-02-doc-convergence-audit/**` | 同路径 | evidence | 历史审计证据 | none | archived | 不作为 current facts | 旧治理索引已声明 archive audit 不是 current facts source |
| `archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md` | 同路径 | historical-source | backlog 历史过程明细 | `docs/03-delivery/BACKLOG.md` | archived | 有效工作项需重编为 AIFI-* | `archive/governance/archive-ledger.md` |

## 3. F0 审计报告归档

| 原路径 | 归档路径 | 类型 | 归档原因 | 替代路径 | 状态 | 前置条件 | 证据 |
|---|---|---|---|---|---|---|---|
| F0 主审计报告输出 | `archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md` | evidence | F0 文档治理审计报告，只作历史证据 | `docs/00-governance/DOCS_INDEX.md` | archived | none | 本轮固定归档路径 |
| Markdown/MDX 全量盘点输出 | `archive/2026-05-doc-consolidation/audit/MARKDOWN_INVENTORY.md` | evidence | F0 全量盘点，只作历史证据 | `docs/00-governance/DOCS_INDEX.md` | archived | none | 本轮固定归档路径 |
| 重复、废弃、冲突识别输出 | `archive/2026-05-doc-consolidation/audit/DOC_CONFLICTS_AND_DUPLICATES.md` | evidence | F0 冲突识别，只作历史证据 | `docs/00-governance/DOCS_GOVERNANCE.md` | archived | none | 本轮固定归档路径 |

## 4. 现有归档台账合并项

| 原路径 | 归档路径 | 类型 | 归档原因 | 替代路径 | 状态 | 前置条件 | 证据 |
|---|---|---|---|---|---|---|---|
| `archive/ARCHIVE_INDEX.md` | `archive/2026-05-doc-consolidation/archive-index.replaced.md` | superseded-doc | 台账入口分裂 | `archive/MANIFEST.md` | proposed | MANIFEST 生效后迁移 | `archive/ARCHIVE_INDEX.md` 仅两条记录 |
| `archive/governance/archive-ledger.md` | `archive/2026-05-doc-consolidation/archive-ledger.replaced.md` | superseded-doc | 台账入口分裂 | `archive/MANIFEST.md` | proposed | MANIFEST 生效后迁移 | archive ledger 仅一条记录 |

## 5. F0.1 已归档旧入口与旧文档

| 原路径 | 归档路径 | 类型 | 归档原因 | 替代路径 | 状态 | 前置条件 | 证据 | 归档日期 |
|---|---|---|---|---|---|---|---|---|
| `PLAN_LATEST.md` | `archive/2026-05-doc-consolidation/delivery/PLAN_LATEST.md` | superseded-doc | 旧 planning 入口被目标交付计划替代 | `docs/03-delivery/DELIVERY_PLAN.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `TASK_INDEX.md` | `archive/2026-05-doc-consolidation/delivery/TASK_INDEX.md` | superseded-doc | 旧任务入口被 Backlog 替代 | `docs/03-delivery/BACKLOG.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `DAILY_EXECUTION_PANEL.md` | `archive/2026-05-doc-consolidation/legacy/root/DAILY_EXECUTION_PANEL.md` | superseded-doc | 旧根执行面板不再作为 active 入口 | `docs/00-governance/DOCS_INDEX.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `DESIGN_DECISIONS.md` | `archive/2026-05-doc-consolidation/legacy/root/DESIGN_DECISIONS.md` | superseded-doc | 旧根决策入口被 ADR 目录替代 | `docs/04-decisions/ADR-*.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `DOCUMENT_MATURITY.md` | `archive/2026-05-doc-consolidation/legacy/root/DOCUMENT_MATURITY.md` | superseded-doc | 旧成熟度入口不再作为 active 事实源 | `docs/00-governance/DOCS_INDEX.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `DOCUMENT_PROGRESS.md` | `archive/2026-05-doc-consolidation/legacy/root/DOCUMENT_PROGRESS.md` | superseded-doc | 旧进展入口不再作为 active 事实源 | `docs/00-governance/DOCS_INDEX.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `EXECUTION_LOG.md` | `archive/2026-05-doc-consolidation/legacy/root/EXECUTION_LOG.md` | superseded-doc | 旧执行日志不再作为 active 入口 | `docs/03-delivery/BACKLOG.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `MODULE_INDEX.md` | `archive/2026-05-doc-consolidation/legacy/root/MODULE_INDEX.md` | superseded-doc | 旧模块索引被 Backlog 和后续 active 设计文档替代 | `docs/03-delivery/BACKLOG.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `OPEN_QUESTIONS.md` | `archive/2026-05-doc-consolidation/legacy/root/OPEN_QUESTIONS.md` | superseded-doc | 旧开放问题入口不再作为 active 入口 | `docs/03-delivery/BACKLOG.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `TECHNICAL_STANDARDS.md` | `archive/2026-05-doc-consolidation/legacy/root/TECHNICAL_STANDARDS.md` | superseded-doc | 旧技术标准不再作为 active 入口 | 后续 active 技术设计文档 | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/DOC_GOVERNANCE.md` | `archive/2026-05-doc-consolidation/legacy/docs/DOC_GOVERNANCE.md` | superseded-doc | 旧文档治理入口被 `DOCS_GOVERNANCE.md` 替代 | `docs/00-governance/DOCS_GOVERNANCE.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/SUBTASK_DOC_TEMPLATES.md` | `archive/2026-05-doc-consolidation/legacy/docs/SUBTASK_DOC_TEMPLATES.md` | template | 旧子任务模板不再作为 active 任务体系入口 | `docs/03-delivery/BACKLOG.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/project-language-rules.md` | `archive/2026-05-doc-consolidation/legacy/docs/project-language-rules.md` | superseded-doc | 旧语言规范并入 F0 协作规则和治理规则 | `AGENTS.md`、`docs/00-governance/DOCS_GOVERNANCE.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/governance/**` | `archive/2026-05-doc-consolidation/legacy/docs/governance/**` | superseded-doc / generated-artifact / evidence | 旧治理状态、报告、packet 和 preview 不再作为 active 入口 | `docs/00-governance/**`、`archive/MANIFEST.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/planning/**` | `archive/2026-05-doc-consolidation/legacy/docs/planning/**` | superseded-doc | 旧规划体系被 `DELIVERY_PLAN.md` 替代 | `docs/03-delivery/DELIVERY_PLAN.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/tasks/**` | `archive/2026-05-doc-consolidation/legacy/docs/tasks/**` | superseded-doc | 旧任务包被 `BACKLOG.md` 替代 | `docs/03-delivery/BACKLOG.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/modules/**` | `archive/2026-05-doc-consolidation/legacy/docs/modules/**` | superseded-doc | 旧模块文档不再作为 active source of truth | `docs/03-delivery/BACKLOG.md`、后续 active 设计文档 | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/requirements/**` | `archive/2026-05-doc-consolidation/legacy/docs/requirements/**` | historical-source | 迁移前需求事实源转为历史来源 | `docs/01-product/REQUIREMENT_TRACEABILITY.md`、后续 `PRD.md` | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/design/**` | `archive/2026-05-doc-consolidation/legacy/docs/design/**` | historical-source | 迁移前设计事实源转为历史来源 | 后续 active 设计文档 | archived | none | F0.1 `git mv` | 2026-05-02 |
| `docs/development/**` | `archive/2026-05-doc-consolidation/legacy/docs/development/**` | historical-source | 迁移前开发说明转为历史来源 | 后续 active 技术设计或测试文档 | archived | none | F0.1 `git mv` | 2026-05-02 |

## 6. 禁止事项

1. 禁止把 archive 下任何文档作为 PRD、设计、计划或任务的当前依据。
2. 禁止在未登记本 MANIFEST 的情况下移动、删除或归档 Markdown/MDX。
3. 禁止以“已有历史文档”为理由跳过 `REQUIREMENT_TRACEABILITY.md`。
4. 禁止归档仍被 state/source_doc/required doc slot 绑定的文件。
