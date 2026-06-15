---
name: aifi-context-index-gate
description: Use when AiForInterviewer refactors, governance audits, closeout, false-done risk, or context checks need Understand-Anything/CodeGraph.
---

# aifi-context-index-gate

## Purpose

在大型重构、跨模块分析、文档治理审计、closeout / false-done 风险核查前，先用 Understand-Anything 与 CodeGraph 获取压缩上下文、调用关系和影响面证据，减少盲目 `Read` / `Grep` / `Glob` 和过早拆分 read-only subagent。只要需要把文档结论与 runtime / Agent / API / domain / test code evidence 交叉验证，本 Skill 就是前置上下文压缩入口。本 Skill 只负责上下文索引、影响面分析和调用链压缩，不负责业务实现、修复、规划或提交。

## When to use

- 大型重构、跨模块修改、DDD / `PolishUseCases` / Agent 架构任务开始前。
- docs-governance、closeout、false-done risk、release / readiness 审计开始前，只要需要把文档结论和 runtime / Agent / API / domain / test code evidence 交叉验证。
- docs false-done closeout、runtime evidence recon、Agent / `PolishUseCases` / DDD 任务开始前。
- 调用链分析、依赖链分析、影响面分析开始前。
- 需要判断下一批最小源码读取范围时。

## Default order

1. 检查 Understand-Anything 本地索引是否存在，判断是否足以回答全局、domain、diff 或知识图谱问题。
2. 在任何 CodeGraph 查询前强制做 freshness check，优先使用 MCP `codegraph_status`；CLI 场景使用：
   - `command -v codegraph`
   - `codegraph --version`
   - `test -d .codegraph`
   - `codegraph status .`
3. 如果 `.codegraph/` 不存在，不擅自初始化，除非当前任务明确允许本地索引初始化；输出建议命令：`codegraph init -i`。
4. 如果 `codegraph status .` 显示 pending sync、stale 或 no index，优先执行或建议 `codegraph sync .`；如果 sync 失败，报告失败并降级为最小 `Read` / `Grep`。
5. 优先直接查询 CodeGraph MCP / CLI，使用 `codegraph_explore`、`codegraph_search`、`codegraph_callers`、`codegraph_callees`、`codegraph_impact`、`codegraph_node` 做 symbol、caller / callee、call graph、dependency chain 和 precise impact 查询。
6. 只有当 Understand-Anything / CodeGraph 证据不足、过期、不可用或无法覆盖目标路径时，才扩大 `Read` / `Grep` 范围。

## CodeGraph freshness strategy

- 主机制：依赖 CodeGraph MCP auto-sync、watcher 和 connect-time catch-up。
- 前置保证：大型任务前必须用 `codegraph status .` 检查 freshness。
- MCP 前置保证：任何 `codegraph_explore`、`codegraph_search`、`codegraph_callers`、`codegraph_callees`、`codegraph_impact` 或 `codegraph_node` 查询前，先调用 `codegraph_status` 或等价 CLI freshness check。
- 缺 `.codegraph/`：建议 `codegraph init -i`，不在未授权任务中初始化。
- pending / stale / no index：执行或建议 `codegraph sync .`。
- watcher / MCP 不可用：降级为最小化 `Read` / `Grep`，并在输出中说明降级原因。
- 可选 hook 只能作为后续建议，不在本 Skill 或当前补丁中创建。

## CodeGraph throttling

- 默认先用 `codegraph_explore`、`codegraph_search`、caller / callee / impact 查询获取 outline、调用关系和影响面。
- `codegraph_node` 默认 `includeCode=false`。
- 只有 final evidence 需要源码片段，或 outline / call relationship 无法判断关键逻辑时，才对最小 symbol 使用 `includeCode=true`。
- 不用多个 `codegraph_node includeCode=true` 调用替代有界 `Read`；需要源码验证时，先列出最小文件 / symbol 清单。

## Subagent throttling

- 默认不要在 `aifi-context-index-gate` 前启动 read-only subagents。
- 先用 Understand-Anything / CodeGraph 缩小文档、runtime、Agent、API、domain、test 的交叉验证范围，再拆分独立风险给 subagent。
- 只有当风险边界已经独立、输入文件清单已最小化、且并行读取不会扩大事实源时，才启动 read-only subagent。
- subagent 输出不得替代当前 agent 对 final evidence、scope lock 和验证命令的汇总判断。

## Forbidden

- 不允许先盲目 `Read` 20+ 文件。
- 不允许在本 Skill 前用 read-only subagent 扩大探索范围。
- 不允许用 `rg` 结果堆上下文替代 CodeGraph 查询。
- 不允许把图谱结论当最终事实；关键修改仍必须回到源码、契约和测试验证。
- 不允许创建 `post-commit`、`post-merge`、`post-checkout` 或其他 git hook。
- 不创建 roadmap、任务体系、治理文档或长期入口。

## Required output

- `index freshness`: 索引时间、来源和是否需要刷新。
- `codegraph status summary`: CodeGraph 可用性、版本、`.codegraph/` 状态和 sync/freshness 结论。
- `queried scope`: 查询的问题、symbol、模块、diff 或目录范围。
- `graph evidence`: 选中的 Understand-Anything / CodeGraph 证据摘要。
- `affected modules`: 受影响模块和调用链边界。
- `confidence`: 高 / 中 / 低，并说明依据。
- `missing coverage`: 图谱缺口、未覆盖路径或过期风险。
- `next minimal files to read`: 下一步最小源码读取清单。
- `fallback reason`: 图谱工具不可用或证据不足时的降级原因；未降级则写 `None`。
