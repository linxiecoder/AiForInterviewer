---
title: ST13_15_IMPLEMENTATION
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-15/st13-15-implementation
---

# ST13_15 模拟面试复盘实施说明

## 1. 文档定位

本文档冻结 `R1-DEV-08B` 模拟面试可信复盘实现窗口的 implementation gate 输入。它不是 implementation packet；是否可实施以 `DOC_STATE.yaml`、doc-governor gate 和生成的 packet 为准。

## 2. 本轮实施目标

- 为 R1 提供可信复盘 payload，消费 ST13_13 多维评分、ST13_10 RAG citation / evidence gap 与 trace summary。
- 输出用户可读 review_summary、dimension reason 汇总、suggestions、weak_areas、citation_refs、evidence_gap_refs、status、degraded 与 retryable。
- 将证据不足、RAG degraded 或 provider fallback 显式映射为低置信度说明，不保存完整 prompt 或 raw LLM response。
- 复用 ST13_20 interview payload / traceability refs，不新增 schema、ORM、Alembic 或规范化 review tables。
- 保持 ST13_21 API contract 与前端可信详情页可消费。

## 3. 允许修改

- `apps/api/app/api/v1/**`
- `apps/api/app/review/**`
- `apps/api/app/scoring/**`，仅限读取或复用多维 score payload
- `apps/api/app/export/**`，仅限 review payload 与导出衔接的最小共享类型
- `apps/api/app/interview_flow/**`，仅限读取 session / turns / answers 与最小 payload 衔接
- `apps/api/app/traceability.py`，仅限 score / review / RAG evidence refs 的安全摘要衔接
- `apps/api/app/persistence.py`，仅限复用既有 payload / traceability store，不新增 schema
- `apps/api/app/main.py`，仅限 router registration / handler wiring
- `apps/api/app/boundary.py`，仅限 error envelope compatibility
- `tests/api/test_review_export.py`
- `tests/api/test_traceability_integration.py`
- `tests/api/test_rag_persistence.py`
- `tests/api/test_interview_flow.py`，仅限 e2e 衔接最小调整
- `apps/web/src/interview/**`
- `apps/web/src/components/TrustedTracePage.tsx`
- `apps/web/e2e/trusted-trace.spec.ts`

## 4. 禁止修改

- `docs/governance/DOC_STATE.yaml`，implementation 窗口中禁止手改
- `docs/governance/transition_history.jsonl`，implementation 窗口中禁止手改
- `docs/governance/packets/**`
- `tools/**`
- `infra/**`
- `.env`
- `.env.*`
- 未授权 schema / migration
- ORM / Alembic
- score_reports / score_dimensions / review_reports 等新增规范化表
- 高级检索质量平台
- embedding / vector store 新实现
- 新 LLM provider
- 真实 secret、真实 `DATABASE_URL`、真实 `TEST_DATABASE_URL`
- 完整 RAG 质量评估
- 训练中心
- 训练抽屉
- 弱点累计 / 消减 / 归档生命周期
- 资产归档
- PDF 导出
- R2 训练闭环
- 大规模 UI 重构
- 新状态管理库
- `package.json`
- lockfile
- CI 配置
- `requirements.txt`
- `docs/requirements/workbench-mvp/**`
- `docs/design/workbench-mvp/**`

## 5. 自动化验证

- `git diff --check`
- `.venv/bin/python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_15`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_13`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_10`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_20`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_review_export.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_traceability_integration.py tests/api/test_rag_persistence.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_flow.py -q`
- `npm --workspace apps/web run build`
- `npm --workspace apps/web run test`
- `npm --workspace apps/web run e2e`
- `git status --short`

## 6. 必测场景

- 已存在的 interview session 可以生成可信 `review_summary`。
- review payload 包含 `score_total`、`dimensions`、dimension reason、`citation_refs`、`evidence_gap_refs`、`suggestions`、`weak_areas`、`status`、`degraded` 与 `retryable`。
- evidence gap 或 degraded trace 时输出低置信度说明，并保持复盘可读。
- 如使用 provider-assisted review，provider failure 必须映射到 stable error envelope。
- session 不存在时返回 404 stable error envelope。
- validation error 返回 stable error envelope。
- persistence 将 review payload 写入 session payload，并写入可读取的 score / review trace reference。
- 前端可信详情页能展示总分、维度、reason、citation、gap、suggestions、weak areas 与稳定空态。
- 页面不得展示 full prompt、raw LLM response、secret、object storage path 或 hidden resource id。
- 既有 provider tests 不回退。
- 既有 main flow tests 不回退。
- 既有 persistence behavior 不回退。

## 7. 完成判定

- 已存在的 interview session 可以生成可信复盘 payload。
- review summary、suggestions、weak areas 与 evidence refs 输出存在，并可被 API 与前端测试稳定断言。
- 如使用 provider，调用必须通过 ST13_11 boundary。
- persistence 复用 ST13_20 store，不引入 schema、完整 DB、ORM 或 migration。
- error envelope 与 ST13_21 保持兼容。
- 复盘范围不扩展到 R2 训练闭环、资产归档或高级检索质量平台。
- required tests 通过。
- governance validation 保持 green。
- implementation 只触碰 packet allowed paths。

## 8. 停止条件

- task gate 无法合法推进。
- 需要真实 LLM network / key 才能测试。
- 需要新增 schema / migration 或规范化复盘表。
- 需要完整 RAG 质量平台。
- 需要训练中心。
- 需要资产归档。
- 需要 PDF 导出。
- 需要 ORM / Alembic。
- 需要真实 secret 或 `.env` 提交。
- 需要修改 forbidden paths。
- state transition 不能由当前规则合法完成。
