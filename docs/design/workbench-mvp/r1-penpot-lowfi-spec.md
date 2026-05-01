---
title: R1 Penpot 低保真页面规格
type: design
permalink: ai-for-interviewer/docs/design/workbench-mvp/r1-penpot-lowfi-spec
---

# R1 Penpot 低保真页面规格

## 1. 文档定位

本文档用于 R1 acceptance closeout 前的页面设计校准，目标是把现有 R1 需求、设计、前端实现、E2E 断言和用户反馈整理为 Penpot 低保真页面输入。

本文档只定义低保真页面规格、Penpot frame 规划、Penpot MCP 后续执行方式和后续窗口计划。

本文档不修改业务代码，不修改前端代码，不修改测试，不修改数据库，不修改 `docs/governance/**`，不修改 `DOC_STATE.yaml`，不生成 implementation packet，不进入 R1 closeout，不声明任何任务 implementation-ready。

## 2. 输入事实

本规格基于以下现有事实源整理：

| 来源 | 已确认事实 |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | Workbench MVP 目标是文本优先的模拟面试工作台，覆盖岗位、简历、材料、问题、回答、评分、复盘、导出和历史回看闭环。 |
| `docs/design/workbench-mvp/information-architecture.md` | 一级导航包括工作台、模拟面试、岗位、简历、知识库、复盘 / 评分、账号 / 权限；核心路径为历史列表、发起模拟、面试台、评分 / 复盘详情。 |
| `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` | RAG、traceability、评分、复盘、导出和弱项训练需要可追踪引用、可恢复状态和可降级提示。 |
| `docs/design/workbench-mvp/scoring-review-export-dod.md` | 评分必须支持 `0-100` 总分、多维评分、reason、证据、低置信度、建议、弱项和 Markdown 导出。 |
| `docs/development/r1-trusted-trace-ui-compliance.md` | 根路径 `/` 已切到 R1 工作台首页；旧 W10 mock 只保留在 `/legacy-mock` 或 `/mock`；Ant Design 当前是 R1 试点。 |
| `docs/development/local-startup.md` | 当前前端 route 覆盖 `/`、`/interviews`、`/interviews/:sessionId`、`/reviews`、`/jobs`、`/resumes`、`/interviews/new`，E2E 通过 mock API 验证。 |
| `docs/development/database.md` | 前端只展示安全摘要和引用，不展示完整 prompt、raw LLM response、secret、对象存储真实路径或隐藏 resource id。 |
| `apps/web/src/**` | 当前页面已有工作台首页、历史列表、复盘列表、详情页和若干入口页，但布局仍由代码直接推断，未经过 Penpot 低保真校准。 |
| `apps/web/e2e/trusted-trace.spec.ts` | E2E 已覆盖根路径 R1 首页、旧 mock 隔离、历史到详情、复盘入口、可信详情、空 trace、敏感字段不展示。 |

用户反馈已经确认：后续不能继续完全依赖 Codex 基于文字和现有代码自行推断布局，必须引入 Penpot 低保真页面稿作为前端实现依据。

## 3. 全局页面原则

### 3.1 布局优先级

后续前端实现的布局优先级固定为：

1. 已经由用户确认的 Penpot frame。
2. 本文档 low-fi spec。
3. 现有需求和设计文档。
4. 当前前端代码和 E2E 断言。

现有代码只能作为能力事实和字段事实，不能作为最终布局依据。

### 3.2 R1 页面共同结构

所有 R1 页面低保真稿应包含：

- 顶部全局导航，保持工作台、岗位、简历、历史记录、发起面试、复盘的主入口。
- 当前页面标题、阶段状态和关键能力标签。
- 主要内容区，优先展示当前页面最需要完成的任务，而不是大面积说明文案。
- 状态区，统一表达 loading、empty、degraded、failed、retryable、permission-hidden。
- 安全信息边界，明确不展示敏感字段。
- 可进入下一步的主操作，避免只有静态空态。

### 3.3 状态表达

低保真稿必须显式预留以下状态：

| 状态 | 页面表达 |
| --- | --- |
| loading | 骨架或轻量提示，不使用空白屏。 |
| empty | 展示当前没有数据的原因，并提供下一步动作。 |
| degraded | 用中等强度提示说明能力可继续但可信度降低。 |
| failed | 用高强度提示说明失败原因和恢复动作。 |
| retryable | 和 failed / degraded 并列展示是否可重试。 |
| permission-hidden | 明确说明当前身份不可见，不泄露对象是否真实存在。 |

### 3.4 安全展示边界

所有页面禁止展示：

- full prompt。
- raw LLM response。
- secret、token、password、provider key。
- 完整数据库连接串。
- object storage path。
- hidden resource id。
- embedding vector。
- provider 原始载荷。

页面可以展示安全摘要、状态、分数、reason、citation ref、evidence gap label、snapshot ref、content version 和用户可理解的失败原因。

## 4. 页面清单

| 页面 | Route | Penpot frame | R1 目标 |
| --- | --- | --- | --- |
| 工作台首页 | `/` | `R1 Workbench Home` | 成为 R1 默认首页，汇总主链路入口、最近记录和可信能力。 |
| 历史列表页 | `/interviews` | `R1 Interview History` | 展示模拟记录、评分摘要、复盘状态、export 状态，并进入详情。 |
| 评分 / 复盘详情页 | `/interviews/:sessionId` | `R1 Trusted Review Detail` | 展示可信评分、复盘、RAG citation、evidence gap、trace refs 和 export 状态。 |
| 发起模拟面试页 | `/interviews/new` | `R1 Start Interview` | 选择岗位、简历、知识库 / RAG 后发起文本模拟。 |
| 岗位管理页 | `/jobs` | `R1 Jobs` | 展示岗位列表、最近使用和新建入口。 |
| 简历管理页 | `/resumes` | `R1 Resumes` | 展示简历列表、上传 / 新建入口、解析状态和失败态。 |
| 复盘列表页 | `/reviews` | `R1 Reviews` | 汇总最近复盘、分数、状态、evidence gap 和详情入口。 |
| 空态集合 | 多页面适用 | `R1 Empty States` | 统一历史、岗位、简历、复盘、旧 trace、旧 score 的空态。 |
| 降级集合 | 多页面适用 | `R1 Degraded States` | 统一 RAG degraded、LLM unavailable、export failed、permission hidden 等状态。 |

旧 W10 mock 不允许作为主界面；只能保留在 `/legacy-mock` 或 `/mock`。

## 5. 页面规格

### 5.1 工作台首页

页面目标：根路径 `/` 的 R1 默认首页，帮助用户从一个清晰的工作台进入发起模拟、历史记录、岗位、简历、复盘和可信详情。

必须包含：

| 区块 | 低保真要求 |
| --- | --- |
| 顶部区域 | 显示产品名、R1 当前定位、owner / identity 摘要、R1 状态标签。 |
| 主导航 | 展示工作台、岗位、简历、历史记录、发起面试、复盘；当前页高亮。 |
| R1 状态区 | 展示 `PostgreSQL`、`RAG citation`、`traceability`、`0-100 scoring`、`E2E protected`，并预留 degraded / failed 标签位。 |
| 主操作入口 | 首要操作是“发起模拟面试”；次要操作是历史记录、岗位管理、简历管理、复盘。所有入口必须是真实 route，不允许 `#anchor` 假入口。 |
| 最近模拟记录 | 展示 session、更新时间、状态、trace count、score、review、export、evidence gap 摘要和“查看可信详情”。 |
| 可信能力摘要 | 汇总 trace summary、RAG citation、evidence gap、0-100 score report、review evidence chain、Markdown export。 |
| 岗位 / 简历 / 知识库入口 | 首页应显示三个准备对象的可用性摘要，并提供进入对应管理页或发起页的动作。 |
| 历史 / 复盘入口 | 首页应可进入 `/interviews` 和 `/reviews`，并能从最近记录直接进 `/interviews/:sessionId`。 |
| degraded / failed / empty | 首页必须展示最近记录读取失败、没有历史记录、旧记录无 trace、RAG degraded / evidence missing、export failed / retryable 的低保真状态。 |
| 旧 mock 隔离 | 首页不得出现 `W10 首切片 / apps/web mock 原型`、`Mock LLM`、`单次会话临时数据` 等旧 mock 主界面文案。 |

Codex 实现注意事项：

- 后续实现不得仅照抄当前 Ant Design card 堆叠；布局以 Penpot 首页 frame 为准。
- 首页可以保留 Ant Design 作为组件基础，但信息架构和视觉密度以 Penpot frame 为准。
- 首页只能展示安全摘要，不展示 prompt、raw response、secret 或私有存储路径。

### 5.2 历史列表页

页面目标：`/interviews` 成为模拟记录列表页，支持用户扫描历史记录并进入可信详情。

必须包含：

| 区块 | 低保真要求 |
| --- | --- |
| 列表字段 | session / title、状态、mode、turn、updated_at、score、review、export、trace count、evidence gap。 |
| 状态标签 | `feedback_ready`、`archived`、`available`、`empty`、`degraded`、`failed`、`retryable` 等状态有固定标签位。 |
| 评分摘要 | 展示 `score: 82` 或 `score: empty`；不得把无评分误显示为 0 分。 |
| 复盘状态 | 展示 `review: generated/degraded/failed/empty`。 |
| export 状态 | 展示 `export: generated/failed/empty`、失败原因、是否可重试、`content_version`、`snapshot_ref`。 |
| 点击进入详情 | 每条记录必须有“查看可信详情”入口，进入 `/interviews/:sessionId` 并保留 `owner_id`。 |
| 空态 | 没有历史记录时，提示用户从发起模拟面试开始，并提供发起入口。 |
| 加载失败态 | API 失败时展示错误摘要和重试 / 返回工作台动作。 |
| 权限不可见态 | 当当前身份无权查看历史时，展示“当前身份暂无可见记录”，不泄露隐藏 session id。 |

Codex 实现注意事项：

- 历史列表不得展示 `unsafe_debug`、prompt、raw LLM response、object storage path 或 hidden resource id。
- 后续若引入筛选 / 分页，不能改变 `/interviews` 作为历史列表的主定位。

### 5.3 评分 / 复盘详情页

页面目标：`/interviews/:sessionId` 展示一场模拟面试的可信评分、复盘、证据链和导出状态。

必须包含：

| 区块 | 低保真要求 |
| --- | --- |
| 总分 | 显示 `0-100` 总分、score status、低置信度提示；无分数时显示旧记录空态。 |
| 多维评分 | 每个维度显示 label、score、reason、citation ref、evidence gap、low confidence。 |
| 每个维度 reason | reason 必须和分数并列展示，不允许隐藏到 tooltip 中作为唯一入口。 |
| RAG citation | 展示 source summary、chunk summary、chunk index、position、citation ref。 |
| evidence gap | 展示 no_result、permission_filtered、index_pending、index_failed、rag_unavailable 等 label。 |
| trace refs | 展示 session、turn、answer、score、review、export refs 和 trace counts。 |
| review summary | 展示整体复盘摘要，不与维度 reason 混合。 |
| suggestions | 展示可执行建议列表。 |
| weak areas | 展示薄弱项列表，并预留后续训练入口。 |
| export status | 展示 Export status、failure reason、retryable、content version、snapshot ref。 |
| degraded / failed / retryable | 使用单独状态带汇总，避免散落在页面角落。 |
| 旧记录无 trace / 无 score | 旧记录应显示“暂无 trace_summary”“暂无评分维度”“旧记录暂无评分复盘”等稳定空态。 |
| 敏感字段禁止展示 | 禁止展示 full prompt、raw LLM response、secret、object storage path、hidden resource id。 |

Codex 实现注意事项：

- 详情页应该采用“评分复盘摘要 -> trace / RAG -> export / request refs”的阅读顺序，具体列数和区域位置以 Penpot frame 为准。
- request refs 只能展示安全 label，不展示 provider 原始请求体。
- evidence gap 和 degraded 不是错误噪声，应作为可信度信息长期可见。

### 5.4 发起模拟面试页

页面目标：`/interviews/new` 从入口页升级为可被 Penpot 设计约束的启动页。

必须包含：

| 区块 | 低保真要求 |
| --- | --- |
| 岗位选择 | 显示最近岗位、岗位状态、必填标记和去新建岗位入口。 |
| 简历选择 | 显示最近简历、解析状态、必填标记和去上传 / 新建简历入口。 |
| 知识库 / RAG 选择 | 显示可用知识库、索引状态、是否启用 RAG、无资料提示。 |
| 开始按钮 | 在岗位和简历满足最小输入前 disabled，并说明缺失项。 |
| 缺失输入提示 | 对岗位缺失、简历缺失、知识库为空分别显示局部提示。 |
| RAG degraded 预警 | 当索引 pending / failed 或检索不可用时，提示“面试可继续，但复盘会标注 evidence gap”。 |
| LLM unavailable 预警 | 当 LLM 不可用时，提示无法生成真实问题，并阻止进入真实模拟主链。 |

Codex 实现注意事项：

- 该页后续实现必须先有正式任务授权；本文档不授权新增面试创建 API。
- 低保真稿应预留“下一步进入面试台”的位置，但不要假装当前代码已经具备完整面试台。

### 5.5 岗位管理页

页面目标：`/jobs` 展示岗位准备对象，支撑后续从岗位发起模拟。

必须包含：

| 区块 | 低保真要求 |
| --- | --- |
| 岗位列表 | 显示岗位名称、目标方向、最近更新、使用次数、可见状态。 |
| 新建岗位入口 | 明确主按钮“新建岗位”，并预留后续创建表单入口。 |
| 最近使用 | 首页和发起页应能引用最近岗位；岗位页展示最近使用排序。 |
| 空态 | 无岗位时提示先新建岗位或返回发起页，并说明岗位是发起模拟的必填输入。 |
| 权限不可见态 | 无可见岗位时展示权限提示，不泄露隐藏岗位名称。 |

Codex 实现注意事项：

- 当前 `/jobs` 仍是静态空态入口；Penpot 低保真稿应定义未来列表形态，但不宣称后端已经完成。
- 岗位页不得成为复杂管理后台；R1 只服务模拟面试主链路。

### 5.6 简历管理页

页面目标：`/resumes` 展示简历材料准备对象，支撑后续发起模拟和评分证据。

必须包含：

| 区块 | 低保真要求 |
| --- | --- |
| 简历列表 | 显示简历名称、更新时间、解析状态、最近使用、关联岗位数量。 |
| 上传 / 新建入口 | 提供上传文件和新建文本简历两个入口；低保真稿可用占位控件表达。 |
| 解析状态 | 展示 pending、parsed、failed、degraded；解析成功后显示可引用摘要。 |
| 解析失败态 | 显示失败原因和重试 / 手动录入动作。 |
| 最近使用 | 显示发起模拟最近选中的简历。 |

Codex 实现注意事项：

- 简历页不得展示原始对象存储路径。
- 如果后续上传能力未授权，前端只能展示入口和空态，不能伪造上传完成。

### 5.7 复盘列表页

页面目标：`/reviews` 汇总最近复盘，帮助用户从评分结果回到可信详情和后续训练建议。

必须包含：

| 区块 | 低保真要求 |
| --- | --- |
| 最近复盘列表 | 复用或映射历史记录，展示最近复盘条目。 |
| 分数 | 显示 `score: 82` 或 `score: empty`。 |
| 状态 | 显示 review、trace、export、retryable 状态。 |
| evidence gap 标记 | 复盘列表必须能看到该复盘是否存在 evidence gap。 |
| 进入详情入口 | 每条记录有“查看复盘详情”，进入 `/interviews/:sessionId`。 |
| 空态 | 没有复盘时提示先完成一次模拟或从历史记录查看旧结果。 |

Codex 实现注意事项：

- `/reviews` 可以复用 history contract，但 UI 语义必须是“复盘列表”，不是历史列表复制品。
- 后续如果新增独立 review API，需要同步更新 E2E，不得破坏 `/interviews/:sessionId` 详情入口。

## 6. Penpot frame 规划

### 6.1 `R1 Workbench Home`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 定义 R1 默认首页布局，替代 Codex 仅凭当前代码推断首页。 |
| 页面区块 | 顶部导航、R1 状态带、主操作区、最近模拟记录、可信能力摘要、岗位 / 简历 / 知识库概览、风险状态区。 |
| 关键文案 | `AI 模拟面试工作台`、`R1 可信工作台闭环`、`发起模拟面试`、`查看可信详情`、`旧记录无 trace`、`RAG degraded / evidence missing`。 |
| 主要组件 | 顶部导航、状态标签、主操作按钮组、记录列表、能力摘要卡、对象概览、Alert 状态块。 |
| 用户动作 | 发起模拟、进入历史、进入岗位、进入简历、进入复盘、从最近记录进详情。 |
| 状态变化 | loading 最近记录、empty 最近记录、history failed、degraded / failed / retryable 标签显示。 |
| Codex 实现注意事项 | `/` 必须匹配此 frame；旧 mock 不得出现在首页；不得显示敏感字段。 |

### 6.2 `R1 Interview History`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 定义历史列表的扫描结构和记录字段。 |
| 页面区块 | 顶部导航、列表标题、筛选占位、记录列表、失败 / 空态区域。 |
| 关键文案 | `历史记录`、`模拟面试历史列表`、`查看可信详情`、`score`、`review`、`export`、`trace_summary`。 |
| 主要组件 | 列表行、状态标签、评分摘要、export 摘要、详情链接、空态、错误提示。 |
| 用户动作 | 点击详情、返回工作台、发起新模拟、重试读取。 |
| 状态变化 | empty、failed、permission-hidden、export retryable。 |
| Codex 实现注意事项 | 每行需要保留足够字段密度；不要把 export failure 藏到二级页面。 |

### 6.3 `R1 Trusted Review Detail`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 定义可信评分 / 复盘详情的信息优先级。 |
| 页面区块 | 总分摘要、多维评分、review summary、suggestions、weak areas、trace refs、RAG citation、evidence gap、export status、request refs。 |
| 关键文案 | `评分 / 复盘详情`、`可信复盘工作区`、`总分`、`评分维度`、`RAG citation 详情`、`Evidence gap`、`Export status`。 |
| 主要组件 | 分数条、维度列表、reason 文本、citation 列表、trace ref 列表、状态 Alert、export 元数据。 |
| 用户动作 | 查看 citation、查看 evidence gap、复制 / 下载导出入口占位、返回历史。 |
| 状态变化 | score empty、trace empty、citation empty、degraded、failed、retryable、low confidence。 |
| Codex 实现注意事项 | 敏感字段硬隔离；reason 必须可见；旧记录空态必须稳定。 |

### 6.4 `R1 Start Interview`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 定义发起模拟前的选择和风险提示。 |
| 页面区块 | 岗位选择、简历选择、知识库 / RAG 选择、模式占位、缺失输入提示、开始按钮、风险提示。 |
| 关键文案 | `发起模拟面试`、`选择岗位`、`选择简历`、`知识库 / RAG`、`开始模拟`、`缺失输入`、`LLM unavailable`。 |
| 主要组件 | 选择卡、下拉占位、状态标签、禁用按钮、局部错误提示、预警 Alert。 |
| 用户动作 | 选择岗位、选择简历、启用 / 关闭 RAG、进入新建岗位 / 简历、开始模拟。 |
| 状态变化 | job missing、resume missing、RAG degraded、LLM unavailable、ready。 |
| Codex 实现注意事项 | 当前文档不授权 API；实现前必须另开 formal implementation 窗口。 |

### 6.5 `R1 Jobs`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 定义岗位管理入口的列表形态和空态。 |
| 页面区块 | 顶部导航、岗位列表、最近使用、新建入口、权限提示。 |
| 关键文案 | `岗位管理`、`新建岗位`、`最近使用`、`暂无岗位列表`、`当前身份暂无可见岗位`。 |
| 主要组件 | 列表、状态标签、主按钮、空态、权限不可见提示。 |
| 用户动作 | 新建岗位、选择最近岗位、从岗位发起模拟。 |
| 状态变化 | empty、permission-hidden、loading、failed。 |
| Codex 实现注意事项 | R1 不做复杂后台；岗位服务于发起模拟主链路。 |

### 6.6 `R1 Resumes`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 定义简历材料入口和解析状态表达。 |
| 页面区块 | 简历列表、上传 / 新建入口、解析状态、最近使用、失败恢复。 |
| 关键文案 | `简历管理`、`上传简历`、`新建文本简历`、`解析中`、`解析失败`、`最近使用`。 |
| 主要组件 | 列表、上传入口占位、状态标签、解析失败 Alert、空态。 |
| 用户动作 | 上传、手动新建、重试解析、选择用于模拟。 |
| 状态变化 | empty、parsing、parsed、failed、degraded、permission-hidden。 |
| Codex 实现注意事项 | 不展示对象存储真实路径；未授权上传时只能保留入口和空态。 |

### 6.7 `R1 Reviews`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 定义最近复盘列表和详情入口。 |
| 页面区块 | 最近复盘列表、评分摘要、review 状态、evidence gap、export 状态、详情入口、空态。 |
| 关键文案 | `复盘`、`最近复盘入口`、`查看复盘详情`、`score`、`review`、`evidence gap`。 |
| 主要组件 | 列表行、分数标签、状态标签、详情链接、空态。 |
| 用户动作 | 进入详情、返回历史、发起新模拟。 |
| 状态变化 | empty、degraded、failed、retryable、permission-hidden。 |
| Codex 实现注意事项 | `/reviews` 的页面语义必须是复盘列表，不能只是历史列表换标题。 |

### 6.8 `R1 Empty States`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 统一 R1 页面空态，不让空页面变成无反馈白屏。 |
| 页面区块 | 无历史、无复盘、无岗位、无简历、旧记录无 trace、旧记录无 score、无 citation。 |
| 关键文案 | `没有历史模拟记录`、`暂无复盘记录`、`暂无岗位列表`、`暂无简历材料`、`旧记录暂无 trace_summary`、`旧记录暂无评分复盘`。 |
| 主要组件 | Empty、主动作按钮、次动作链接、原因说明。 |
| 用户动作 | 发起模拟、新建岗位、上传 / 新建简历、返回工作台。 |
| 状态变化 | 数据为空、旧记录缺字段、权限不可见。 |
| Codex 实现注意事项 | 空态要给下一步动作；权限不可见不能泄露隐藏资源。 |

### 6.9 `R1 Degraded States`

| 项 | 内容 |
| --- | --- |
| frame 目标 | 统一降级、失败、可重试和不可用状态的视觉表达。 |
| 页面区块 | RAG degraded、evidence gap、export failed、LLM unavailable、history failed、permission hidden。 |
| 关键文案 | `RAG degraded`、`Evidence gap`、`Degraded / failed / retryable`、`LLM unavailable`、`读取失败`、`当前身份暂无可见记录`。 |
| 主要组件 | Alert、状态标签、重试按钮、详情链接、恢复建议。 |
| 用户动作 | 重试、继续但标记 degraded、返回工作台、补充资料。 |
| 状态变化 | failed -> retryable、degraded -> continued、permission-hidden、LLM unavailable。 |
| Codex 实现注意事项 | 降级态不能被隐藏；RAG 失败时面试可继续但复盘必须标注 evidence gap；LLM unavailable 时不能进入真实生成问题链路。 |

## 7. Penpot MCP 后续工作流

后续使用 Penpot MCP 时必须按以下流程执行：

1. 用户先在 Penpot 中打开目标设计文件，并通过 Penpot MCP Plugin 连接当前项目。
2. Codex 使用 Penpot MCP 读取当前 focused page / current page，确认 page 名称、已有 frame 和 selection。
3. Codex 根据本文档整理将创建的 frame、尺寸、区块、组件层级、命名规则和状态覆盖计划。
4. 创建任何 Penpot frame 前，Codex 必须先输出计划并等待用户确认。
5. 用户确认后，Codex 通过 Penpot MCP 创建低保真 frame；创建时优先使用 board、text、rectangle、group、flex / grid layout 等基础形状，不做高保真视觉。
6. Codex 创建后应读取 frame structure，并在必要时导出 frame 预览用于检查。
7. 用户在 Penpot 中手工调整 frame，包括布局、区块顺序、信息密度和文案。
8. 用户明确确认 frame 后，Codex 再通过 Penpot MCP 读取设计稿结构、导出预览，并把 Penpot frame 作为最高优先级布局依据。
9. Codex 按用户确认的 Penpot frame 修复前端页面。
10. Playwright 增加 screenshot baseline，覆盖首页、历史、详情、空态、degraded 和旧 mock 隔离。
11. E2E 必须继续覆盖根路径、历史列表、详情页、复盘列表、空态、degraded / failed / retryable、敏感字段不展示和旧 mock 隔离。
12. 未经用户确认，Codex 不允许自行改变 Penpot 信息架构、删除用户手工调整、合并 frame 或新增不在本文档范围内的页面。

Penpot MCP 执行注意事项：

- 读取结构时优先使用 `penpotUtils.getPages()`、`penpot.root`、`penpot.selection` 和 `penpotUtils.shapeStructure()`。
- 创建 frame 时按视觉顺序 append child；如果 board 使用 flex / grid layout，优先修改 layout gap / padding，不手动硬改子元素坐标。
- 创建文字元素时避免重复写 shape 名称；Penpot 图层名和画布文字职责应分开。
- 输出给用户的计划必须列出 frame 名称、页面区块、主要状态和不会修改代码的保证。
- 后续从 Penpot 到代码时，缺失的样式值不能由 Codex 自行发挥，应先标注缺失并向用户确认。

## 8. 后续页面实现验收原则

后续页面实现必须遵守：

- Penpot frame 是最高优先级布局依据。
- 现有文字描述只作为辅助。
- 不能只凭现有代码推断布局。
- 根路径 `/` 必须符合 Penpot 首页。
- `/interviews` 必须符合 Penpot 历史列表。
- `/interviews/:sessionId` 必须符合 Penpot 评分复盘详情。
- 旧 mock 只能在 `/legacy-mock` 或 `/mock`。
- 不展示 full prompt、raw LLM response、secret、object storage path、hidden resource id。
- 页面能力必须有 Playwright E2E。
- 关键页面必须有 screenshot baseline。
- R1 未被用户确认 closeout 前，不得把本设计规格解释为 R1 acceptance closeout 已完成。

## 9. 后续窗口规划

| Window ID | 目标 | 修改范围 |
| --- | --- | --- |
| `R1-UX-02-PENPOT-LOWFI-GENERATION` | Codex 使用 Penpot MCP 生成本文档定义的低保真 frame。 | 只改 Penpot，不改代码。 |
| `USER-PENPOT-REVIEW` | 用户在 Penpot 中手工调整 frame，并确认最终低保真稿。 | Penpot 手工调整。 |
| `R1-FE-03-PENPOT-DESIGN-IMPLEMENTATION` | Codex 读取用户确认的 Penpot frame 并修复前端页面。 | 以后续窗口卡授权为准。 |
| `R1-FE-04-VISUAL-E2E-CLOSEOUT` | 增加 Playwright screenshot baseline 和 E2E 收口。 | 以后续窗口卡授权为准。 |
| `R1-CLOSEOUT-02` | 在视觉和 E2E 收口后执行 R1 acceptance closeout。 | 以后续 closeout 窗口授权为准。 |

## 10. 下一窗口卡：`R1-UX-02-PENPOT-LOWFI-GENERATION`

| 字段 | 内容 |
| --- | --- |
| Window ID | `R1-UX-02-PENPOT-LOWFI-GENERATION` |
| Iteration | R1 |
| Task Mode | UX specification / Penpot generation / no code |
| Goal | 使用 Penpot MCP 在当前 focused page 创建 R1 低保真 frame。 |
| Existing Source | `docs/design/workbench-mvp/r1-penpot-lowfi-spec.md` |
| Allowed Paths | Penpot 当前连接文件；本地仓库无写入。 |
| Forbidden Paths | `apps/**`、`tests/**`、`docs/governance/**`、`DOC_STATE.yaml`、packet、数据库、`.env`、package 依赖。 |
| Input Docs | `docs/design/workbench-mvp/r1-penpot-lowfi-spec.md`、`docs/development/r1-trusted-trace-ui-compliance.md`、当前 Penpot focused page。 |
| DoD | 9 个指定 frame 已创建或已明确说明无法创建的阻断；frame 名称、区块、关键文案、状态集合与本文档一致。 |
| Validation | Penpot MCP 读取当前 page structure；必要时导出 frame 预览；本地执行 `git status --short` 确认仓库未变。 |
| Change Budget | 本地文件 0；Penpot frame 9 个。 |
| Stop Conditions | Penpot MCP 未连接；focused page 不明确；用户未确认创建计划；现有 Penpot 信息架构与本文档冲突且用户未决策。 |
| Writeback Target | none |

目标偏离：否。当前动作服务于 R1 的页面实现前设计校准，不进入业务代码实现或 R1 closeout。

推进缓慢风险：否。本文档解除“后续页面只能靠文字和现有代码推断布局”的设计输入阻断，下一步直接进入 Penpot 低保真生成窗口。
