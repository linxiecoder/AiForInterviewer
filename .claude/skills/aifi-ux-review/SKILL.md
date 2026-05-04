---
name: aifi-ux-review
description: Review AiForInterviewer UX_SPEC and Figma-related low-fidelity evidence for scenario coverage, interaction consistency, and unresolved UX risks.
---

# aifi-ux-review

## Purpose

审阅 `UX_SPEC.md` 与 Figma 相关登记信息，判断低保真 UX 是否满足场景覆盖和交互一致性要求。

## Applicable phases

- F2 低保真设计
- F3 高保真设计与设计系统

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/02-design/UX_SPEC.md`、`docs/01-product/PRD.md`、`docs/03-delivery/BACKLOG.md`。
3. 如 `UI_DESIGN_SYSTEM.md` 未创建或未登记，标记为 `UNKNOWN`。
4. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-ux-flow-designer`
- `aifi-figma-ux-auditor`

## Execution steps

1. 核对 `UX_SPEC.md` 是否为当前 active 低保真入口。
2. 检查场景、页面、状态和人工接受状态。
3. 若 Figma MCP 未接入，只审阅文档登记，不声称读取 Figma 本体。
4. 输出 UX 缺口、风险和交接建议。

## Forbidden actions

- 不得调用不存在的 Figma MCP tool。
- 不得假设 Figma 内容。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改 `docs/` 或 `archive/`，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- UX 结论均引用本轮读取证据。
- Figma 未接入状态明确标记为 `UNKNOWN` 或 `待核查`。
- 缺口能追踪到需求或任务。

## Risk markers

- 低保真稿状态未知。
- UX 与 PRD 场景断链。
- 交互状态不完整。
- 高保真交接输入不足。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "Figma\|UNKNOWN\|待核查\|AIFI-" docs/02-design docs/03-delivery 2>/dev/null || true
```

## Write authorization rules

默认只读。UX 更新必须进入 `docs/02-design/UX_SPEC.md`；若需新增任务，只能写入 `docs/03-delivery/BACKLOG.md`，且需要当前任务明确授权。
