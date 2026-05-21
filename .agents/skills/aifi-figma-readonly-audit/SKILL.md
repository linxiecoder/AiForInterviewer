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

## Figma 读取安全规则

- 只允许读取用户明确指定的 fileKey、page 或 node_id；不得扩大到无关 page、无关 node 或完整文件树。
- 禁止创建、移动、删除、重命名或修改 Figma 文件、页面、组件、变量、图层或 prototype 设置。
- 禁止在读取任务中顺手修复 Figma 内容；读取失败不得自动转成设计假设。
- 用户描述、截图描述或历史记录只能标记为 `用户提供但未验证`，不得写成 MCP 已验证事实。
- Frame 清单、数量、名称和层级必须来自已读取节点证据；未读取到时写 `UNKNOWN` 或 `待确认`。

## 定位与精简读取规则

- 定位优先使用 `fileKey + nodeId`；只有用户未提供 node_id 时才读取最小 page 信息辅助定位。
- Figma URL 的 `node-id` 必须转换为 MCP `nodeId`：例如 `2-2` 转为 `2:2`，`114-2` 转为 `114:2`。
- 不优先依赖 Page 名称精确匹配；名称不一致时记录 `名称不匹配`，并继续按明确 node_id 读取。
- 默认禁止完整 Page metadata 读取；Page 只核验存在性、实际名称、type、childCount、可访问状态和最多 12 个直接 children 摘要。
- 默认禁止完整 Figma 树展开和深层递归；节点结构摘要最多 2 层，`childrenSummary` 最多 12 个直接子节点。
- 节点精简字段只包含 nodeId、name、type、可见性、尺寸、直接 children 摘要和必要状态；不得输出完整文本层、完整坐标、完整样式或深层 descendants。
- Page `children` 为空不得判定为 Figma 无内容；应继续按指定 node_id 清单读取，失败时输出待确认项。
- 每个目标节点必须标记 `readStatus`：`已读取`、`未读取`、`读取失败`、`名称不匹配`、`待确认` 或 `用户提供但未验证`。

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
3. 归一化用户提供的 Figma URL、fileKey、page 和 node_id；将 URL `node-id` 连字符形式转换为 MCP `nodeId` 冒号形式。
4. 优先按明确 node_id 清单逐个精简读取；未提供 node_id 时，只读取 Page 最小核验信息和直接 children 摘要。
5. Page 读取只记录存在性、实际名称、type、childCount、可访问状态和最多 12 个直接 children 摘要；禁止完整 Page metadata。
6. Frame / node 读取只记录精简字段和最多 2 层结构摘要；禁止完整 descendant dump、深层递归和完整文本/样式/坐标输出。
7. Page `children` 为空、权限受限、输出截断或节点读取失败时，不得判定为无内容；记录失败原因并标记 `UNKNOWN` 或 `待确认`。
8. 每批读取后整理 evidence table、节点精简矩阵和 readStatus。
9. 证据不足、权限受限或上下文截断时停止并标记 `UNKNOWN`。

## Output format

```markdown
## 结论

PASS / WARN / UNKNOWN：...

## Scope checked

- task_id: ...
- files: ...
- figma_nodes: ...
- allowed_ops: READ_ONLY

## 读取摘要

- fileKey: ...
- page: ...
- normalized_node_ids: ...
- read_strategy: fileKey + nodeId compact-read / Page minimal verification

## Page 核验结果

| fileKey | nodeId | expected_page | actual_name | type | childCount | readStatus | 结论 | 说明 |
|---|---|---|---|---|---:|---|---|---|

## 节点精简矩阵

| nodeId | name | type | size | childCount | readStatus | 结论 | 说明 |
|---|---|---|---|---:|---|---|---|

## 节点结构摘要

| nodeId | depth | childrenSummary | 结论 | 说明 |
|---|---:|---|---|---|

## 失败节点

| nodeId | readStatus | failure_reason | next_step |
|---|---|---|---|

## F2_READ_RESULT

```text
fileKey: ...
pageNodeId: ...
readStatus: 已读取 / 未读取 / 读取失败 / 名称不匹配 / 待确认 / 用户提供但未验证
verifiedFrames: UNKNOWN / [已读取 Frame 摘要]
prototypeEvidence: UNKNOWN / [已读取证据]
pendingConfirmation: ...
```

## 证据

| 检查项 | 证据来源 | 读取范围 | 结论 | 说明 |
|---|---|---|---|---|

## 风险

- ...

## 待确认项

- 无 / ...

## 待处理文件

- 无 / ...

## 下一步动作

- ...
```

## Forbidden actions

- 不写入 Figma 文件、页面、组件、变量或图层。
- 不创建、移动、删除、重命名或修改 Figma 对象。
- 不修改仓库文件。
- 不读取无关页面或无关 node。
- 不读取完整 Page metadata、完整 Figma 树、完整 descendant dump 或深层递归 children。
- 不把未读取、不可读、空 children、权限受限或截断的内容推断为通过。
- 不伪造 Frame 清单、Frame 数量、Frame 名称、Prototype Path 或组件清单。
- 不把用户描述、历史记录或截图描述写成 MCP 已验证事实。
- 不把 F2 Components 当作 F3 视觉规范。
- 不把 Prototype Path 注释自动转换为原生 Figma prototype reactions。
- 不把抽屉、弹窗或状态 Frame 自动升级为一级页面。
- 不把 F2 node name 当作新增产品需求或 F3 计划输入。
