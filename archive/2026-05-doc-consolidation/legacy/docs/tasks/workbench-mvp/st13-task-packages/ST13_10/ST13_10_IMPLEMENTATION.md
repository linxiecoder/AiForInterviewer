---
title: ST13_10_IMPLEMENTATION
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-10/st13-10-implementation-1
---

# ST13_10 实施说明：R1 RAG 最小可用任务包实施说明

## 当前实现授权状态

- 状态：`implementation_ready`
- 文档性质：ST13_10 official implementation packet 的范围输入；用于授权 R1 RAG foundation slice 的最小代码与测试路径。
- 当前 readiness：`DOC_STATE.yaml` 中 `ST13_10` 已为 `implementation_doc_state=active_working_doc`、`maturity=L5`、`readiness=implementation_ready`。
- 当前 formal window：`formal_window_status=open`。
- 当前 implementation approval：`implementation_approval_status=approved`。
- 当前允许：在 official packet 重新生成且 allowed paths 覆盖真实代码 / 测试路径后，进入 R1 RAG ingestion / indexing / retrieval / citation 最小可用 slice。
- 当前仍不允许：schema / migration / ORM implementation、完整 embedding pipeline、真实 vector store tuning、大规模 document ingestion、复杂 reranking、大规模 UI、R2 训练闭环、资产归档、批量导出、新依赖或无关重构。
- 已有状态层 task：`ST13_10 / WT13-10 / RAG / 知识库`。
- 不新增 task ID，不创建新长期状态入口。

## 本轮实施目标

- 修正 ST13_10 official implementation packet 的 allowed paths，使其基于真实 repo 结构授权 R1 RAG ingestion / indexing / retrieval / citation 的最小实现路径和 targeted tests 路径。
- 在新 official packet 授权后，实现 R1 RAG 最小可用 slice：文档切块、索引状态、keyword / substring retrieval、citation、evidence item、evidence gap、degraded trace 与 trace summary 读取。
- 继续消费 ST13_21 API contract、ST13_20 data readiness 和 ST13_24 acceptance / tests boundary。
- 保持 R1 RAG must-have / optional / R2-deferred 边界不变。
- 明确本 slice 只建立 domain 类型、service boundary、in-memory document index、deterministic chunking、query/result summary、citation/evidence/evidence gap、degraded 状态、visibility filter 和 evidence refs 接口，不进入 schema / migration / ORM。

## 允许修改范围

- `apps/api/app/rag/**`
- `apps/api/app/traceability.py`
- `tests/api/test_rag_foundation.py`
- `tests/api/test_traceability_integration.py`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_10/ST13_10_IMPLEMENTATION.md`

## 禁止修改范围

下方 `禁止修改` 子句柄用于让 evaluator 抽取 forbidden paths。

### 禁止修改

- `apps/web/**`
- `apps/api/app/schema/**`
- `apps/api/app/persistence.py`
- `infra/**`
- `tools/**`
- `docs/governance/**`
- `DOC_STATE.yaml`
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/**`
- `requirements.txt`
- `package.json`
- `apps/web/package.json`
- schema 文件
- migration 文件
- ORM / database implementation
- 完整 embedding pipeline
- 真实 vector store tuning
- 大规模 document ingestion
- 复杂 reranking
- 大规模 UI
- R2 训练闭环
- 资产归档
- 批量导出
- 复杂 tenant / RBAC
- 新依赖
- 任何新 task ID
- 任何新长期状态入口

## 测试与验证

ST13_10 implementation packet 至少需要覆盖以下 required tests 输入：

- governance / state validation：validate-state、evaluate-state、focused ST13_10 evaluate、preflight-open-window、git diff --check、allowed / forbidden path audit。
- targeted pytest：`.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_rag_foundation.py -q`。
- traceability pytest：`.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_traceability_integration.py -q`。
- py_compile：`.venv/bin/python -m py_compile apps/api/app/rag/__init__.py apps/api/app/rag/models.py apps/api/app/rag/service.py`。
- knowledge source boundary：用户私有资料、管理员公共资料、岗位、简历和历史回答 scope 的读取边界。
- document lifecycle：uploaded、parsing、parsed、indexed、failed、archived 等状态语义。
- indexing status：pending、running、indexed、failed、retryable 和 failure reason 的展示与追踪。
- retrieval query summary：query summary、scope、selected materials、topK、actor context 和 visibility filter。
- retrieval result summary：hit count、hit summary、empty result、permission filtered empty、degraded 和 retryable。
- citation contract：source ref、chunk ref、snippet summary、source label、visibility snapshot 不泄露不可见资源。
- evidence item / evidence gap：evidence summary、citation refs、confidence label、no result、index pending、index failed、RAG unavailable、low confidence。
- RAG unavailable / empty result / degraded behavior：主链路继续，评分、复盘、导出和历史回看明确降级或证据缺口。
- permission / resource visibility filtering：owner、visibility、resource_not_visible、permission_denied、安全 404 和脱敏输出。
- frontend display contract：面试台、评分、复盘、导出和历史回看能消费 citation、evidence item、evidence gap、pending、failed、degraded 和 empty state。
- persistence boundary：与 ST13_20 对齐 retrieval query、retrieval result、citation、evidence、source snapshot 和 permission snapshot。
- score / review / export / history evidence integration：评分理由、复盘证据、Markdown 导出和历史回看都能追溯 evidence refs、source snapshot、low confidence 和降级说明。

## 停止条件

出现以下任一情况必须停止：

1. 需要修改 `DOC_STATE.yaml` 或 `docs/governance/**`。
2. 需要修改 task remap。
3. 需要修改 `ST13_20`、`ST13_21` 或 `ST13_24` 文档正文。
4. 需要新增 task ID 或任何新长期状态入口。
5. Phase B 需要重新生成 packet 或打开 formal window。
6. 需要实现 packet 未授权的业务代码、测试代码、schema、migration、ORM、repository、worker、queue、provider 或前端页面。
7. 需要引入新依赖或环境变量。
8. `validate-state`、全量 `evaluate-state`、focused ST13_10 evaluate 或 ST13_10 preflight 失败且无法解释。
9. `git status --short` 出现本窗口允许范围外改动。
10. Phase A 后 official packet 仍不授权 `apps/api/app/rag/**` 与 `tests/api/test_rag_foundation.py`。
11. Phase B 需要修改 packet 未授权路径。

## 7. RAG 摄取 / 索引 / 检索最小实现输入

未来最小实现输入应按以下顺序收敛：

1. knowledge source：确认用户私有资料、管理员公共资料、岗位、简历、历史回答的 scope。
2. document ingestion：确认文档上传 / 粘贴、解析状态、失败原因和 source snapshot。
3. chunk / indexing：确认 chunk 引用、index status、index pending / failed / retryable。
4. retrieval query：确认 query summary、topK、scope、selected materials、visibility filter。
5. retrieval result：确认 hit summary、empty reason、permission filtered summary、degraded。
6. citation / evidence：确认 source ref、chunk ref、snippet summary、evidence gap、confidence label。
7. integration：确认面试台、评分、复盘、导出、历史回看如何消费。

该顺序是本 slice 的边界输入。本 slice 只允许创建 RAG foundation domain / service skeleton 与 targeted tests，不代表当前创建 schema、worker、queue、provider、真实向量库或 UI。

## 8. RAG 与评分 / 复盘 / 导出 / 历史回看的集成边界

| 下游 | RAG integration boundary |
| --- | --- |
| score | 评分可引用 evidence refs、evidence gap、low confidence；RAG evidence 不直接决定分数 |
| review | 复盘展示整场证据、关键缺口、建议来源和降级说明 |
| export | Markdown 导出包含 RAG 引用、证据缺口、低置信度和 content version |
| history | 历史回看恢复 source snapshot、citation、evidence gap 和当时的可见性摘要 |

训练闭环自动消费 RAG evidence 属于 R2，不进入 R1 must-have。

## 9. RAG 与前端 UI 消费的集成边界

未来前端消费需要遵守：

- 面试台展示 citation、reference summary、evidence gap、RAG degraded。
- 知识库显示 upload / parse / index status、failure reason、retryable。
- 评分 / 复盘显示 evidence、low confidence、missing evidence。
- 导出显示引用和证据缺口，但不得泄露不可见资源。
- empty result 与 RAG unavailable 必须区分展示。
- pending / running 不能误显示为无资料。

当前不实现页面、组件、hook、store、route 或样式。

## 10. RAG 与 schema / migration / ORM 的前置依赖

RAG implementation 进入持久化前必须等待：

- `ST13_20` 将 RAG must-persist 字段转换为明确 schema 设计。
- schema 文件路径、migration 工具、up/down、rollback、dry-run 策略确认。
- Citation / Evidence / SourceSnapshot 与权限字段的关系确认。
- embedding 向量是否落库、落哪里、如何脱敏和如何保留仍需另窗确认；R1 默认不把 embedding 向量作为必落库字段。
- ORM / repository / persistence layer 只有在 packet 授权后才可实现。

当前不允许进入 schema / migration / ORM implementation。

## 11. 后续窗口顺序建议

推荐顺序：

1. `R1-DEV-05-ST13_10-RAG-INGESTION-INDEXING-RETRIEVAL-CITATION`：修正 packet scope，重新生成 official packet，实现 RAG ingestion / indexing / retrieval / citation 最小可用 slice。
2. 后续 schema / migration readiness 只能在用户明确授权、packet 和状态 gate 通过后开启。
3. 后续 API / route / persistence / UI 集成必须另开 packet，不能由本 slice 顺手实现。

## 12. 完成判定

本 implementation window 完成判定：

- official packet 由 `generate-implementation-packet` 重新生成，且 allowed paths 包含 `apps/api/app/rag/**`、`apps/api/app/traceability.py`、`tests/api/test_rag_foundation.py` 与 `tests/api/test_traceability_integration.py`。
- packet 不再只授权 ST13_10 文档路径，且 forbidden paths 继续禁止 schema / migration / ORM、新依赖、大规模 UI、R2 训练闭环、资产归档和批量导出。
- `apps/api/app/rag/**` 提供 RAG domain 类型、service boundary、in-memory document index、deterministic chunking、index status、retrieval query summary、retrieval result summary、citation / evidence item / evidence gap、degraded 状态和 visibility filter。
- RAG retrieval 对 score / review / export / history 预留 evidence reference contract，并通过 traceability summary 读取 citation / evidence gap；不修改对应业务服务。
- `tests/api/test_rag_foundation.py` 至少覆盖 chunking、indexed hit、citation、no result gap、pending / failed index gap、permission filtering 和 degraded behavior。
- `tests/api/test_traceability_integration.py` 至少覆盖 retrieval trace 写入后可通过 trace summary 读取 citation / evidence / evidence gap。
- 明确 `ST13_10` 是 R1 RAG anchor。
- 明确不新增 task ID。
- 明确当前不能进入 schema / migration / ORM implementation。
- 未新增第三方依赖或环境变量。