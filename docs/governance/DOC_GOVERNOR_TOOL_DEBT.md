---
title: DOC_GOVERNOR_TOOL_DEBT
type: note
permalink: ai-for-interviewer/docs/governance/doc-governor-tool-debt
---

# Doc Governor 工具债追踪

## 1. 背景

本文件用于追踪 `doc_governor` 在 P0-2 / P0-3 已闭环后的 P1 / P2 工具债，避免低优先级工具问题继续拖慢 W13 主线设计推进。

本追踪文件只覆盖工具链与治理文档，不修改 W13 产品事实源，不修改正式 `docs/governance/DOC_STATE.yaml`，不生成 implementation packet，不打开 formal window，不标记 implementation-ready。

## 2. 当前已闭环 P0

- P0-2：candidate / readiness / formal window open 状态表达已通过 facts-only、near-ready facts、diagnostics、preflight gate 闭环。
- P0-3：formal window / implementation packet / implementation-ready 已有工具级 preflight / packet gate；packet gate 不再信任伪造 evaluate payload。
- 当前基线要求：`validate-state` 与 `evaluate-state` 必须保持 `ok=true`、`error=0`、`warning=0`，并且 `documents_blocked_count=0`。

## 3. P1 本窗口处理结果

| 编号 | 主题 | 处理结果 | 是否阻断当前 W13 主线 | 后续动作 |
| --- | --- | --- | --- | --- |
| P1-1 | render / report 与新 gate 摘要统一 | 已修复并补测试。`render-report` 新增子任务 gate 摘要，展示 `gate_result`、`can_open_formal_window`、`can_generate_implementation_packet`、`can_mark_implementation_ready`、top blockers、next actions，并明确 facts-only candidate 不等于 formal window open。 | 否 | 后续只在需要固定 asset/compliance 摘要时扩展 render。 |
| P1-2 | task readiness / sync 系列命令贯通新 gate 字段 | 已部分修复并补测试。`preview-task-state-dependency-map` 与 `preview-task-readiness-state-sync` 输出同一组 `gate_result/can_*` 字段；更宽的 `plan-task-readiness` 和其他 sync wrapper 保持现状，进入 P1 backlog。 | 否 | 单独工具窗口统一所有 task plan/sync Markdown 输出。 |
| P1-3 | asset / compliance / language governance 接入主链 | 已标准化并记录边界。当前已有 `asset_checks.py`、`language_check.py`、测试策略和语言规则；本窗口不扩成大型合规系统。 | 否 | 后续按 P1 backlog 决定是否把独立检查器接入主链 gate。 |
| P1-4 | MTxx_yy / legacy alias 迁移策略标准化 | 已标准化为文档规则，不迁移实际 ID，不改 schema，不改 `DOC_STATE.yaml`。 | 否 | 后续如需状态层支持 `MTxx_yy`，必须先确认 schema 与 alias 策略。 |
| P1-5 | stale / outdated 文档识别边界化 | 已标准化为工具边界。当前工具主要检查结构和状态，不完全判断内容方向是否过时。 | 否 | 后续可增强 stale OQ/DD/MQ/FC、current vs archive、unique fact source 检查。 |

## 4. P1 后续 backlog

### P1-BL-001：统一 task plan / sync Markdown gate 输出

- 类别：task readiness / sync 输出统一
- 优先级：P1
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P1-ReadinessSync-Output
- 触发条件：需要让 `plan-task-readiness`、`preview-task-readiness-fix`、`preview-task-state-writeback`、`preview-task-formal-window-sync` 等全部固定显示同一组 `gate_result/can_*` 字段。
- 不处理风险：不同 wrapper 的 Markdown 读者仍需回看 JSON 字段或 preflight 输出。
- 过度处理风险：容易把只读 plan/sync 输出误扩成状态写入能力。

### P1-BL-002：asset / compliance / language 检查器接入策略

- 类别：governance check 主链接入
- 优先级：P1
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P1-Compliance-Gate-Wiring
- 触发条件：需要让语言规则、临时产物规则、asset/compliance blocker 稳定参与 `validate-state` / `evaluate-state` / `render-report`。
- 不处理风险：部分规则仍只能靠 runbook、独立测试或人工审计发现。
- 过度处理风险：过早把不稳定检查接成 hard gate，导致状态推进被非核心治理噪音阻断。

### P1-BL-003：alias 只读展示与迁移策略

- 类别：task id / alias 治理
- 优先级：P1
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P1-Alias-Display
- 触发条件：`facts.business_task_id`、`facts.wt13_alias`、`facts.legacy_task_ids` 需要在 report / preflight / readiness 输出中稳定展示。
- 不处理风险：读者需要手工对照 W13 文档和状态层 `ST13_XX`。
- 过度处理风险：把 alias 当作状态层主键使用，破坏当前 schema 支持的 `STxx_yy` 约束。

### P1-BL-004：stale / outdated 文档识别增强

- 类别：文档事实源一致性
- 优先级：P1
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P1-Stale-Truth-Source
- 触发条件：历史文档、archive、superseded、current fact source 的误读开始影响开窗判断。
- 不处理风险：工具无法完整判断内容方向是否过时，仍需人工治理流程维护唯一事实源。
- 过度处理风险：自动 stale 判定误伤仍有追溯价值的历史文档。

## 5. P2 backlog

### P2-BL-001：RUNBOOK 示例矩阵完善

- 类别：runbook 示例
- 优先级：P2
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P2-Runbook-Matrix
- 触发条件：需要覆盖 blocked / facts-only / near-ready / formal-window-open / packet-ready 等示例矩阵。
- 不处理风险：新窗口需要反复从历史命令输出中拼示例。
- 过度处理风险：示例矩阵过长，反而掩盖当前主链最小路径。

### P2-BL-002：preview / dry-run / official state 一等命令

- 类别：状态操作体验
- 优先级：P2
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P2-State-Mode-UX
- 触发条件：preview YAML、dry-run、official write 的入口需要更统一的 CLI 体验。
- 不处理风险：窗口提示词仍需反复声明 official / preview / dry-run 边界。
- 过度处理风险：把 preview 通过误导成 official state 已变更。

### P2-BL-003：Basic Memory 更强自动化

- 类别：长期上下文写回
- 优先级：P2
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P2-BasicMemory-Automation
- 触发条件：需要把 Basic Memory guard 与讨论/收口窗口更自然地串起来。
- 不处理风险：会话总结仍依赖人工或独立 wrapper。
- 过度处理风险：把 Basic Memory 误当作 `DOC_STATE.yaml` 的正式结构化真值。

### P2-BL-004：工具报告中文化

- 类别：报告语言治理
- 优先级：P2
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P2-Report-i18n
- 触发条件：报告标题、说明性正文或 Markdown 输出继续出现英文自然语言漂移。
- 不处理风险：正式治理目录下的生成报告仍需人工辨认语言漂移。
- 过度处理风险：过度翻译命令名、JSON key、diagnostic code，降低技术准确性。

### P2-BL-005：模块历史文档进一步压缩

- 类别：历史文档治理
- 优先级：P2
- 是否阻断当前主线：否
- 建议处理窗口：ToolDebt-P2-Historical-Docs-Compression
- 触发条件：旧模块文档继续干扰 current fact source 判断。
- 不处理风险：历史文档可能被新窗口误读为当前任务事实源。
- 过度处理风险：过早删除或迁移仍有审计价值的历史记录。

## 6. 不阻断 W13 主线的问题

- `render-report` 中 requirement / asset / compliance 摘要未完整固定分区，不阻断 W13-E13.x / formal window candidate 主线。
- `plan-task-readiness` 等更宽 wrapper 尚未全部显示 `can_*` 字段，不阻断当前 facts-only State Update 后续讨论。
- `MTxx_yy` 未进入 schema，不阻断当前 `ST13_01~ST13_25` 状态层主线。
- stale / outdated 自动识别不完整，不阻断当前 ST13 candidate / formal-window 前置链路。
- Basic Memory 自动化增强属于 P2，不阻断当前工具 gate。

## 7. 仍可能阻断主线的问题

当前本窗口未发现新的 P1/P2 工具债直接阻断 W13 主线。

仍可能阻断主线的条件仅包括：

- `validate-state` 或 `evaluate-state` 不再全绿。
- `preflight-open-window` 对目标 ST13 误报可开窗。
- `generate-implementation-packet` 绕过 official state gate。
- 正式 `DOC_STATE.yaml` 或 W13 产品事实源被未授权修改。

## 8. 建议后续工具窗口

1. ToolDebt-P1-ReadinessSync-Output：统一 task plan/sync Markdown 的 gate 摘要。
2. ToolDebt-P1-Compliance-Gate-Wiring：决定 asset/language/compliance 检查器如何接入主链。
3. ToolDebt-P1-Alias-Display：只读展示 business alias / WT13 alias / legacy IDs。
4. ToolDebt-P1-Stale-Truth-Source：增强 current vs archive 与 stale 识别。
5. ToolDebt-P2-Runbook-Matrix：补齐示例矩阵，但不作为当前主线前置。

## 9. 不进入业务实现说明

本文件不定义业务功能，不创建 `apps/**` 或 `infra/**`，不生成 implementation packet，不打开 formal window，不把任何子任务标记为 implementation-ready。所有正式状态推进仍必须回到 `DOC_STATE.yaml`、`validate-state`、`evaluate-state`、`preflight-open-window`、`confirm-transition` 与用户确认窗口。