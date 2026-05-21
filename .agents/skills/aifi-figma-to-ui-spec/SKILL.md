---
name: aifi-figma-to-ui-spec
description: Translate verified AiForInterviewer Figma design evidence into UI specification checks while marking unavailable MCP evidence as UNKNOWN.
---

# aifi-figma-to-ui-spec

## Purpose

将已验证的 Figma 设计证据转化为 UI 规范审阅输入；未接入 Figma MCP 时仅检查仓库文档登记，不声称读取 Figma。

## Applicable phases

- F2 低保真设计
- F3 高保真设计与设计系统
- F6 前端开发

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/02-design/UX_SPEC.md`。
3. 如 `UI_DESIGN_SYSTEM.md` 已创建且登记，再读取该文件。
4. 默认先运行或建议 `/aifi-drift-check`。
5. Figma MCP 不可用时，Figma 本体内容为 `UNKNOWN`。

## Delegatable SubAgents

- `aifi-figma-ux-auditor`
- `aifi-ui-design-system-owner`

## Execution steps

1. 确认仓库中登记的 Figma 链接、页面名和接受状态。
2. 判断是否具备可引用的设计证据。
3. 对可验证内容提出 UI 规范落库建议。
4. 对不可验证内容标记 `UNKNOWN` 并列出待接入项。

## Forbidden actions

- 不得调用不存在的 Figma MCP tool。
- 不得声称读取或验证未实际读取的 Figma 内容。
- 不得上传设计内容到外部服务。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改文件，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- Figma 证据来源被区分为仓库登记或 MCP 读取。
- 未接入 MCP 时所有 Figma 本体判断为 `UNKNOWN`。
- UI 规范建议引用 active 文档证据。

## Risk markers

- Figma 链接登记不完整。
- 设计系统未登记。
- 高保真状态未知。
- UI 规范缺少可验证来源。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "Figma\|Prototype\|Page\|UNKNOWN\|待核查" docs/02-design 2>/dev/null || true
```

## Write authorization rules

默认只读。UI 规范落库只能写入已登记 active 设计文档；任务缺口只能写入 `docs/03-delivery/BACKLOG.md`；需要当前任务明确授权。
