# ST13_15 模拟面试复盘实施说明

## 1. 文档定位

本文档冻结 `R0-Final-04` 模拟面试复盘实现窗口的 implementation gate 输入。它不是 implementation packet；是否可实施以 `DOC_STATE.yaml`、doc-governor gate 和生成的 packet 为准。

## 2. 本轮实施目标

- 为 R0 提供评分 / 复盘 / Markdown 导出最小闭环中的 review summary。
- 基于 ST13_12 main flow session 和 ST13_13 score。
- 输出主要表现、风险、建议、weakness / improvement minimal output。
- 可调用 ST13_11 provider boundary，也可使用 deterministic review rule。
- 复用 ST13_20 persistence，把 review payload 写入 session payload。

## 3. 允许修改

- `apps/api/app/api/v1/**`
- `apps/api/app/review/**`
- `apps/api/app/scoring/**`，仅限读取或复用 score payload
- `apps/api/app/export/**`，仅限 review payload 与导出衔接的最小共享类型
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
- 训练抽屉
- 弱点累计 / 消减 / 归档生命周期
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
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_15`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_13`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_11`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_12`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_20`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_review_export.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_flow.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_llm_provider.py -q`
- `git status --short`

## 6. 必测场景

- 已存在的 interview session 可以生成 review summary。
- review summary 包含主要表现、风险和建议字段。
- weakness / improvement 最小输出存在。
- 如使用 provider-assisted review，provider failure 必须映射到 stable error envelope。
- session 不存在时返回 404 stable error envelope。
- validation error 返回 stable error envelope。
- persistence 将 review payload 写入 session payload。
- 既有 provider tests 不回退。
- 既有 main flow tests 不回退。
- 既有 persistence behavior 不回退。

## 7. 完成判定

- 已存在的 interview session 可以生成 review summary。
- review summary 与 weakness / improvement 输出存在。
- 如使用 provider，调用必须通过 ST13_11 boundary。
- persistence 复用 ST13_20 store，不引入完整 DB / ORM / migration。
- error envelope 与 ST13_21 保持兼容。
- 复盘范围不扩展到 R1/R2 完整复盘中心或训练中心。
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
