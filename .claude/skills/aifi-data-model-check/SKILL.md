---
name: aifi-data-model-check
description: Check AiForInterviewer data model, persistence boundaries, lifecycle states, privacy fields, and backend implementation alignment.
---

# aifi-data-model-check

## Purpose

检查数据模型、持久化边界、生命周期状态、隐私字段和后端实现是否一致。

## Applicable phases

- F4 技术架构、接口、数据、Prompt 设计
- F5 后端开发
- F7 联调、测试与质量加固

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md`。
3. 如 `DATA_MODEL.md` 已创建且登记，再读取该文件；否则标记 `UNKNOWN`。
4. 涉及实现时读取 `apps/api/` 相关持久化和 schema 文件。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-data-modeler`
- `aifi-backend-implementer`

## Execution steps

1. 确认数据模型文档 active 状态。
2. 检查实体、字段、状态、保留策略和敏感字段。
3. 对照后端持久化实现检查差异。
4. 输出迁移风险、隐私风险和测试建议。

## Forbidden actions

- 不得执行数据库写入、迁移或 destructive 操作。
- 不得读取 `.env`、密钥或凭据文件。
- 不得把未登记数据文档当作 active 依据。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改代码或文档，除非当前任务明确授权。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 数据模型状态和实现差异均引用证据。
- 敏感字段和保留策略风险被标记。
- 未验证数据库状态为 `UNKNOWN`。

## Risk markers

- 数据模型未登记。
- 持久化实现与契约不一致。
- 敏感字段缺少边界。
- 数据保留策略缺失。

## Recommended read-only commands

```bash
git status --short --ignored
find apps/api -maxdepth 4 -type f | sort
grep -RIn "schema\|store\|persistence\|retention\|AIFI-" apps/api docs 2>/dev/null || true
```

## Write authorization rules

默认只读。数据模型更新必须进入已登记 active 数据文档；后端实现变更只能在明确授权的 `AIFI-*` 任务范围内进行；任务进入 `BACKLOG.md`。
