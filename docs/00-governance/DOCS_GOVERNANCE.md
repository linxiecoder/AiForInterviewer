---
title: DOCS_GOVERNANCE
type: governance
status: active-f0
owner: 文档治理
permalink: ai-for-interviewer/docs/00-governance/docs-governance
---

# DOCS_GOVERNANCE

本文档定义 F0 文档治理落库后的文档生命周期和防腐规则。当前有效入口以 `docs/00-governance/DOCS_INDEX.md` 为准。

## 1. 文档职责

| 事项 | 唯一写入位置 |
| --- | --- |
| 当前有效文档索引 | `docs/00-governance/DOCS_INDEX.md` |
| 阶段与里程碑 | `docs/03-delivery/DELIVERY_PLAN.md` |
| 任务与优先级 | `docs/03-delivery/BACKLOG.md` |
| 历史需求继承和缺口 | `docs/01-product/REQUIREMENT_TRACEABILITY.md` |
| 归档动作 | `archive/MANIFEST.md` |
| AI / 人工协作约束 | `AGENTS.md`、`docs/00-governance/AI_WORKFLOW.md` |

## 2. 生命周期

| 状态 | 含义 | 要求 |
| --- | --- | --- |
| active | 当前执行、治理或追踪依据 | 必须登记到 `DOCS_INDEX.md` |
| reserved | 目录或编号保留，尚无生效文档 | 不得作为执行依据 |
| superseded | 已被 active 文档替代 | 保留到完成归档登记 |
| archived | 已迁入 archive | 只能作为历史来源或证据 |
| blocked | 因 state/source_doc/引用绑定暂不能移动 | 先登记阻断，不强行迁移 |

## 3. 命名规则

- 阶段只使用 `F0` 至 `F8`。
- 里程碑只使用 `M0` 至 `M8`。
- 任务只使用 `AIFI-*`。
- 优先级只使用 `MUST`、`SHOULD`、`COULD`、`LATER`。
- 不得新建新的 roadmap、plan-v2、latest-plan、codex-plan 或同类临时入口。

## 4. 归档规则

1. 归档前必须确认原路径、归档路径、替代路径、状态和阻断条件。
2. 归档动作必须写入 `archive/MANIFEST.md`。
3. 不能删除历史文档；只允许移动到 archive 并保留台账。
4. 仍被 state/source_doc/required doc slot 绑定的文件不得移动。
5. archive 只作历史来源，不能作为当前需求、设计、阶段或任务依据。

## 5. 历史需求处理

- 历史需求是否有效，只能通过 `docs/01-product/REQUIREMENT_TRACEABILITY.md` 判断。
- 历史需求进入实现前，必须迁入对应 active 文档或映射到 `AIFI-*` 任务。
- 未完成迁移的历史内容不得直接驱动开发。

## 6. 审计输出处理

- 审计报告归档到 `archive/2026-05-doc-consolidation/audit/`。
- 审计报告不是当前事实源，只能作为本轮治理证据。
- 若审计报告中发现有效内容，必须进入 active 文档后才能使用。
