# ST13_12 多轮上下文 / 状态机实施说明

## 1. 文档定位

本文档冻结 R0-Final-03 主链路实现窗口的 implementation gate 输入。它不实现主链路业务代码，只用于 formal window、implementation approval 与 implementation packet。

## 2. 本轮实施目标

- 实现 R0 最小模拟面试主链路：start interview、generate first question、submit answer、next turn / minimal follow-up、save / restore / history。
- 使用 ST13_11 provider boundary 生成问题和最小追问，不绕过 provider interface。
- 复用 ST13_20 R0 minimal persistence，不新增完整 DB / ORM / migration。
- 复用 ST13_21 API boundary 与 error envelope。
- 保持 validation、404、provider failure 与 persistence failure 的稳定错误表达。

## 3. 允许修改

- `apps/api/app/api/v1/**`
- `apps/api/app/interview_flow/**`
- `apps/api/app/main.py`，仅限 router registration / handler wiring
- `apps/api/app/boundary.py`，仅限 error envelope compatibility
- `tests/api/test_interview_flow.py`
- `tests/api/**`，仅限主链路直接相关的最小测试调整

## 4. 禁止修改

- `docs/governance/DOC_STATE.yaml`，implementation 窗口中禁止手改
- `docs/governance/transition_history.jsonl`，implementation 窗口中禁止手改
- `docs/governance/packets/**`
- `tools/**`
- `infra/**`
- `apps/web/**`
- scoring / review / Markdown export business
- full RAG / knowledge base governance
- full DB migration / ORM / repository
- `package.json`
- lockfile
- CI 配置
- `docs/requirements/workbench-mvp/**`
- `docs/design/workbench-mvp/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/**`

## 5. 自动化验证

- `git diff --check`
- `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_12`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_11`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_20`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_flow.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_llm_provider.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_records.py -q`

## 6. 手动验证

- `git diff --name-only` 确认未修改 forbidden paths。
- 复核主链路实现没有直接调用真实 provider SDK / HTTP client。
- 复核 deterministic provider 只在 test/dev 显式配置下用于测试。

## 7. 完成判定

- start -> question -> answer -> next-turn / follow-up 最小主链路可运行。
- provider 调用必须通过 ST13_11 boundary，不绕过 provider interface。
- persistence 复用 ST13_20 store，不新建 full DB / ORM / migration。
- owner_id 最小隔离保持，history / restore 不跨 owner 泄露。
- provider failure、validation error、missing session 404 均返回稳定 error envelope。
- scoring / review / Markdown export 未实现。
- full RAG、frontend、完整训练闭环未实现。
- 主链路测试、provider tests、persistence tests 通过。
- governance validation 保持 green。

## 8. 必测场景

- start interview success using deterministic provider
- provider failure propagates stable error envelope
- submit answer success
- next turn / minimal follow-up
- save to persistence
- restore session
- history list owner scoped
- validation error
- missing session 404
- existing ST13_11 provider tests no regression
- existing ST13_20 persistence tests no regression

## 9. 停止条件

- main flow gate 无法合法推进。
- 需要真实 LLM 外部网络或真实 API key 才能测试。
- 需要 scoring / review / Markdown export。
- 需要 RAG。
- 需要 full DB / ORM / migration。
- 需要 frontend。
- 需要修改 forbidden paths。
- 需要绕过 provider interface。
- state transition 不能由当前规则合法完成。
