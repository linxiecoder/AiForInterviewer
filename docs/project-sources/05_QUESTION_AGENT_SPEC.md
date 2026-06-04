---
title: 05_QUESTION_AGENT_SPEC
type: note
permalink: ai-for-interviewer/docs/project-sources/05-question-agent-spec
---

# 05 Question Agent Spec

agent_id: polish_question_agent
current_maturity: L1.5-L2
target_maturity_short_term: L2 planned guarded workflow
target_runtime_phase: Phase 5   # Question

## Mission
基于岗位、简历、进展树、历史回答、历史反馈、资产事实和训练目标，生成下一道最有价值、事实可追踪、可评分、可追问的问题。

## Non-Goals
不得写正式题目、不得编造项目事实、不得把岗位要求改写成候选人经历、不得无证据引入技术栈、不得把 deterministic fallback 当成功。

## Skills
QAG-SKILL-001 SourceSupportClassificationSkill
QAG-SKILL-002 QuestionIntentPlanningSkill
QAG-SKILL-003 QuestionKindSelectionSkill
QAG-SKILL-004 EvidenceGroundingSkill
QAG-SKILL-005 FollowUpCoverageSkill
QAG-SKILL-006 AntiRepetitionSkill
QAG-SKILL-007 ExpectedPointDraftingSkill
QAG-SKILL-008 RubricDraftingSkill

## Tools
get_canonical_evidence_pack、get_progress_node、get_prior_questions、get_prior_feedback、get_same_focus_history、classify_source_support、validate_question_grounding、evaluate_follow_up_coverage。

## Planned Workflow
Load context -> classify source support -> plan intent -> select kind -> build compact request -> generate candidate -> grounding policy -> follow-up coverage policy -> finalize generated / clarification / blocked / failed。