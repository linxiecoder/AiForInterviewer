---
title: P3_W4_FINAL_REPORT
type: execution-evidence
status: evidence-only
owner: P3-W4-FEEDBACK-NEXT-ACTION-POLICY
permalink: ai-for-interviewer/docs/goals/2026-06-03/p3-w4-final-report
---

# P3-W4 Final Report

本文件记录 P3-W4 feedback next-action policy 抽取结果。它只作为 `docs/goals/**` 执行证据，不替代 active delivery 文档，不关闭 Phase 3，不改变 Phase 2 / SRC-001 / CTX-002 的 deferred gap 状态。

## 1. 结论

| 项 | 状态 | 说明 |
| --- | --- | --- |
| Window | `P3-W4` | Feedback next-action policy extraction |
| Capability IDs | `FAG-005`, `DDD-004` | next action / candidate confirmation / fail-closed policy |
| Result | `implemented_p3_w4` | `FeedbackNextActionPolicy` 已新增，`feedback_rules.py` 改为 next-action adapter |
| External behavior | `preserved_by_regression_tests` | 旧 `next_recommended_actions` 字符串和 payload shape 保持兼容 |
| Deferred gaps | `still_open` | Phase 2 closeout evidence、SRC-001、CTX-002 / `SourceSupportSummary`、P3-W1 partial 均未关闭 |

## 2. 代码变更

| 文件 | 变更 |
| --- | --- |
| `apps/api/app/domain/polish/policies/feedback_next_action_policy.py` | 新增纯 domain policy；编码 asset conflict 阻断、unresolved coverage / regression 阻断、asset update candidate confirmation、formal write deny、provider/validation fail-closed、low-confidence / missing-context reason codes。 |
| `apps/api/app/domain/polish/policies/__init__.py` | 导出 P3-W4 policy input / decision / outcome 类型。 |
| `apps/api/app/application/polish/feedback_rules.py` | `_next_recommended_actions()` 改为 adapter，组装 `FeedbackNextActionInput` 并回填 legacy actions list。 |
| `tests/domain/polish/test_feedback_next_action_policy.py` | 新增 next-action policy 单测。 |
| `tests/api/test_polish_feedback_generation_service.py` | 新增 `next_action` API 回归，确认 answer regression 移除 `generate_next_question` 并优先 retry same question。 |

## 3. Scope Audit

| 边界 | 结果 |
| --- | --- |
| Prompt assets | 未修改 `feedback_prompt_assets.py` 或 `question_generation_prompts.py`。 |
| Provider / AI runtime | 未修改 `application/ai_provider/**`、provider SDK、LLM transport 或 Agent runtime。 |
| Infrastructure / DB / API | 未修改 `infrastructure/**`、DB schema、migration、API route / schema。 |
| Validation schema | 未修改 `feedback_validation.py`；既有 validator 继续拒绝 unsafe next question 和 candidate formal-write leakage。 |
| Failed payload in `use_cases.py` | 未修改；P3-W4 边界审计判定该路径不在 allowed files 内，且当前失败 task/status 不表示 generated success。 |
| Frontend | 未修改。 |
| CTX-002 / SourceSupportSummary | 未修复、未标记完成。 |

## 4. Multi-Agent Notes

| Agent | 状态 | 结论 |
| --- | --- | --- |
| Raman / Recon | `completed` | P3-W4 可通过新增 policy + `feedback_rules.py` adapter 完成；service/application delegate 无需改。 |
| Banach / Boundary | `completed` | Allowed files 足够；失败 payload 若要去掉 `generate_next_question` 需要扩窗到 `use_cases.py`，本窗不做。 |
| Fermat / Policy Design | `timed_out_then_shutdown` | 未在实现前返回；本地设计按 Recon / Boundary 交叉结论和窗口要求完成。 |

## 5. Validation Evidence

| 命令 | 结果 |
| --- | --- |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/domain/polish/test_feedback_next_action_policy.py -q` | `7 passed in 0.14s` |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m compileall apps/api/app/domain/polish apps/api/app/application/polish` | Pass |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/api -k "feedback and next_action" -q` | `1 passed, 620 deselected in 7.76s` |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/api -k "asset_consistency or answer_coverage or answer_change or next_action" -q` | `2 passed, 619 deselected in 7.63s` |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/api -k "feedback and polish" -q` | `84 passed, 537 deselected in 20.06s` |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/architecture -q` | `22 passed, 2 xfailed in 0.59s`; xfail 仍为既有 P1-W3 provider sanitizer known gap |
| `rg -n "from app\.infrastructure|import app\.infrastructure|FastAPI|sqlalchemy|Session\(|openai|anthropic|LLM|Prompt|prompt|provider|uvicorn|requests|httpx" apps/api/app/domain/polish/policies/feedback_next_action_policy.py` | No matches |

## 6. Non-Claims

本窗口不声明以下事项：

- 不声明 Phase 2 closeout evidence 已补齐。
- 不声明 SRC-001 已完成。
- 不声明 CTX-002 或完整 `SourceSupportSummary` 契约已完成。
- 不声明 P3-W1 从 `partial_with_deferred_gap` 升级为完成状态。
- 不声明 P3-W5 bridge / boundary hardening 已完成。
- 不声明 Phase 3 可以 final closeout。

## 7. Remaining Work

| 项 | 状态 | 下一步 |
| --- | --- | --- |
| P3-W5 bridge / boundary strengthening | `not_started_after_p3_w4` | 补强 adapter / boundary drift tests，确认 application modules 调用 policies 且无残留策略逻辑漂移。 |
| P3-W6 closeout | `blocked_by_p3_w5_and_deferred_gaps` | 需要 P3-W5 证据，并处理或显式接受 Phase 2 / SRC-001 / CTX-002 deferred gaps。 |
