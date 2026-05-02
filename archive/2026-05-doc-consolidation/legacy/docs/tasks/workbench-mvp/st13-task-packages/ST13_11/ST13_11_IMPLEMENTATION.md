---
title: ST13_11_IMPLEMENTATION
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-11/st13-11-implementation-1
---

# 子任务实施文档

## 1. 文档定位

- 本文档定义 `ST13_11` 在 `R0-Final-02` 中的 provider implementation gate 输入。
- 本文档不是 implementation packet；是否可实施以 `DOC_STATE.yaml`、doc-governor gate 和生成的 packet 为准。
- 本窗口只做 gate / packet 前置收敛，不写 provider 代码。

## 2. 基本信息与关联

- 子任务 ID：`ST13_11`
- 子任务名称：真实 LLM provider / adapter
- 所属 requirement：`RQ01`
- 所属模块：`M04`
- 对应设计文档：`docs/tasks/workbench-mvp/st13-task-packages/ST13_11/ST13_11_DESIGN.md`
- 对应官方状态条目：`docs/governance/DOC_STATE.yaml -> subtasks.ST13_11`

## 3. 本轮实施目标

- 为真实 R0 实现 LLM provider boundary。
- 支持真实 provider 配置。
- 支持 deterministic provider 仅用于 test / dev。
- 实现 provider interface、request model、result model、provider config、real provider adapter boundary、deterministic test provider、provider error mapping 和 provider tests。
- 不实现 interview main flow。
- 不实现 scoring / review / Markdown export。
- 不实现 full RAG。
- 不实现 prompt platform。

## 4. 实施前提与阻塞

- 必须先通过 `validate-state`。
- 必须先通过 `evaluate-state --entity-type subtask --entity-id ST13_11`。
- 必须生成并复核 `ST13_11` implementation packet。
- 如果真实 API key 或真实外部网络成为测试前提，必须停止。

## 5. 允许修改范围

### 5.1 允许修改

- `apps/api/app/llm/**`
- `apps/api/app/boundary.py`
- `apps/api/app/main.py`
- `apps/api/app/config.py`
- `tests/api/test_llm_provider.py`
- `.env.example`
- `requirements.txt`

### 5.2 禁止修改

- `docs/governance/DOC_STATE.yaml`
- `docs/governance/transition_history.jsonl`
- `docs/governance/packets/**`
- `tools/**`
- `infra/**`
- `apps/web/**`
- `package.json`
- `package-lock.json`
- lockfile
- CI 配置
- interview main flow routes / services
- scoring / review / Markdown export business
- full RAG
- full DB migration / ORM / repository
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/**`
- `docs/requirements/workbench-mvp/**`
- `docs/design/workbench-mvp/**`

## 6. 实施方案

### 6.1 计划改动

- 新增 provider interface、request model 和 result model。
- 新增真实 provider adapter boundary，并允许测试 mock client / transport。
- 新增 deterministic provider，并限制为 test / dev 显式配置。
- 新增 provider config 读取与校验。
- 将 provider failure 映射到稳定错误码和 error envelope。

### 6.2 关键技术约束

- `LLM_PROVIDER` 选择 provider。
- `LLM_API_KEY` 只用于真实 provider，不写入测试 fixture。
- `LLM_MODEL` 指定真实模型或安全默认。
- `LLM_TIMEOUT_SECONDS` 必须有明确默认。
- provider 缺配置、非法 provider、timeout、client failure 和 unavailable 必须可断言。
- deterministic provider metadata 必须明确标记 provider=deterministic。
- 不允许 silent fallback。

## 7. 测试与验证

### 7.1 自动化验证

- `git diff --check`
- `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_11`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_20`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_llm_provider.py -q`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_records.py -q`
- `git status --short`

### 7.2 必须覆盖的测试场景

- provider config missing。
- invalid provider name。
- deterministic provider success。
- deterministic provider not reported as real provider。
- real provider mocked success。
- provider failure maps to stable error。
- timeout / client failure path。
- no external network call in tests。
- env / config parsing。
- existing ST13_20 persistence tests no regression。

## 8. 完成判定

- Provider interface exists and is typed or documented.
- Real provider adapter can be configured without running network tests.
- Deterministic provider is explicit test or dev only.
- Deterministic provider is not reported as real provider.
- Provider failures map to stable error codes.
- Provider config missing returns a stable error.
- No main flow implementation is introduced in this window.
- No scoring, review, Markdown export, full RAG, full DB, ORM or migration implementation is introduced in this window.
- Required provider tests pass.
- Existing ST13_20 persistence tests do not regress.
- Governance validation remains green.
- Implementation only touches packet allowed paths.
- Forbidden paths remain untouched.

## 9. 停止条件

- 需要真实 API key 才能测试。
- 需要真实外部网络才能通过测试。
- 需要实现 main flow API。
- 需要实现 scoring / review / Markdown export。
- 需要 full RAG / full DB / ORM / migration。
- 需要修改 forbidden paths。
- provider fallback 会把失败伪装成成功。
- state transition 不能由当前规则合法完成。