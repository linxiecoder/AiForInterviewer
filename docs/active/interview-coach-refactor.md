---
title: Interview Coach Refactor G-001 Post-Merge Record
type: active-record
status: active-completed
updated: 2026-06-12
permalink: ai-for-interviewer/interview-coach-refactor
---

# Interview Coach Refactor G-001 Post-Merge Record

Status: Active / Completed

本文记录 PR #32 合入后的 G-001 最终状态。它是 `interview-coach` 启发式重构在 AiForInterviewer 仓库中的长期记录，不替代 `BACKLOG.md`、`DELIVERY_PLAN.md`、ADR 或代码事实。

## Background

G-001 只吸收 `interview-coach` 工作流中适合当前 Polish 工作台的两个方向：session continuity 与 context hygiene。实现已经合入 `main`，生产事实以当前代码、测试和 active docs 为准。

本记录替换旧的临时摘要口径；临时工作区已从本仓库移除。`interview-coach` 的 command system、menu、目录结构、prompt prose、workflow wording 和 source scoring vocabulary 未复制到 AiForInterviewer。

## Implemented Capabilities

### G-001 session continuity

现有 Polish session detail / refresh 响应可以携带向后兼容的可选 continuity metadata：

- `continuity_status`
- `continuity_summary`
- `restored_refs`

这些字段基于既有 session 状态、progress tree、turns、active question refs、evidence refs 和 context digest 计算，不新增 endpoint，不新增 DB migration。

### G-001 context hygiene

question / feedback metadata 统一输出有界且安全的 context hygiene contract：

- `context_hygiene_status`
- `safe_context_metadata`
- `fallback_reason`
- `validation_signals`

该 contract 只允许短 metadata、状态、fallback 与 validation signal，不暴露 raw prompt、provider payload、完整 source document 或敏感凭据。

### Final behavior

- Session detail 保持现有 API 路径与响应主体，只追加 optional metadata。
- Question generation 与 feedback generation 使用同一 context hygiene contract。
- Feedback application 会归一化已保存 metadata，legacy / malformed metadata 退化为 `unknown` 或带 fallback 的安全形态。
- 前端类型只接受 optional contract，不要求 UI 新增展示，也不改变现有工作台流程。

## Key Architecture Notes

### session continuity in application layer

`apps/api/app/application/polish/session_continuity.py` 承载 continuity 计算规则。API 层只组装 `SessionContinuitySnapshot` 并把 `compute_session_continuity(...).to_response_payload()` 合入响应，不在 router 中复制业务规则。

### context hygiene unified contract

`apps/api/app/application/polish/context_hygiene.py` 是统一 contract。它集中处理 status normalization、安全 JSON 裁剪、forbidden key 过滤和敏感文本 redaction。

### API layer mapping only

`apps/api/app/api/v1/polish.py` 只负责从既有 session detail 映射 snapshot 与 response payload。G-001 没有新增 endpoint，也没有把 context hygiene 或 continuity 变成新的命令入口。

### backend schema / frontend type optional contract

`apps/api/app/schemas/polish.py` 与 `apps/web/src/entities/polish/model/types.ts` 只登记 optional response/type contract。缺失这些字段的既有调用方仍可工作。

### no raw prompt/provider payload exposure

G-001 明确禁止 raw prompt、provider response、provider payload、full source、source document、API key、token、secret、cookie 等内容进入 `safe_context_metadata`。

## Key Changed Files

- `apps/api/app/application/polish/session_continuity.py`
- `apps/api/app/application/polish/context_hygiene.py`
- `apps/api/app/api/v1/polish.py`
- `apps/api/app/schemas/polish.py`
- `apps/api/app/application/polish/question_generation_service.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `apps/api/app/application/polish/feedback_application_service.py`
- `apps/api/app/application/polish/question_metadata.py`
- `apps/web/src/entities/polish/model/types.ts`
- `tests/api/test_polish_session_continuity.py`
- `tests/api/test_polish_context_hygiene.py`
- `tests/api/test_polish_api.py`
- `tests/api/test_polish_feedback_generation_service.py`
- `apps/web/src/pages/interview/InterviewPage.test.ts`

## Deferred Capabilities

G-002 remains draft / not implemented. It may cover capture / analysis separation in a separate authorized window, but this G-001 record does not implement it.

- storybank memory: deferred; no current model/API/UI/test landing point.
- transcript ingestion: deferred; no current transcript source model/API/UI/test landing point.
- outcome / progress calibration: deferred; no outcome log or drift lifecycle in this scope.
- command routing: rejected as source shape for production; no command system, command menu, or command prose was copied.
- external feedback taxonomy and root-cause scoring expansion: deferred; no change beyond existing safe metadata boundary.

## Validation Summary

| Area | Command | Round 7-A status |
| --- | --- | --- |
| Backend focused pytest / eval gate | `python -m pytest tests/evals -q` or `.venv/bin/python -m pytest tests/evals -q` | Initial chained command found `python` unavailable, then pytest passed 43 tests but local `tmp/` leak guard returned failure; rerun with `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/evals -q` passed 43 tests |
| Frontend type/test gate | `npm run web:test` | Passed; `tsc -p tsconfig.json --noEmit` completed |
| Frontend build gate | `npm run web:build` | Passed; `tsc -p tsconfig.json --noEmit && vite build` completed with existing chunk-size warning |

PR #32 already carried focused backend and frontend validation for G-001. Round 7-A re-ran the hygiene branch validation after removing the temporary workspace and updating this active record.

## Known Risks

- Repo-root `tmp/` may trigger the local tmp leak guard in pytest environments. If that happens, use `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest tests/evals -q` and report the guard condition.
- `AGENTS.md` remains unchanged in this hygiene round by instruction. It currently contains a managed `SPECKIT` marker while `.specify` is absent; owner should decide separately whether that marker is still desired.
- `.agents/skills/**` and `.claude/skills/**` contain retained AI skill assets. They are not required by G-001 production behavior and need a separate owner decision.

## Follow-up Work

- Decide whether retained `.agents` and `.claude` skill assets are long-term repository capabilities or should be removed in a separate cleanup PR.
- Decide whether the remaining `AGENTS.md` `SPECKIT` marker belongs in current governance.
- Start G-002 only after explicit scope approval.

## Main Hygiene Note

- `.codex-temp/interview-coach-refactor/` removed from the hygiene branch.
- `.specify` absent.
- Any retained `.agents/.claude` skill assets require separate owner decision if still present.
