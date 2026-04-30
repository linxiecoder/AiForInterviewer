---
title: ST13_10_DESIGN
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-10/st13-10-design
---

# ST13_10 设计：R1 RAG 最小可用任务包设计

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务设计文档；用于冻结 R1 RAG 最小可用范围和后续实现输入。
- 任务锚点：`ST13_10` 是 R1 RAG / 知识库 anchor。
- 当前 official state：`DOC_STATE.yaml` 中 `ST13_10` 仍为 `implementation_doc_state=missing`、`readiness=blocked`；本窗口不修改 official state。
- 当前窗口性质：docs-only readiness；不生成 packet，不打开 formal window，不授权 RAG implementation。
- 新 task ID：不新增；R1 RAG 继续沿用 `ST13_10`。

## 2. 关联 ST13 / WT13

- ST13：`ST13_10`
- WT13 alias：`WT13-10`
- 任务名称：RAG / 知识库
- 主模块：M05
- 横向依赖：M01、M02、M03、M04、M06、M08、M10
- 上游稳定输入：
  - `ST13_21` R1 API contract freeze
  - `ST13_20` R1 data / schema / migration readiness
  - `docs/requirements/workbench-mvp/**`
  - `docs/design/workbench-mvp/**`

## 3. R1 RAG 最小范围

R1 RAG 最小可用目标是让岗位、简历、用户资料、公共知识材料和历史回答能够作为可引用上下文进入模拟面试、评分、复盘、导出和历史回看。

R1 minimum 不追求高级检索质量平台，而是冻结以下最小闭环：

| 范围 | R1 最小含义 | 不代表 |
| --- | --- | --- |
| knowledge source | 用户私有资料、管理员公共知识库、岗位 / 简历 / 历史回答可作为上下文来源 | 不实现团队共享知识库或复杂组织治理 |
| document lifecycle | 文档上传 / 粘贴、解析状态、切块状态、索引状态和失败原因可追踪 | 不冻结具体解析器、对象存储或向量库 |
| retrieval query | 保存 query 脱敏摘要、scope、selected materials、topK 和触发场景 | 不保存完整敏感 prompt 或 provider secret |
| retrieval result | 返回命中摘要、命中数量、过滤结果、无命中原因和降级状态 | 不承诺复杂 ranking / reranking |
| citation | 表达 source document、chunk、位置、片段摘要和可见性快照 | 不泄露不可见资源或完整私有文档原文 |
| evidence item | 表达证据摘要、使用场景、confidence label 和低置信度说明 | 不让 RAG evidence 直接决定评分 |
| evidence gap | RAG 无结果、索引未完成、索引失败或权限过滤为空时显式说明 | 不静默隐藏缺口 |
| degraded / fallback | RAG 不可用时主链路继续，评分 / 复盘 / 导出显示降级原因 | 不实现完整重试平台 |

## 4. 知识来源边界

R1 knowledge source 至少包含：

- 用户私有文档：简历补充材料、项目材料、面试准备资料。
- 管理员公共知识库：低干扰公共材料入口，只覆盖最小可见和引用边界。
- 岗位与简历：作为 RAG scope 的结构化业务输入。
- 历史回答：可作为当前模拟的上下文来源候选，但必须遵循 owner / visibility。

R1 不包含：

- 团队共享知识库治理。
- 多租户复杂可见性策略。
- 完整知识库运营后台。
- 外部搜索爬取系统。
- 大规模文档治理平台。

## 5. 文档与来源快照边界

R1 document / source snapshot 需要表达：

- `knowledge_document_ref`：文档稳定引用。
- `source_type`：用户私有、管理员公共、岗位、简历、历史回答等来源类型。
- `source_version`：引用时的版本或快照候选。
- `parse_status`：uploaded、parsing、parsed、failed 等等价语义。
- `index_status`：pending、running、indexed、failed 等等价语义。
- `failure_reason`：可展示、脱敏、可审计的失败原因。
- `visibility_snapshot`：引用时的权限和可见性摘要。

source snapshot 用于复盘、评分、导出和历史回看重现，不代表当前已经创建 schema、migration 或对象存储实现。

## 6. 检索查询边界

R1 retrieval query contract 至少需要：

| 字段族 | R1 语义 |
| --- | --- |
| trigger | 发起模拟、追问、评分、复盘、导出或历史回看 |
| query summary | query 脱敏摘要；不保存完整敏感 prompt |
| scope | job、resume、selected materials、private knowledge、public knowledge、history answers |
| topK | 检索数量候选，进入数据 readiness 和测试边界 |
| filters | owner、visibility、workspace / tenant 候选、document status |
| operation trace | request_id、operation_id、status、failure reason、retryable |

retrieval query 可以被 `ST13_20` 持久化为 summary / metadata / source refs，不得在 R1 默认落完整 prompt、embedding 向量或 provider secret。

## 7. 检索结果边界

R1 retrieval result contract 至少需要：

- 命中数量。
- 命中摘要。
- 命中文档和 chunk 引用。
- 权限过滤结果摘要。
- 无命中原因。
- `degraded` 标记。
- `retryable` 标记。
- `evidence_gap` 候选。

retrieval result 必须能被面试台、评分、复盘、导出和历史回看消费，但不冻结排序算法、embedding provider、向量数据库或 reranking 策略。

## 8. 引用契约

R1 citation contract 需要表达：

| 字段族 | R1 语义 |
| --- | --- |
| source ref | source document、job、resume、history answer 或 public material 引用 |
| chunk ref | chunk id / chunk ordinal / source position 候选 |
| snippet summary | 可展示片段摘要，不默认复制完整私有原文 |
| source label | 用户可理解的来源名称和来源类型 |
| visibility snapshot | 引用时的权限摘要，防止导出或复盘泄露不可见资源 |
| used by | question、answer、score、review、export 或 history detail |

citation 是可解释引用，不是评分唯一依据，也不是完整知识库治理实现。

## 9. 证据项契约

R1 evidence item contract 需要表达：

- evidence summary。
- related question / answer / score dimension / review item。
- citation refs。
- confidence label。
- low confidence reason。
- source snapshot ref。
- degraded / fallback reason。

Evidence item 可以进入评分理由、复盘证据、导出内容和历史回看，但必须遵守资源可见性与脱敏边界。

## 10. 证据缺口契约

R1 必须显式表达 evidence gap：

| 场景 | R1 语义 |
| --- | --- |
| no result | 检索完成但无命中，面试可继续 |
| index pending | 材料尚未完成索引，提示等待或继续无证据路径 |
| index failed | 索引失败，显示脱敏失败原因和 retryable |
| permission filtered empty | 权限过滤后为空，不泄露不可见资源 |
| RAG unavailable | RAG 服务不可用，主链路降级继续 |
| low confidence | 检索或证据不足，评分 / 复盘显示低置信度 |

evidence gap 不得被前端静默隐藏，也不得让用户误以为有证据支持。

## 11. RAG 不可用 / 空结果 / 降级 / 回退语义

R1 fallback 规则：

- RAG unavailable：返回 degraded 状态和安全失败原因；主链路可继续。
- Empty result：返回 evidence gap；不得当作系统错误。
- Index pending：返回 pending / running 等状态；前端展示等待或继续路径。
- Index failed：保留失败记录、failure reason 和 retryable 候选。
- Permission denied / resource not visible：按 `ST13_21` error contract 与 `ST13_20` visibility boundary 处理。
- LLM 仍可基于岗位、简历、当前回答和历史上下文继续，但复盘 / 评分必须标注证据缺口。

## 12. 安全与可见性边界

R1 RAG 必须遵守：

- 用户私有资料默认只对 owner 可见。
- 管理员公共知识库只开放最小读取和引用语义。
- citation / evidence / export 必须继承源资源 visibility。
- `resource_not_visible` 不得泄露资源真实存在性。
- 前端只展示安全摘要，不展示不可见资源 id。
- 不保存 provider secret、真实 token、真实数据库连接、对象存储真实路径。
- 不把完整私有文档原文复制到 citation / evidence 表。

## 13. 前端展示契约

R1 前端可消费的 RAG display contract：

| UI surface | R1 展示语义 |
| --- | --- |
| 面试台 | 展示当前问题可用 citation、参考材料摘要、evidence gap 和 RAG degraded |
| 发起模拟 | 展示可选资料、索引状态、缺失资料和权限过滤后的空状态 |
| 知识库 | 展示上传、解析、索引、失败原因和 retryable |
| 评分详情 | 展示维度评分关联的 evidence、低置信度和证据缺口 |
| 复盘详情 | 展示整场证据、关键缺口、建议来源和 RAG 降级说明 |
| Markdown 导出 | 包含 RAG 引用、证据缺口和低置信度提示 |
| 历史回看 | 恢复当时 source snapshot、citation 和 evidence gap 摘要 |

本任务不设计具体 UI 组件，不修改 `apps/**`，不创建前端页面。

## 14. 持久化边界

R1 persistence boundary 必须与 `ST13_20` 对齐：

- `RetrievalQuery`：query summary、scope、topK、trigger、status、request_id / operation_id。
- `RetrievalResult`：hit count、hit summary、empty reason、permission filtered summary、degraded、retryable。
- `Citation`：source ref、chunk ref、source position、snippet summary、visibility snapshot。
- `Evidence`：evidence summary、used_by、confidence label、evidence_gap、low_confidence_reason。
- `SourceSnapshot`：source version、index status、parse status、visibility snapshot。

R1 不把完整 prompt、完整 LLM response、embedding 向量、provider secret、对象存储真实路径作为必落库字段。

## 15. 对 ST13_21 API 契约的依赖

`ST13_10` 必须消费 `ST13_21` 已冻结的 R1 API contract：

- Knowledge / RAG action boundary。
- Request contract：query、scope、topK、selected materials、actor context。
- Response contract：citations、evidence_items、evidence_gap、confidence、degraded。
- Error envelope：rag_unavailable、resource_not_visible、validation_failed、retryable、request_id。
- Async / degradation：index pending、index failed、RAG no result、RAG unavailable。
- Frontend UI consumption：citation、evidence gap、pending、failed、degraded、empty state。

`ST13_10` 不反向创建 endpoint、OpenAPI、router、mock server 或 API implementation。

## 16. 对 ST13_20 数据 readiness 的依赖

`ST13_10` 必须消费 `ST13_20` 已冻结的 R1 data readiness：

- RetrievalQuery / RetrievalResult / Citation / Evidence / SourceSnapshot 的候选保存边界。
- request_id、operation_id、audit event、source snapshot、schema version、content version。
- resource identity、resource reference、visibility snapshot、permission snapshot。
- score / review / export / history 对 evidence refs 的消费方式。
- R1 candidate / non-persisted 字段边界。

`ST13_10` 不创建 schema、migration、ORM、repository 或 database implementation。

## 17. R1 必做 / 可选 / R2 延后的 RAG 范围

| 层级 | RAG scope |
| --- | --- |
| R1 must-have | 文档来源边界、最小 document / chunk / index status contract、retrieval query summary、retrieval result summary、citation contract、evidence item / evidence gap、RAG unavailable / empty result / degraded、权限过滤、面试台 / 评分 / 复盘 / 导出消费、与 `ST13_20` persistence boundary 对齐、与 `ST13_24` acceptance / test boundary 对齐 |
| R1 optional | 轻量知识库状态摘要、简单检索配置候选、confidence label 细分、retry 提示增强、管理员公共知识库最小维护说明 |
| R2 deferred | 高级检索质量平台、复杂 ranking / reranking、团队共享知识库治理、多租户复杂可见性策略、完整 embedding provider / vector store tuning、大规模文档治理后台、训练闭环自动消费 RAG evidence、资产归档增强 |

## 18. 完成定义

本 task package readiness 的完成定义：

- `ST13_10` 明确为 R1 RAG anchor。
- 不新增 task ID。
- R1 RAG minimum scope 已冻结。
- `ST13_21` / `ST13_20` dependency 已明确。
- R1 must-have / optional / R2-deferred scope 已区分。
- RAG display、persistence、security、fallback、citation、evidence gap 边界已明确。
- 当前仍不允许进入 RAG implementation。
- 当前仍不允许进入 schema / migration / ORM implementation。
- 未修改代码、测试、governance state、packet 或 formal window。