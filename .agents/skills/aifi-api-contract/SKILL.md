---
name: aifi-api-contract
description: Check AiForInterviewer API contracts across PRD, UX, backend, frontend, error semantics, and AIFI task acceptance criteria.
---

# aifi-api-contract

## Purpose

检查 API 契约是否覆盖 PRD/UX 场景，并与后端、前端和 `AIFI-*` 验收标准一致。

## Applicable phases

- F4 技术架构、接口、数据、Prompt 设计
- F5 后端开发
- F6 前端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/01-product/PRD.md`、`docs/02-design/UX_SPEC.md`、`docs/03-delivery/BACKLOG.md`。
3. 如 `API_SPEC.md` 已创建且登记，再读取该文件；否则标记 `UNKNOWN`。
4. 涉及实现时读取相关后端和前端代码。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-api-contract-designer`
- `aifi-backend-implementer`
- `aifi-frontend-implementer`

## Execution steps

1. 确认 API 规范 active 状态。
2. 跨模块理解、调用链分析、DDD / Agent / `PolishUseCases` 重构前，必须先经过 `aifi-context-index-gate`，用 Understand-Anything / CodeGraph 获取压缩上下文，再最小化 `Read` / `Grep`。
3. docs false-done closeout、runtime evidence recon、Agent / `PolishUseCases` / DDD 与 API contract 交叉验证任务，先走 `aifi-context-index-gate`，再读取 PRD / UX / API_SPEC / backend / frontend 最小证据。
4. 对照 PRD/UX 检查接口、字段、错误语义和边界状态。
5. 对照代码检查前后端契约一致性。
6. 输出断链、兼容风险和测试建议。

## Forbidden actions

- 不得把未登记 API 文档当作 active 依据。
- 不得扩大到无关重构。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改代码或文档，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- API 状态、字段和错误语义判断均有证据。
- 未登记契约标记 `UNKNOWN`。
- 前后端差异列出具体路径或待核查项。

## Risk markers

- API 规范缺失或未登记。
- 前后端字段不一致。
- 错误语义未定义。
- 关键路径无测试。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "fetch\|axios\|route\|APIRouter\|AIFI-" apps docs/03-delivery docs/02-design 2>/dev/null || true
```

## Write authorization rules

默认只读。API 规范更新必须进入已登记 active API 文档；实现变更只能在明确授权的 `AIFI-*` 任务范围内修改代码；任务进入 `BACKLOG.md`。
