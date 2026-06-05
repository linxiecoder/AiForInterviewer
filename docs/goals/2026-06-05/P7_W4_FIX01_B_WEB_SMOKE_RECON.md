---
title: P7_W4_FIX01_B_WEB_SMOKE_RECON
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w4-fix01-b-web-smoke-recon
---

# P7-W4.fix.01 B Web Smoke Auth Recon

Window ID: `P7-W4.fix.01-FULL-VALIDATION-BLOCKER-REMEDIATION`

Agent: Web Smoke Auth Recon Agent

Mode: `READ_ONLY`

## 结论

`npm run web:smoke:auth` 的 blocker 是 `scripts/qa/authenticated-frontend-smoke.mjs` 的 `smokeEnv()` 显式设置 `LLM_PROVIDER: "fake"`。Phase 7 runtime policy 已要求 `LLM_PROVIDER=fake` fail-closed，因此 API app 在 startup 调用 `build_llm_transport_from_env()` 时抛出 `LlmTransportConfigurationError`。

Controller Decision A 已确认：auth smoke 不得依赖 fake LLM provider；不得弱化 runtime fake rejection。最小修复是让 auth smoke 覆盖外部 fake env，使用非 fake runtime provider wiring 启动 API，但当前 smoke 路径不触发 LLM generate。

## 读取范围

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/goals/2026-06-05/P7_W4_FINAL_REPORT.md`
- `docs/goals/2026-06-05/P7_W3_FINAL_REPORT.md`
- `docs/project-sources/20_PHASE7_CLOSEOUT.md`
- `package.json`
- `apps/web/package.json`
- `scripts/qa/authenticated-frontend-smoke.mjs`
- `scripts/qa/seed_authenticated_frontend_smoke.py`
- `apps/api/app/main.py`
- `apps/api/app/infrastructure/llm/runtime.py`
- `apps/api/app/infrastructure/llm/openai_compatible.py`
- `tests/api/test_llm_runtime.py`
- `tests/api/test_fake_llm_boundary.py`

## Script 路径

| Script | 定义 |
|---|---|
| `npm run web:smoke:auth` | root `package.json`: `node scripts/qa/authenticated-frontend-smoke.mjs` |
| `npm run web:test` | root `package.json`: `npm --workspace apps/web run test` |
| `apps/web` test | `tsc -p tsconfig.json --noEmit` |

`web:test` 不调用 auth smoke script，不读取或设置 `LLM_PROVIDER`。

## Fake Env 设置位置

`scripts/qa/authenticated-frontend-smoke.mjs` 的 `smokeEnv()` 设置：

```js
LLM_PROVIDER: "fake",
```

该 env 用于：

- seed helper 子进程。
- API 子进程。

seed helper 只写入 SQLite smoke 数据，不需要 LLM provider。API 子进程会在 app startup 构造 LLM transport，因此被 fake runtime rejection 拦截。

## 最小改法

将 auth smoke env 改为：

```js
LLM_PROVIDER: "",
```

理由：

- `smokeEnv()` 先展开 `...process.env`，显式空值可以覆盖外部 `LLM_PROVIDER=fake`。
- `apps/api/app/infrastructure/llm/runtime.py` 对 blank provider 走默认 `openai_compatible`。
- auth smoke 当前只覆盖 health、HTML、login、auth/me、polish session list/detail，不触发真实 LLM generate。
- OpenAI-compatible transport 构造本身不要求 API key；只有 generate 路径才需要 key。

## Runtime Fake Rejection 非回归边界

必须保持：

- `LLM_PROVIDER=fake` 在 `build_llm_transport_from_env()` 中继续抛出 `LlmTransportConfigurationError`。
- `create_app()` 在 runtime fake env 下继续失败。
- `FakeLlmTransport()` 只能作为显式测试注入使用。

验证入口：

- `tests/api/test_llm_runtime.py`
- `tests/api/test_fake_llm_boundary.py`

## 风险

- 仅删除 `LLM_PROVIDER` 行会透传外部 fake env，因此必须显式置空。
- 若未来 auth smoke 增加会触发 LLM generate 的路径，不能回退到 runtime `LLM_PROVIDER=fake`，需要另行授权设计非 fake smoke 策略。
