# tests 局部规则

本文件只补充根目录 `AGENTS.md`。冲突时以根规则、`docs/00-governance/TEST_POLICY.md`、`pytest.ini` 和当前测试代码为准。

## 测试结构

- `tests/api` 是核心后端/API/LLM/Polish/provider 回归区。
- `tests/doc_governor` 覆盖文档治理 CLI、状态机、临时产物治理和规则验证。
- `tests/evals` 与 `evals/` 覆盖 Phase 9 / Phase 12 deterministic、replay 和 negative-control gate。
- `tests/architecture`、`tests/domain`、`tests/application` 覆盖分层、领域策略和 agent runtime 边界。
- `apps/web/src/**/*.test.ts(x)` 是前端 TypeScript 类型/契约断言，不在 pytest 下运行。

## pytest

- `pytest.ini` 指定 `testpaths = tests`，启用 `--strict-markers`、`--strict-config`、`-p no:cacheprovider`。
- marker 目前只有 `integration` 和 `slow`；新增 marker 前先更新 `pytest.ini`。
- API 测试需要 `apps/api` import path；保持 `PYTHONPATH=.:apps/api` 语义或使用既有 conftest。
- 优先跑聚焦命令，例如 `PYTHONPATH=.:apps/api python -m pytest tests/api/<target>.py -q`。

## 测试替身

- `tests/fakes/llm_transport.py` 是 Fake LLM 测试入口，只能测试显式注入。
- 生产代码不得从 `tests` 反向依赖，也不得允许环境变量启用 fake provider 成为成功路径。
- `tests/api/asgi_client.py` 是 sandbox-stable ASGI 调用器；API 回归优先使用它，不依赖外部 server。

## 临时产物

- 测试临时目录必须走 `ManagedTempArtifacts`、`ManagedTempArtifactsTestCase` 或 pytest 受管 fixture。
- 不要在仓库根或 `tests/` 下直接创建 `tmp`、`_tmp`、`temp*`。
- 不要手写 `shutil.rmtree()` 清测试目录，除非先确认符合 `TEST_POLICY.md` 的受管边界。

## 证据表述

- deterministic、replay、fake、eval gate 只能表述为回归证据，不得表述为真实 provider 质量认证。
- 当前 GitHub workflow 只覆盖 eval gate 子集；不要把它写成 full pytest、web build、web smoke 或部署通过。
- 涉及 F7、E2E、全链路测试计划时，必须回到 `docs/03-implementation/BACKLOG.md` 的 `AIFI-QA-*` 和 `DELIVERY_PLAN.md`。

## 前端测试

- `npm run web:test` 走 TypeScript 编译契约，不会启动浏览器。
- `scripts/qa/authenticated-frontend-smoke.mjs` 是 Node/Vite/API smoke，不是 Playwright。
- 修改 `apps/web/src/app/routes/router.tsx`、导航或页面状态时，优先更新邻近 `*.test.ts(x)` 类型断言。
- 引入新的测试 runner 前，必须先落到授权任务和 active docs，不要隐式创建 F7 外测试体系。
