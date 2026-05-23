---
title: 前后端验证计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/validation-plan
---

# 前后端验证计划

## 1. 文档目的

本文定义 PR1-PR8 的分阶段验证骨架，保证 docs、runtime、facade、graph、frontend UI、report/review/candidate closure 都有最小可执行验证命令。

## 2. 输入来源

- active docs：`BACKLOG.md`、`DELIVERY_PLAN.md`、`TEST_POLICY.md`、`SECURITY_PRIVACY.md`、`PERSISTENCE_MODEL.md`
- `13_TEST_PLAN_BACKEND.md`
- `14_TEST_PLAN_FRONTEND.md`
- 当前 package scripts 和 pytest 结构只读盘点

## 3. 当前状态

当前仓库常用验证入口包括 `git status`、`git diff --check`、`.venv/bin/python -m pytest ...`、`npm run web:test`、`npm run web:build` 和文档治理命令。PR1 不运行全量业务测试。

## 4. 目标输出

每个 PR 都有：

- repo-state gate。
- diff check。
- backend pytest 最小集合。
- frontend test/build，如适用。
- fake transport gate。
- real provider gated manual test。
- sensitive redaction scan。

## 5. 必须覆盖范围

| 阶段 | 验证命令占位 | 通过条件 | 失败处理 |
|---|---|---|---|
| PR1 docs 验证 | `git status --short --untracked-files=all`; `git diff --stat`; `git diff --check`; doc governor minimal | 只变更允许文档；无 whitespace error；docs gate 通过 | 停止并修正文档/索引 |
| PR2 AI Runtime 基础模型验证 | `pytest tests/api/test_agent_run_repository.py tests/api/test_llm_call_repository.py tests/api/test_sensitive_payload_redaction.py -q` | 表/仓储/脱敏通过 | rollback migration 或修 schema |
| PR3 AI Orchestration Facade 验证 | `pytest tests/api/test_agent_contracts.py tests/api/test_agent_graph_runner.py tests/api/test_architecture_boundaries.py -q` | Core 不 import LangGraph；facade contract 通过 | 停止迁移业务 graph |
| PR4 LangGraph Runtime + Fake Graph 验证 | `pytest tests/api/test_langgraph_checkpointer_factory.py tests/api/test_agent_interrupt_replay.py tests/api/test_agent_runtime_api.py -q` | fake graph start/resume/replay/timeline 通过 | 关闭 runtime feature flag |
| PR5 Job Match Graph 验证 | `pytest tests/api/test_agent_graphs.py tests/api/test_architecture_boundaries.py -q` plus job match subset | score、analysis、candidate-only 通过 | fallback legacy path 或禁用 graph |
| PR6 Polish Question / Feedback Graph 验证 | polish graph subset plus existing polish API tests | answer save no LLM；feedback independent task | fallback deterministic / legacy path |
| PR7 Frontend AI Runtime UI 验证 | `npm run web:test`; `npm run web:build` | status/timeline/interrupt/candidate UI 编译/测试通过 | 关闭 UI feature flag |
| PR8 Report / Review / Candidate Closure 验证 | report/review/candidate backend subset; `npm run web:test`; optional `npm run web:smoke:auth` | copy boundary、confirmation、redaction 通过 | 禁用 graph/candidate closure |

### 5.1 通用命令占位

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
.venv/bin/python -m pytest tests/api/test_architecture_boundaries.py -q
npm run web:test
npm run web:build
```

### 5.2 fake / real provider gate

| Gate | 默认 | 条件 |
|---|---|---|
| fake transport gate | 必跑 | 所有 PR4-PR8 graph tests 使用 deterministic fake |
| real provider gated manual test | 默认不跑 | 只能在显式 env flag、人工批准、raw-off scan 通过后执行 |
| sensitive redaction scan | PR4 起必跑 | 扫描 response/log/timeline/checkpoint ref，不扫描 raw store 内容 |

### 5.3 sensitive redaction scan 占位

```bash
rg -n "raw_prompt|raw_completion|provider_payload|system prompt|hidden_rubric|api_key|token|cookie|secret|full_resume|full_jd" apps/api tests/api apps/web/src
```

## 6. 与 active docs 的关系

本文提供验证计划，不替代 `TEST_POLICY.md`、`SECURITY_PRIVACY.md` 或后续 F7 测试计划。每个 PR 的实际结果必须写入对应 PR 总结或 active delivery docs。

## 7. 非目标

- 不默认执行全量业务测试。
- 不默认执行真实 provider。
- 不以 smoke 代替 security/privacy。
- 不把测试全绿写成 release Go。

## 8. 后续 PR 使用方式

每个 PR 开始时复制对应行作为 Scope Lock，结束时填实际命令、结果、失败项分类和 residual risk。

## 9. Definition of Done

- PR1-PR8 验证矩阵已覆盖。
- 包含 git status、diff stat、diff check、pytest、frontend test/build、fake transport、real provider gated manual test、redaction scan。
- 明确失败项处理方式和默认不跑真实 provider。

