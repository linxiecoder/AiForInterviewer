---
title: FEEDBACK_LOOP_QA_EVIDENCE
type: qa-evidence
status: active-f8
owner: 发布与质量
source_task: AIFI-REL-009
permalink: ai-for-interviewer/docs/03-implementation/feedback-loop-qa-evidence
---

# FEEDBACK_LOOP_QA_EVIDENCE

本文档归档 feedback-loop（反馈闭环）Step1 到 Step11 的 QA evidence（质量证据）摘要，供 Step12 / AIFI-REL-009 release gate（发布门禁）使用。原始证据仍以对应测试输出、commit（提交）和 `.omo/evidence/**` 为准；本文件不替代代码事实，也不声明生产可发布。

## 1. Evidence Matrix（证据矩阵）

| Step | AIFI | 状态 | 关键证据 | Release gate 处理 |
|---|---|---|---|---|
| Step1 | AIFI-QA-004 | ACCEPTED_RED | feedback acceptance semantics tests（反馈验收语义测试）首批护栏；RED 保留为实现缺口证据 | Accepted gap evidence（已接受缺口证据） |
| Step2 | AIFI-BE-010 | DONE | effective feedback state（有效反馈状态）、旧 payload（载荷）兼容投影、Step2 commit `763ad98668535998bb7c16ad32e08d7bae1bc94a` | PASS |
| Step3 | AIFI-BE-011 | DONE | fail-closed validation（失败关闭校验）与失败投影 | PASS |
| Step4 | AIFI-BE-012 | DONE | same-answer stability（同答稳定性）、reference-answer replay（参考答案回放）、Step4 commit `2e82dbfbc8f23d0c09cd784a94190dceecc36732` | PASS |
| Step5 | AIFI-BE-015 | DONE | improved-answer trend calibration（改进回答趋势校准）、Step5 commit `ef95d4a9139d4c0f41593a6c9c57897d533aca0b` | PASS |
| Step6 | AIFI-BE-013 | DONE | progress mastery（进展掌握度）、longitudinal feedback summary（纵向反馈摘要）、Step6 commit `1bfa1cea0d213e01c00f20fda33971b68fac7996` | PASS |
| Step7 | AIFI-BE-014 | DONE | policy-signed follow-up / next-question contract（策略签名追问 / 下一题契约）；`127 passed in 13.04s` | PASS |
| Step8 | AIFI-BE-017 | DONE | API schema / response envelope boundary（接口结构 / 响应信封边界）、Step8 commit `23990da79118d200024735f193ba9b5d4499d4a2` | PASS |
| Step9 | AIFI-FE-003 | DONE | feedback view model（反馈视图模型）、failure folding（失败折叠）、Step9 commit `7f5f889` | PASS |
| Step10 | AIFI-FE-004 | DONE | workbench interaction（工作台交互）、refresh recovery（刷新恢复）、`npm.cmd run web:test`、web/action tests、backend regression、`npm.cmd run web:build` | PASS_WITH_RESIDUALS |
| Step11 | AIFI-QA-005 | DONE | red/green smoke、real page QA、enhanced real page QA、focused tests、review-work PASS、commits `9a97458`、`bd3c861`、`8a08cb9` | PASS_WITH_RESIDUALS |

## 2. Step1-Step10 Historical Command Evidence（历史命令证据）

以下命令和结果来自既有 closeout evidence（收口证据）与 active docs（当前有效文档）登记；本轮未重新运行这些测试，也不把历史 residual risk（残余风险）写成 resolved（已解决）。

| Step | 命令或证据 | 历史结果 | 残余风险 / 备注 |
|---|---|---|---|
| Step1 / AIFI-QA-004 | `PYTHONPATH=.:apps/api python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_acceptance_semantics.py -q` | `2 failed, 3 passed`；状态为 `ACCEPTED_RED` | RED（红灯）被接受为后续实现缺口证据，不是全量验收通过。 |
| Step2 / AIFI-BE-010 | `$env:PYTHONPATH=".;apps/api"; $env:PYTHONDONTWRITEBYTECODE="1"; $env:AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS="1"; python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_payload_compatibility.py tests/api/test_polish_effective_feedback_state.py -q` | `14 passed in 1.75s`；`py_compile` PASS；`git diff --check` PASS | 当时使用 `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1`；该环境口径不得扩大为后续步骤默认允许泄漏。 |
| Step3 / AIFI-BE-011 | `python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_failure_contract.py tests/api/test_polish_feedback_runtime.py -q` | `31 passed in 9.33s`；`py_compile` PASS；`git diff --check` PASS | 曾有 `FAIL_CHECK_ENV`，最终由 `step3-final-closeout.md` supersede（替代）为 PASS。 |
| Step4 / AIFI-BE-012 | `python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_generation_service.py -q` | `47 passed in 1.08s` | generation service suite（生成服务套件）是 Step4 硬 gate。 |
| Step4 / AIFI-BE-012 | Step1/Step4 semantic bundle（语义组合测试）、reference replay / prompt source matching（参考答案回放 / 提示词来源匹配）、Step2/Step3 bundle、API pending / idempotency（等待 / 幂等）节点 | `10 passed`、`20 passed`、`45 passed`、`4 passed`、`2 passed`；`py_compile` PASS；`git diff --check` PASS | `tests/api/test_polish_same_answer_stability.py` 当时不存在，按规则跳过；Windows pytest temp cleanup warning（临时目录清理警告）不影响退出码。 |
| Step5 / AIFI-BE-015 | improvement trend（改进趋势）、Step1/Step4 semantic bundle、generation service、payload/effective/failure/runtime bundle、same-key API node、optional `tests/api/test_polish_api.py -q` | `8 passed`、`30 passed`、`47 passed`、`45 passed`、`1 passed`、optional `120 passed` | pytest 在 Windows 用户临时目录清理时输出 `rm_rf` warning；所有相关命令退出码为 0。 |
| Step6 / AIFI-BE-013 | progress mastery、score evolution、longitudinal summary、complete question flow、Step5 trend、Step1/Step4 semantic bundle、generation service、payload/effective/failure/runtime bundle、API stuck / metadata / idempotency nodes | `2 passed`、`4 passed`、`2 passed`、`2 passed`、`8 passed`、`30 passed`、`47 passed`、`45 passed`、`3 passed`；`py_compile` PASS；`git diff --check` PASS | Python 3.14 / Pydantic v1 compatibility warning（兼容性警告）和 Windows temp cleanup warning 均记录为非阻断。 |
| Step7 / AIFI-BE-014 | `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python -m py_compile apps/api/app/application/polish/use_cases.py apps/api/app/application/polish/question_metadata.py apps/api/app/api/v1/polish.py apps/api/app/domain/polish/policies/follow_up_coverage_policy.py` | PASS | 只证明语法门禁，不授权 Step8、FE、migration、release 或 C-049 / C-054 关闭。 |
| Step7 / AIFI-BE-014 | focused Step7 API tests；`PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/domain/polish/test_follow_up_coverage_policy.py tests/api/test_polish_api.py -q` | `9 passed in 4.53s`；`127 passed in 13.04s`；`git diff --check` PASS；forbidden path diff 为空 | 完成 policy-signed follow-up / next-question contract（策略签名追问 / 下一题契约），不关闭 C-049 / C-054。 |
| Step8 / AIFI-BE-017 | Step8 focused RED / GREEN tests、contract optional fix、Step2-Step7 API canary、full `tests/api` canary | RED: `2 failed`；GREEN: `2 passed in 2.62s`；fix: `3 passed in 2.51s`；`211 passed in 23.01s`；supplemental `3 passed`、`279 passed`、full `1052 passed, 1 skipped, 1 warning` | full `tests/api` 后 Windows pytest garbage cleanup 留有目录；LSP diagnostics 返回 `Transport closed`；均不得写成已解决。 |
| Step9 / AIFI-FE-003 | `npm.cmd run web:test` RED / GREEN；single-file runtime compile（单文件运行时编译）；`node .omo/evidence/plan/step9-runtime-js/feedbackViewModel.test.js`；Step2-Step8 backend canary | RED: `npm.cmd run web:test` 按预期失败；GREEN: `npm.cmd run web:test` PASS；runtime JS PASS；backend canary `91 passed in 3.51s`；review supplemental `14 passed` / `91 passed`；`git diff --check` PASS | 只覆盖 `entities/polish` view model（视图模型）与 failure folding（失败折叠）；不授权 Step10 / Step11 / Step12。 |
| Step10 / AIFI-FE-004 | `npm.cmd run web:test` RED / GREEN；`python -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`；focused backend regression；`npm.cmd run web:build`；limited smoke attempt | RED: web:test FAIL as expected；GREEN: web:test PASS；`14 passed in 8.11s`；backend `77 passed in 4.68s`；web build PASS；limited smoke FAIL | limited smoke 在 browser assertions（浏览器断言）前失败：`failed answer should expose generation_failed payload`；该风险不得写成 Step11 QA PASS，已由 Step11 后续处理。 |

## 3. Step11 Command Evidence（命令证据）

| 命令或证据 | 结果 |
|---|---|
| `node scripts/qa/polish-feedback-frontend-smoke.mjs --scenario seeded-feedback-states --evidence-dir .omo/evidence/step11-polish-feedback-frontend-smoke-red` | FAIL reproduced（复现红灯）：`failed answer should expose generation_failed payload` |
| `node scripts/qa/polish-feedback-frontend-smoke.mjs --scenario seeded-feedback-states --evidence-dir .omo/evidence/step11-polish-feedback-frontend-smoke-green` | PASS；pending、generated、generation_failed 样本均返回 |
| `.omo/evidence/step11-real-page-qa/action-log.json` | PASS；覆盖 generated、pending、failure、follow-up surface、next action |
| `.omo/evidence/step11-real-page-qa-enhanced/action-log.json` | PASS；覆盖 partial、refresh recovery、trusted signed action、untrusted action |
| `tests/api/test_polish_api.py::test_get_polish_session_exposes_generation_failed_feedback_payload -q` | PASS，`1 passed in 2.71s` |
| `tests/api/test_polish_api.py::test_get_polish_session_exposes_partial_feedback_payload` | PASS |
| `tests/api/test_polish_effective_feedback_state.py::test_latest_failed_record_does_not_override_earlier_generated_effective_feedback` | PASS |
| `npm.cmd run web:test` | PASS |
| `python -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q` | PASS，`14 passed in 7.93s` |
| focused backend regression（聚焦后端回归） | PASS，`81 passed in 5.36s` |
| `npm.cmd run web:build` | PASS；保留 Vite chunk size warning（构建体积警告） |
| `git diff --check` | PASS；仅 LF/CRLF warning（换行提示） |

## 4. Coverage（覆盖面）

- generated feedback display（已生成反馈展示）：covered。
- pending feedback display（等待中反馈展示）：covered。
- generation_failed feedback display（生成失败反馈展示）：covered。
- partial feedback display（部分反馈展示）：covered。
- refresh recovery（刷新恢复）：covered。
- trusted signed action（可信签名动作）：covered。
- untrusted signed action（不可信签名动作）：covered。
- follow-up surface（追问入口展示）：covered。
- next action display（下一步动作展示）：covered。
- provider payload redaction（供应商载荷脱敏）：covered by sanitizer（安全投影）路径和 smoke（冒烟）证据。

## 5. Residual Evidence Gaps（残余证据缺口）

| 缺口 | 分类 | Step12 处理 |
|---|---|---|
| mobile 375 截图主要依赖 DOM 文本检查 | Accepted known risk | 进入 release checklist，生产前可人工复核 |
| action log 中 404 console error | Requires follow-up | 生产发布前需要 triage |
| Ant Design deprecated warning | Non-blocking tech debt | 记录为技术债 |
| Vite chunk size warning | Non-blocking tech debt | 生产前性能复核 |
| inherited large file issue（继承的大文件问题） | Maintainability debt（可维护性债务） | 不阻塞文档收口，不得扩大 |
| LSP diagnostics（语言服务诊断）`Transport closed` | Evidence gap（证据缺口） | 生产发布前需替代诊断或豁免 |

## 6. C-049 到 C-054 Guard（后置护栏）

本 QA evidence 不关闭或实现以下 Deferred / Open Question：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。
