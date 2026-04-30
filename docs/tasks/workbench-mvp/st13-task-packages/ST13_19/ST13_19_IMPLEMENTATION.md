---
title: ST13_19_IMPLEMENTATION
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-19/st13-19-implementation
---

# ST13_19 Markdown 导出 / 复制实施说明

## 1. 文档定位

本文档冻结 `R0-Final-04` Markdown export / copy 实现窗口的 implementation gate 输入。它不是 implementation packet；是否可实施以 `DOC_STATE.yaml`、doc-governor gate 和生成的 packet 为准。

## 2. 本轮实施目标

- 为 R0 提供评分 / 复盘 / Markdown 导出最小闭环中的 Markdown export content。
- 基于 ST13_12 session / turns / answers、ST13_13 score、ST13_15 review。
- 返回 content、format、content_version、metadata。
- 复用 ST13_20 persistence，把 export payload 写入 session payload。
- 不实现 PDF、asset archive、frontend 或完整导出平台。

## 3. 允许修改

- `apps/api/app/api/v1/**`
- `apps/api/app/export/**`
- `apps/api/app/review/**`，仅限读取 review payload
- `apps/api/app/scoring/**`，仅限读取 score payload
- `apps/api/app/interview_flow/**`，仅限读取 session / turns / answers 与最小 payload 衔接
- `apps/api/app/main.py`，仅限 router registration / handler wiring
- `apps/api/app/boundary.py`，仅限 error envelope compatibility
- `tests/api/test_review_export.py`
- `tests/api/test_interview_flow.py`，仅限 e2e 衔接最小调整

## 4. 禁止修改

- `docs/governance/DOC_STATE.yaml`，implementation 窗口中禁止手改
- `docs/governance/transition_history.jsonl`，implementation 窗口中禁止手改
- `docs/governance/packets/**`
- `tools/**`
- `infra/**`
- `apps/web/**`
- 完整 RAG
- 完整 DB / ORM / migration
- 训练中心
- 资产归档
- PDF 导出
- 前端
- `package.json`
- lockfile
- CI 配置
- `requirements.txt`
- `docs/requirements/workbench-mvp/**`
- `docs/design/workbench-mvp/**`

## 5. 自动化验证

- `git diff --check`
- `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_19`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_13`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_15`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_11`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_12`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_20`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_review_export.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_flow.py -q`
- `git status --short`

## 6. 必测场景

- Markdown export content 包含 interview / session 信息。
- Markdown export content 包含 question 和 answer。
- Markdown export content 包含 score。
- Markdown export content 包含 review summary。
- Markdown export content 包含 weakness / improvement 最小输出。
- export metadata 包含 format、content_version、generated_at 或等价字段。
- session 不存在时返回 404 stable error envelope。
- validation error 返回 stable error envelope。
- persistence 将 export payload 写入 session payload。
- 既有 main flow tests 不回退。
- 既有 persistence behavior 不回退。

## 7. 完成判定

- 已存在的 interview session 可以生成 Markdown export content。
- Markdown export 足够确定，可被测试稳定断言。
- Response 包含 content、format、content_version、metadata。
- Markdown content 包含 interview、answer、score 和 review。
- persistence 复用 ST13_20 store，不引入完整 DB / ORM / migration。
- error envelope 与 ST13_21 保持兼容。
- 导出范围不扩展到 PDF、资产归档、前端或 R1/R2 完整导出平台。
- required tests 通过。
- governance validation 保持 green。
- implementation 只触碰 packet allowed paths。

## 8. 停止条件

- task gate 无法合法推进。
- 需要真实 LLM network / key 才能测试。
- 需要完整 RAG。
- 需要训练中心。
- 需要资产归档。
- 需要 PDF 导出。
- 需要前端。
- 需要完整 DB / ORM / migration。
- 需要修改 forbidden paths。
- state transition 不能由当前规则合法完成。