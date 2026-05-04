---
name: aifi-release-check
description: Check AiForInterviewer release readiness across release checklist, backlog, delivery milestones, tests, security review, residual risk, and rollback evidence.
---

# aifi-release-check

## Purpose

检查 F8 发布准备度，覆盖发布清单、任务、里程碑、测试、安全审阅、残余风险和回滚准备。

## Applicable phases

- F8 发布、复盘与下一轮迭代
- M8 MVP 可发布

## Required context

1. 先读取 `CLAUDE.md`、`AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`。
2. 必须读取 `docs/03-delivery/DELIVERY_PLAN.md`、`docs/03-delivery/BACKLOG.md`。
3. 如 `TEST_PLAN.md`、`RELEASE_CHECKLIST.md` 或安全文档已创建且登记，再读取；否则标记 `UNKNOWN`。
4. 读取相关测试结果和发布验证输出。
5. 默认先运行或建议 `/aifi-drift-check`。

## Delegatable SubAgents

- `aifi-release-manager`
- `aifi-security-privacy-reviewer`
- `aifi-qa-e2e-engineer`

## Execution steps

1. 确认发布清单是否已登记为 active 入口。
2. 对照 `BACKLOG.md` 和 `DELIVERY_PLAN.md` 检查 M8 门禁。
3. 汇总测试、安全、E2E 和回滚证据。
4. 标记阻断项、残余风险和复盘输入。
5. 输出是否可发布的判断。

## Forbidden actions

- 不得执行 git push、发布、部署、关闭 issue/PR 或修改共享系统，除非用户明确授权。
- 不得把未登记发布清单当作 active 依据。
- 不得创建新 roadmap、临时计划入口或并行任务体系。
- 不得跳过失败测试或安全风险。

## Output format

- `## 结论`
- `## 证据`
- `## 风险`
- `## 待处理文件`
- `## 下一步动作`

## Acceptance criteria

- 发布判断引用任务、里程碑、测试、安全和发布清单证据。
- 未验证门禁标记为 `UNKNOWN`。
- 阻断项和回滚准备明确。

## Risk markers

- 发布清单未登记。
- 主链路测试缺失。
- 安全风险未处理。
- 回滚方案缺失。

## Recommended read-only commands

```bash
git status --short --ignored
git diff --stat
grep -RIn "M8\|release\|发布\|rollback\|回滚\|AIFI-" docs apps tests 2>/dev/null || true
```

## Write authorization rules

默认只读。发布清单或复盘落库必须进入已登记 active 入口；任务变更进入 `BACKLOG.md`；任何发布或共享系统操作必须单独获得明确授权。
