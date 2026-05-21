---
name: aifi-security-privacy
description: Review AiForInterviewer security, privacy, secrets, logs, data retention, LLM boundaries, and release-blocking risks.
---

# aifi-security-privacy

## Purpose

审阅安全、隐私、密钥边界、日志、数据保留、LLM 输入输出和发布阻断风险。

## Applicable phases

- F4 技术架构、接口、数据、Prompt 设计
- F7 联调、测试与质量加固
- F8 发布、复盘与下一轮迭代

## Required context

1. 先读取 `AGENTS.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/BACKLOG.md`。
3. 如 `SECURITY_PRIVACY.md` 已创建且登记，再读取该文件；否则标记 `UNKNOWN`。
4. 按任务读取相关 PRD、API、数据、Prompt、代码和测试证据。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-security-privacy-reviewer`
- `aifi-tech-architect`

## Execution steps

1. 确认安全隐私文档 active 状态。
2. 检查密钥、凭据、个人信息、日志和导出风险。
3. 检查 LLM 输入输出和数据保留边界。
4. 输出严重性、影响范围和阻断判断。

## Forbidden actions

- 不得读取 `.env`、密钥、证书或凭据文件。
- 不得提供破坏性、规避检测、批量攻击或未授权利用指导。
- 不得调用外部服务泄露内容。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得修改文件，除非当前任务明确授权实现修复。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 安全判断基于本轮读取证据。
- 敏感文件内容未读取，状态标记为 `UNKNOWN`。
- 发布阻断风险明确标记严重性和范围。

## Risk markers

- 敏感信息暴露。
- 权限边界不清。
- 日志或导出泄露。
- LLM 注入或数据保留缺口。

## Recommended read-only commands

```bash
git status --short --ignored
grep -RIn "secret\|token\|password\|privacy\|retention\|log" apps docs 2>/dev/null || true
```

## Write authorization rules

默认只读。安全文档更新必须进入已登记 active 安全文档；修复实现只能在明确授权范围内修改代码；任务进入 `BACKLOG.md`。
