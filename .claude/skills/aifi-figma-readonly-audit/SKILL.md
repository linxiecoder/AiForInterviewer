---
name: aifi-figma-readonly-audit
description: Run a strict read-only AiForInterviewer Figma audit for explicitly specified files, pages, or node IDs and report UNKNOWN when evidence is unavailable.
---

# aifi-figma-readonly-audit

## Purpose

对用户明确指定的 Figma file、page 或 node_id 执行严格只读审计，输出可追踪证据、缺口和风险。

## Default mode

- 默认 Figma read-only。
- 只检查用户明确指定的 file、page 或 node_id。
- 不写入 Figma，不创建 Figma 对象，不修改仓库文件。
- 不声明拥有 Figma 写权限。
- Figma MCP 不可用、权限不足、输出截断或证据不足时，结论写 `UNKNOWN`。

## Required Scope Lock

```text
task_id: [如适用，必须是 AIFI-*]
files: [相关 active 文档；只读]
figma_nodes: [精确 file_key / page / node_id]
allowed_ops: READ_ONLY
forbidden_ops: [禁止写入 Figma、禁止修改仓库文件、禁止扩大节点范围]
final_artifact: Figma readonly audit evidence report
done_condition: 指定节点证据已读取，或缺口已标记 UNKNOWN
```

## Execution steps

1. 读取 `AGENTS.md`、`docs/00-governance/DOCS_INDEX.md` 和任务相关 active 入口。
2. 建立 Scope Lock，确认 allowed_ops 为 `READ_ONLY`。
3. 先读取目标文件或页面的最小 metadata。
4. 只读取用户指定 node_id 的必要信息。
5. 对大型节点分批读取，避免一次性拉取完整 descendant dump。
6. 每批读取后整理 evidence table。
7. 证据不足、权限受限或上下文截断时停止并标记 `UNKNOWN`。

## Output format

```markdown
## 结论

PASS / WARN / UNKNOWN：...

## Scope checked

- task_id: ...
- files: ...
- figma_nodes: ...
- allowed_ops: READ_ONLY

## 证据

| 检查项 | 证据来源 | 读取范围 | 结论 | 说明 |
|---|---|---|---|---|

## 风险

- ...

## 待处理文件

- 无 / ...

## 下一步动作

- ...
```

## Forbidden actions

- 不写入 Figma 文件、页面、组件、变量或图层。
- 不创建 Figma 对象。
- 不修改仓库文件。
- 不读取无关页面或无关 node。
- 不把未读取、不可读或截断的内容推断为通过。
