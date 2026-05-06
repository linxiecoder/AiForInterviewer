---
title: AI_WORKFLOW
type: governance
status: active-f0
owner: 文档治理
permalink: ai-for-interviewer/docs/00-governance/ai-workflow
---

# AI_WORKFLOW

本文档约束 Claude Code / Codex / AI 在 AiForInterviewer 仓库中的读取、修改、落库和收口流程。

## 1. 默认读取顺序

1. `AGENTS.md`
2. `docs/00-governance/DOCS_INDEX.md`
3. 与当前任务对应的唯一入口：
   - 阶段：`docs/03-delivery/DELIVERY_PLAN.md`
   - 任务：`docs/03-delivery/BACKLOG.md`
   - 需求追踪：`docs/01-product/REQUIREMENT_TRACEABILITY.md`
   - 归档：`archive/MANIFEST.md`
4. 当前任务明确列入允许范围的 active 文档或 ADR。

Scope 外已有本地改动只报告，不阻塞当前任务；除非用户明确授权或这些改动会影响允许文件的判断，不得读取、修改、暂存、回滚、删除或移动。

## 2. Scope 与安全读取

修改、审计、状态判断或续接任务前必须确认：

- 本轮 task_id、允许路径、禁止路径、允许操作、最终产物和完成条件是否明确。
- 任务 ID 是否使用 `AIFI-*`，阶段和里程碑是否仍属于 `F0`-`F8` / `M0`-`M8`。
- 只读取完成当前目标所需的最小 active 文件、ADR 或用户指定节点。
- 读写 Markdown 时按 UTF-8 处理；发现乱码、替换字符、异常问号或表格结构风险时先停止诊断。
- 不把 archive、长 Prompt、临时计划或历史审计报告作为当前执行依据。

安全读取的目标是得到可验证证据，不是扩大审计范围；没有本轮已读取证据支撑的结论必须标记 `UNKNOWN` 或 `待核查`。

## 3. Prompt Markdown 交互规则

面向 Claude Code、Codex、ChatGPT 或其他 AI 的 Prompt 必须满足：

- 使用可直接复制的 Markdown，优先中文表达。
- 文件路径、命令、代码标识符、API 字段、模型名和环境变量保持原样。
- 需要粘贴代码块、表格、反引号、竖线、反斜杠、引号或 JSON 时，使用 fenced code block 或明确转义，避免破坏 Markdown 结构。
- Prompt 只能承载当前轮次的执行指令；长期规则必须进入 active docs 或 ADR，不得用长 Prompt 替代文档治理。
- 不得创建 `.claude/plans/*`、临时 roadmap、并行任务系统或未登记的长期入口来保存 Prompt 结论。

## 4. 修改前检查

修改前必须确认：

- 本轮是否有明确目标、允许路径和禁止路径。
- 是否会新增文档入口、阶段体系或任务体系。
- 是否引用了 archive 内容作为执行依据。
- 是否触碰仍可能被 state/source_doc 绑定的旧文件。
- 是否需要先登记到 `BACKLOG.md` 或 `MANIFEST.md`。
- 是否存在同名任务、同名 ADR、重复索引或状态冲突。

## 5. 写入规则

| 内容 | 写入位置 |
| --- | --- |
| 新任务 | `docs/03-delivery/BACKLOG.md` |
| 新阶段或里程碑 | `docs/03-delivery/DELIVERY_PLAN.md` |
| 历史需求追踪 | `docs/01-product/REQUIREMENT_TRACEABILITY.md` |
| 归档动作 | `archive/MANIFEST.md` |
| 治理规则变更 | `docs/00-governance/DOCS_GOVERNANCE.md`、`docs/00-governance/AI_WORKFLOW.md` |
| 重大 AI 协作治理决策 | `docs/04-decisions/ADR-*.md` |

Codex 不得把临时分析文件升级为 active 文档，也不得绕过上述入口创建新的长期真值。

## 6. 最小审计与三轮推进

AI 协作默认采用最小审计：先核对任务 ID、允许文件、禁止文件、冲突项和完成条件，再读取必要证据并执行最小修改。

当用户要求继续推进、复核或让 ChatGPT / Claude Code / Codex 接力时：

1. 第一轮优先自行完成最小审查，确认是否存在冲突、越权读取、越权写入或证据缺口。
2. 第二轮只针对第一轮发现的问题定向修正，不扩大到全仓库审计。
3. 第三轮完成收口验证和剩余风险报告。
4. 第三轮后，除非出现新 task_id、新文件范围、新 ADR、用户明确要求或允许文件发生实质变更，不重复全面审计；只报告新增证据、剩余风险和最小下一步。

## 7. archive 使用规则

- 可以读取 archive 作为历史证据。
- 不得把 archive 作为当前执行依据。
- 需要复用 archive 内容时，先迁入 active 文档并建立追踪。
- 归档审计报告只提供证据，不替代 `DOCS_INDEX.md`、`DELIVERY_PLAN.md`、`BACKLOG.md` 或 `REQUIREMENT_TRACEABILITY.md`。

## 8. 完成输出

每次完成文档治理落库或迁移后，输出：

1. `git status --short`
2. `git diff --stat`
3. 新增文件清单
4. 修改文件清单
5. 移动到 archive 的文件清单
6. 仍需人工确认的问题
7. 旧阶段或旧任务体系是否仍存在于 active docs
8. Scope 外本地改动是否仅报告且未触碰
