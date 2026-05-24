---
title: Candidate Skill Training Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构 / 产品设计
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/candidate-skill-training-package
---

# Candidate Skill Training Package

## 1. Package 目标

本 package 冻结 candidate、Skill / Capability、Weakness、Asset、Training suggestion 和 confirmation interrupt 的 implementation plan。它确保 AI graph 只生成 candidate / suggestion，正式对象只能来自用户确认或显式 Core API。

## 2. Candidate schema

| Field | Required | Rule |
|---|---|---|
| `candidate_id` | yes | stable candidate id, owner scoped |
| `candidate_type` | yes | weakness, asset, training suggestion or registered subtype |
| `status` | yes | candidate, needs_confirmation, merge_suggested, low_confidence, confirmed, dismissed, merged, archived, rejected, skipped |
| `owner_id` | yes | every action verifies owner |
| `source_type` | yes | job_match, polish_feedback, report, mock_review, real_review, training_result |
| `source_refs[]` | yes | authorized refs only; no raw source body |
| `evidence_refs[]` | optional | evidence refs or redacted summaries |
| `trace_refs[]` | yes | sanitized trace refs |
| `title`, `summary`, `evidence_excerpt` | yes | redacted display fields |
| `confidence_level` | yes | high, medium, low |
| `merge_key` | yes | owner-scoped normalized duplicate key |
| `target_formal_ref` | optional | null until Core formal write succeeds |
| `candidate_payload` | yes | safe subset; `formal_write_intent=false` until confirmation |
| `base_candidate_version_ref` | yes | stale action protection |

## 3. Confirmation interrupt schema

| Field | Required | Rule |
|---|---|---|
| `interrupt_id` | yes | runtime resume id, not business truth |
| `candidate_ref` | yes | candidate being reviewed |
| `candidate_type` | yes | drives validation and target command |
| `source_refs[]` | yes | displayable refs only |
| `evidence_summary` | yes | redacted drawer summary |
| `confidence_flags[]` | optional | low confidence / source unavailable |
| `allowed_actions[]` | yes | confirm, edit, merge, reject, skip, request_more_evidence |
| `base_candidate_version_ref` | yes | stale action protection |
| `edited_payload_ref` | optional | required for edit |
| `target_formal_ref` | optional | required for merge/update |
| `audit_event_ref` | optional | set after action accepted |
| `formal_write_result_ref` | optional | set only after Core command commits |

## 4. Skill mapping rules

| Source object | Skill relation | Rule |
|---|---|---|
| Job Match gap | `SkillEvidence` candidate | no formal Skill object in PR2; graph outputs evidence-bound candidate refs |
| Polish feedback loss point | `SkillGap` candidate | weakness remains candidate until confirmation |
| Review insight | `SkillAssessment` candidate | no exact real interview outcome prediction |
| Training suggestion | `TrainingRecommendation` candidate | no `TrainingTask` until explicit user action |
| Progress tree node | `SkillToQuestionPattern` candidate | progress tree is not Skill source of truth |

## 5. Graph scope

| Graph | Target | PR |
|---|---|---:|
| `weakness_candidate_graph` | extract weakness candidates and merge suggestions | PR8 |
| `asset_candidate_graph` | extract asset candidates and version suggestions | PR8 |
| `training_suggestion_graph` | generate training recommendation candidates | PR8 |
| `candidate_confirmation_interrupt_graph` | confirmation interrupt / resume / formal write handoff | PR8 |

## 6. Candidate graph node plan

| Graph | Node | Inputs | Outputs | Side effects | Idempotency key | Tests |
|---|---|---|---|---|---|---|
| weakness | `load_weakness_sources` | owner/source refs | compact sources | read only | `weakness_candidate:{owner_id}:{source_hash}:load` | owner/source |
| weakness | `build_weakness_context` | compact sources, existing weaknesses | context bundle | none | `weakness_candidate:{source_hash}:context` | compact only |
| weakness | `extract_weakness_candidates` | context | candidate drafts | optional LLM candidate-only | `weakness_candidate:{context_hash}:extract` | no formal write |
| weakness | `suggest_weakness_merge` | drafts, existing weakness refs | merge suggestions | none | `weakness_candidate:{owner_id}:{merge_key}:merge-suggest` | duplicate owner-scoped |
| weakness | `assess_weakness_severity` | candidates and evidence | severity refs | optional LLM | `weakness_candidate:{candidate_hash}:severity` | severity unknown -> low confidence |
| weakness | `weakness_candidate_quality_gate` | candidates | accepted candidates | none | `weakness_candidate:{candidate_hash}:gate` | raw payload sanitizer |
| weakness | `persist_weakness_candidates` | accepted candidates | candidate refs | upsert candidates only | `weakness_candidates:{owner_id}:{candidate_hash}` | target formal ref null |
| asset | `load_asset_sources` | owner/source refs | compact sources | read only | `asset_candidate:{owner_id}:{source_hash}:load` | owner/source |
| asset | `build_asset_context` | compact sources, existing assets | context | none | `asset_candidate:{source_hash}:context` | no raw source |
| asset | `extract_asset_candidates` | context | asset/oral/polished drafts | optional LLM | `asset_candidate:{context_hash}:extract` | no formal Asset |
| asset | `suggest_asset_version_update` | drafts, existing assets | version suggestions | none | `asset_candidate:{owner_id}:{merge_key}:version` | merge/version policy |
| asset | `asset_quality_gate` | drafts/suggestions | accepted candidates | none | `asset_candidate:{candidate_hash}:gate` | user fact insufficient |
| asset | `persist_asset_candidates` | accepted candidates | candidate refs | upsert candidates only | `asset_candidates:{owner_id}:{candidate_hash}` | target formal ref null |
| training | `load_training_sources` | confirmed weakness refs, asset refs, score trends | compact context refs | read only | `training_suggestion:{owner_id}:{source_hash}:load` | confirmed weakness required |
| training | `build_training_context` | source refs | context bundle | none | `training_suggestion:{source_hash}:context` | compact only |
| training | `generate_training_suggestions` | context | suggestion candidates | optional LLM | `training_suggestion:{context_hash}:generate` | no TrainingTask |
| training | `rank_training_priorities` | suggestions, score trends | priority ranking | none or authorized LLM | `training_suggestion:{candidate_hash}:rank` | priority ranking |
| training | `training_suggestion_quality_gate` | suggestions/ranking | accepted suggestions | none | `training_suggestion:{candidate_hash}:gate` | no formal write |
| training | `persist_training_suggestions` | accepted suggestions | candidate refs | recommendation candidates only | `training_suggestions:{owner_id}:{candidate_hash}` | no auto TrainingTask |

## 7. Confirmation graph node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Tests |
|---|---|---|---|---|---|
| `prepare_confirmation_interrupt` | candidate ref, actor | interrupt payload | write runtime interrupt | `candidate_interrupt:{owner_id}:{candidate_id}:{version_ref}` | drawer payload |
| `sanitize_candidate_for_drawer` | candidate | drawer schema | none | `candidate_drawer:{candidate_id}:{version_ref}` | no raw prompt/provider |
| `interrupt_wait_user_action` | drawer schema | user action | runtime wait only | `candidate_interrupt:{interrupt_id}:wait` | pause/resume |
| `resume_with_user_action` | action payload | normalized action | none | `candidate_interrupt:{interrupt_id}:resume:{action_hash}` | stale action |
| `validate_confirmation_owner_and_version` | candidate ref, version ref, actor | valid action scope | none | `candidate_confirm:{owner_id}:{candidate_id}:{version_ref}:validate` | owner isolation |
| `validate_edited_candidate` | edited payload | corrected candidate | none | `candidate_confirm:{candidate_id}:{edited_hash}:edit-validate` | edit validation |
| `call_core_formal_write_command` | action, candidate, target formal ref | formal write result | Core command writes formal object only after confirmation | `formal_write:{owner_id}:{candidate_id}:{action}:{version_ref}` | confirm creates formal refs; rollback |
| `write_user_confirmation_ref` | action and before/after summary | confirmation ref | write user confirmation | `user_confirmation:{owner_id}:{candidate_id}:{action}:{version_ref}` | skip/reject no formal |
| `write_audit_event` | action/result/confirmation ref | audit ref | write sanitized audit event | `audit:candidate:{owner_id}:{candidate_id}:{action}:{version_ref}` | audit required |
| `rollback_on_failed_formal_write` | failed formal write | rollback result | transaction rollback/status restore | `rollback:{owner_id}:{candidate_id}:{version_ref}` | candidate status restored |
| `publish_confirmation_result` | final refs | result response | none | `candidate_result:{owner_id}:{candidate_id}:{action}:{version_ref}` | no raw payload |

## 8. Formal write handoff

Formal write 只允许通过 `call_core_formal_write_command` 执行，并且必须先校验 owner、actor、candidate status 和 `base_candidate_version_ref`。

| Action | Formal write | Audit |
|---|---|---|
| confirm | yes, via Core command | required |
| edit | yes, after edited payload validation | required |
| merge into formal target | yes, via Core update command | required |
| merge candidate-only | no formal write | required |
| reject | no | required |
| skip | no | required |
| request_more_evidence | no | required |

## 9. Duplicate / merge policy

- `merge_key` includes owner, candidate type, normalized title / summary / evidence dimensions and source category.
- Duplicate candidate in one owner becomes `merge_suggested` or points to `merge_target_candidate_id`; it never auto-confirms.
- Merge into formal object requires `target_formal_ref` and explicit user action.
- Low confidence duplicate evidence yields manual check.

## 10. Tests

| Test area | Assertions |
|---|---|
| candidate schema | safe fields, owner-scoped source refs, no raw payload |
| duplicate merge | owner-scoped merge key, no auto-confirm |
| confirmation | confirm/edit/merge/reject/skip behaviors and audit |
| formal write | formal refs created only after user action; rollback on failure |
| training | training recommendation candidate does not create TrainingTask |
| Skill | no temporary Skill key; progress tree is not Skill source of truth |

## 11. Non-goals

- 不做 PR2 implementation。
- No automatic TrainingTask creation.
- No complex semantic merge algorithm beyond owner-scoped deterministic merge key.
- No formal object write from graph replay.
