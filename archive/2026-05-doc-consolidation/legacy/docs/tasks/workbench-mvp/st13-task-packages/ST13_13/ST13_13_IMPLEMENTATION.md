---
title: ST13_13_IMPLEMENTATION
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-13/st13-13-implementation-1
---

# ST13_13 评分体系实施说明

## 1. 文档定位

本文档冻结 `R1-DEV-08B` 评分实现窗口的 implementation gate 输入。它不是 implementation packet；是否可实施以 `DOC_STATE.yaml`、doc-governor gate 和生成的 packet 为准。

## 2. 本轮实施目标

- 为 R1 提供 0-100 多维评分 payload，作为 ST13_15 可信复盘证据链输入。
- 基于 ST13_12 main flow session、turns、answers、ST13_10 RAG citation / evidence gap 与 trace summary 生成评分。
- 输出 score_total、dimensions、dimension reason、citation_refs、evidence_gap_refs、low_confidence、suggestions、weak_areas、review_summary 与 status。
- 复用 ST13_20 interview payload / traceability refs，不新增 schema、ORM、Alembic 或规范化 score tables。
- 保持 ST13_21 API contract 与前端可信详情页可消费。

## 3. 允许修改

- `apps/api/app/api/v1/**`
- `apps/api/app/scoring/**`
- `apps/api/app/review/**`，仅限评分结果与可信复盘证据链衔接
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
- score_reports / score_dimensions 等新增规范化评分表
- 高级检索质量平台
- embedding / vector store 新实现
- 新 LLM provider
- 真实 secret、真实 `DATABASE_URL`、真实 `TEST_DATABASE_URL`
- 完整 RAG 质量评估
- 训练中心
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
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_13`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_15`
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

- 已存在的 interview session 可以生成 `0-100` 的 `score_total`。
- score payload 包含多个 `dimensions[]`，每个 dimension 包含 `id`、`label`、`score`、`reason`、`citation_refs`、`evidence_gap_refs`、`low_confidence` 与 `low_confidence_reason`。
- RAG citation / evidence gap 可影响 reason 与 confidence，但不得直接机械决定分数。
- evidence gap 或 degraded trace 时输出 `low_confidence` 或 `status=degraded`，且评分 / 复盘不崩溃。
- session 不存在时返回 404 stable error envelope。
- validation error 返回 stable error envelope。
- 如使用 provider-assisted scoring，provider failure 必须映射到 stable error envelope。
- persistence 将 score payload 写入 session payload，并写入可读取的 score / review trace reference。
- 前端可信详情页能展示总分、维度、reason、citation、gap、suggestions、weak areas 与稳定空态。
- 页面不得展示 full prompt、raw LLM response、secret、object storage path 或 hidden resource id。
- 既有 provider tests 不回退。
- 既有 main flow tests 不回退。
- 既有 persistence behavior 不回退。

## 7. 完成判定

- 已存在的 interview session 可以生成边界为 0-100 的多维 score payload。
- score 输出足够确定，可被 API 与前端测试稳定断言。
- 如使用 provider，调用必须通过 ST13_11 boundary。
- persistence 复用 ST13_20 store，不引入 schema、完整 DB、ORM 或 migration。
- error envelope 与 ST13_21 保持兼容。
- 评分范围不扩展到 R2 训练闭环、资产归档或高级检索质量平台。
- required tests 通过。
- governance validation 保持 green。
- implementation 只触碰 packet allowed paths。

## 8. 停止条件

- task gate 无法合法推进。
- 需要真实 LLM network / key 才能测试。
- 需要新增 schema / migration 或规范化评分表。
- 需要完整 RAG 质量平台。
- 需要训练中心。
- 需要资产归档。
- 需要 PDF 导出。
- 需要 ORM / Alembic。
- 需要真实 secret 或 `.env` 提交。
- 需要修改 forbidden paths。
- state transition 不能由当前规则合法完成。