---
title: F4 Full Design Remediation Matrix
type: review
status: active-f4
source_task: AIFI-ARCH-004
permalink: ai-for-interviewer/design/reviews/f4-full-design-remediation-matrix
---

# F4 全量技术设计整改矩阵

## 1. 使用边界

本矩阵描述 `AIFI-ARCH-004` 的建议整改动作，并在后续授权 remediation 中记录实际回写结果。所有整改必须在授权轮次回写到对应 active docs；本文件不替代 `TECH_DESIGN.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `prompt-contracts/*.md`。

## 2. Remediation Matrix

| Finding | Target Active Doc | Required Change | Verification Method | Blocks F4 Exit | Blocks F5 | Blocks F7 | Status |
|---|---|---|---|---|---|---|---|
| AR-F4-FULL-001 | `TECH_DESIGN.md`; `DATA_MODEL.md`; `API_SPEC.md`; `PROMPT_SPEC.md`; `SECURITY_PRIVACY.md`; `BACKLOG.md` | 逐项梳理 `F4_TECH_DESIGN` UNKNOWN，关闭、Deferred 或 Accepted Risk；更新 `AIFI-ARCH-002` 事实状态 | `rg -n "F4_TECH_DESIGN|UNKNOWN|DM-UNK|Open Questions"`；F7 UNKNOWN closure fixture | Yes | Yes | Yes | Open |
| AR-F4-FULL-002 | `API_SPEC.md`; `TECH_DESIGN.md`; `SECURITY_PRIVACY.md` | 补齐 endpoint、method、path、request / response、error code、auth / owner、pagination / sorting / filtering、status query、async / sync、retry、idempotency、timeout、rate limit；同步 API handoff 当前性 | API contract review；targeted F7 API tests for auth/owner/failure/retry/rate limit/source unavailable/low confidence/no export/copy boundary | No | No | No | Verified |
| AR-F4-FULL-003 | `TECH_DESIGN.md`; `PROMPT_SPEC.md`; `DATA_MODEL.md`; `API_SPEC.md`; `JOB_MATCH_CONTRACTS.md`; `PRESSURE_CONTRACTS.md`; `REPORT_CONTRACTS.md` | 冻结最小评分规则版本、risk wording、低置信触发、免责声明和禁止表达；明确是否采用固定公式或 rubric / rule version | Fixture 覆盖 score range、score_rule_unknown、low confidence、risk wording、no exact pass probability | Yes | Yes | Yes | Open |
| AR-F4-FULL-004 | `REPORT_CONTRACTS.md`; `API_SPEC.md`; `PROMPT_SPEC.md`（只读核对，无需改动）; `SECURITY_PRIVACY.md`（只读核对，无需改动） | 删除 / 改写 `download_markdown`、`MarkdownExportSnapshot`、`download_filename_hint`、download / export 语义；收敛为页面复制；API 只保留读取和复制内容边界 | `rg -n "download|export|下载|导出|filename|MarkdownExport"` active docs；F7 no file export test | No | No | No | Verified |
| AR-F4-FULL-005 | `DATA_MODEL.md`; `API_SPEC.md`; `PROMPT_SPEC.md`; `SHARED_CONTRACTS.md`; `PRESSURE_CONTRACTS.md` | 冻结 pause / resume 最小快照、进展树状态机、status query、cancel、retry、timeout、partial result 和 source unavailable 恢复路径 | State-machine fixture 覆盖 pause/resume/resume failed/timeout/partial/source unavailable | No | No | Yes | Open |
| AR-F4-FULL-006 | `DELIVERY_PLAN.md`; `UI_DESIGN_SYSTEM.md`; F6 task handoff docs if authorized | 统一 F3 DONE 与 UI 高保真 UNKNOWN / NOT_STARTED 的口径；明确 F6 使用哪些 approved design input | `rg -n "F3 |UNKNOWN|NOT_STARTED|APPROVED"`；人工设计交接复核 | No | No | Yes | Open |
| AR-F4-FULL-007 | `REPORT_CONTRACTS.md`; `REVIEW_CONTRACTS.md`; `WEAKNESS_CONTRACTS.md`; `ASSET_CONTRACTS.md`; `PROMPT_SPEC.md` | 更新过期的“仍保持 Stub”关系说明，与当前 Draft registry 对齐，同时保留 UNKNOWN / non-write 边界 | `rg -n "仍保持 Stub|仍是 Stub|保持 Stub"`；Prompt registry / child status diff | No | No | No | Open |

## 3. Suggested Remediation Order

1. P0: `AR-F4-FULL-004` 已在本轮 Verified，后续只需在 F5 / F7 按 no file export test 回归。
2. P0: `AR-F4-FULL-002` 已 Verified；后续 F5 / F7 只需按 API contract tests 防止实现偏离。
3. P0: 统一评分、风险提示和通过倾向的最小可测口径。
4. P0: 执行 `AIFI-ARCH-002`，逐项关闭或处置 `F4_TECH_DESIGN` UNKNOWN。
5. P1: 冻结进展树、暂停恢复和异步失败状态机。
6. P1: 统一 F3 / F6 设计交接状态。
7. P2: 清理 prompt-contract 子文档中过期的 Stub 关系说明。

## 3.1 Actual Remediation Record

| Finding | Target Active Doc | Required Change | Actual Change | Verification Method | Status |
|---|---|---|---|---|---|
| AR-F4-FULL-002 | `API_SPEC.md`; `TECH_DESIGN.md`; `SECURITY_PRIVACY.md` | 将 `API_SPEC.md` 从骨架补齐为 F5/F6/F7 可交接 API contract；必要时同步 API handoff 当前性 | `API_SPEC.md` 已补齐全局 API 约定、response / error envelope、pagination / sorting / filtering、idempotency、rate limit、trace / request id、async task protocol、AI task create / status / result / retry / cancel、核心 endpoint matrix、candidate / suggestion / confirmation 写入边界、报告 copy content 与 no export 边界、F7 可测试性矩阵。`TECH_DESIGN.md` 已同步 API handoff 当前性，不再说完整 endpoint / retry / idempotency 仍未收敛。`SECURITY_PRIVACY.md` 已同步 endpoint / API schema 由 `API_SPEC.md` 承接，本文不重复定义。未修改 `PROMPT_SPEC.md` 或 prompt-contracts 正文。 | 本轮 verification 已确认：`API_SPEC.md` 不再自称骨架或 endpoint 未定义；endpoint matrix 覆盖核心资源域；F7 assertion 覆盖 success、validation failed、cross-user、source unavailable、low confidence、generation failed、idempotent retry、stale conflict、no export endpoint、copy boundary；`TECH_DESIGN.md` / `SECURITY_PRIVACY.md` 无 API handoff 旧口径；禁止路径无变更。 | Verified |
| AR-F4-FULL-004 | `REPORT_CONTRACTS.md`; `API_SPEC.md` | 将 Report contract 的 Markdown 下载 / 文件产物语义收敛为报告内容复制 / copy content；API 不提供下载 / 导出 endpoint | `REPORT_CONTRACTS.md` 已移除公共 action 和 `P-REPORT-004` 中的文件生成动作、下载快照、文件名 hint、复制 / 下载混合校验和测试语义，改为剪贴板可用内容；已明确复制内容不得包含 `system prompt`、provider payload、隐藏评分规则和未经脱敏的第三方 / 公司 / 个人敏感信息。`API_SPEC.md` 已补充报告 API 只提供报告读取、报告分项读取和复制所需内容，不提供文件下载 / 导出 endpoint。 | `REPORT_CONTRACTS.md` 对 `download|export|下载|导出|filename|MarkdownExport` 无命中；`API_SPEC.md` 命中为“不提供下载 / 导出 endpoint”禁止说明；`SECURITY_PRIVACY.md` 命中为页面复制、Deferred 或 non-goal 边界；未发现 archive、snapshot file、report file、markdown artifact 或 downloadable content 等替代导出命名。 | Verified |

## 4. 不建议整改方式

- 不建议在 review 文件中补写 active design truth。
- 不建议让 F5 自行发明 API schema、错误码、评分阈值或导出策略。
- 不建议把旧 `AIFI-ARCH-003` finding 直接复制成新结论。
- 不建议用 archive 或 Figma 候选稿替代 active docs 事实。
