---
title: 06_FEEDBACK_AGENT_SPEC
type: note
permalink: ai-for-interviewer/docs/project-sources/06-feedback-agent-spec
---

# 06 Feedback Agent Spec

agent_id: polish_feedback_agent
current_maturity: L1.5-L2
target_maturity_short_term: L2 planned guarded workflow
target_runtime_phase: Phase 6   # Feedback

## Mission
基于当前题目、当前回答、标准期待点、资产事实、同题历史回答和训练目标，生成可信、可行动、可复盘的结构化反馈。

## Non-Goals
不得直接写正式资产、不得直接确认资产更新、资产冲突时不得推进下一题、不得把当前回答新事实直接视为真实事实、不得绕过 domain policy。

## Skills
FAG-SKILL-001 ExpectedPointBuildingSkill
FAG-SKILL-002 AssetConsistencyReviewSkill
FAG-SKILL-003 AnswerCoverageReviewSkill
FAG-SKILL-004 SameQuestionChangeReviewSkill
FAG-SKILL-005 ScoringSkill
FAG-SKILL-006 LossPointExtractionSkill
FAG-SKILL-007 ReferenceAnswerPlanningSkill
FAG-SKILL-008 FeedbackCardCompositionSkill
FAG-SKILL-009 NextActionPlanningSkill
FAG-SKILL-010 AssetCandidateProposalSkill

## Tools
get_canonical_evidence_pack、get_question_expected_points、get_same_question_attempts、check_asset_consistency、calculate_answer_coverage、compare_answer_attempts、compose_feedback_cards、validate_next_actions、propose_asset_candidates。

## Planned Workflow
Load evidence -> build expected points -> LLM candidate -> asset consistency policy -> coverage policy -> answer change policy -> next action policy -> card policy -> validate -> persist generated / failed / low confidence。