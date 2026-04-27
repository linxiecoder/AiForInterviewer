# Doc Governor 解释性治理报告

## 摘要

- requirements_review_required: 1
- modules_review_required: 10
- subtasks_review_required: 2
- documents_review_required: 1
- requirements_blocked_count: 0
- modules_blocked_count: 1
- subtasks_blocked_count: 25
- documents_blocked_count: 0
- rounds_open_count: 0
- rounds_in_progress_count: 0
- rounds_review_count: 0
- blocked_by_reason_code:
  - acceptance_criteria_missing: 25
  - formal_window_closed: 25
  - implementation_doc_not_active: 25
  - implementation_scope_unclear: 25
  - missing_required_doc_slot: 42
  - required_tests_missing: 25
  - template_like_required_doc_slot: 14
  - upstream_module_not_ready: 6
- oq_gate_counts:
  - observe_only.clear: 0
  - observe_only.review_only: 25
  - candidate_gate.clear: 0
  - candidate_gate.review_only: 0
  - candidate_gate.candidate_blocker: 0
  - readiness_gate.clear: 0
  - readiness_gate.review_only: 0
  - readiness_gate.readiness_blocker: 0

## 需求主链

### 计数
- requirement_entries: 1
- requirements_review_required: 1
- requirements_blocked_count: 0
- modules_missing_requirement_relation: 0
- modules_ambiguous_requirement_relation: 0
- subtasks_missing_requirement_relation: 0
- subtasks_ambiguous_requirement_relation: 0
- modules_relation_consistency_errors: 0
- modules_relation_consistency_warnings: 0
- subtasks_relation_consistency_errors: 0
- subtasks_relation_consistency_warnings: 0

### 关联总览

- `RQ01`: gate=pass review_required=true modules=[M01, M02, M03, M04, M05, M06, M07, M08, M09, M10] tasks=[ST13_01, ST13_02, ST13_03, ST13_04, ST13_05, ST13_06, ST13_07, ST13_08, ST13_09, ST13_10, ST13_11, ST13_12, ST13_13, ST13_14, ST13_15, ST13_16, ST13_17, ST13_18, ST13_19, ST13_20, ST13_21, ST13_22, ST13_23, ST13_24, ST13_25] blockers=[]

### 关联告警

- 无

## 需评审模块

- `M01`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M02`: review_required=true reason=[oq_review_only]
- `M03`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M04`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M05`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M06`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M07`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M08`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M09`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]
- `M10`: review_required=true reason=[downstream_ready_no_hard_blocker, oq_review_only]

## 需评审子任务

- `ST13_24`: review_required=true reason=[downstream_ready_no_hard_blocker]
- `ST13_25`: review_required=true reason=[downstream_ready_no_hard_blocker]

## 需评审文档

- `DOC-PLAN-CURRENT-REPO-2026-04-25`: review_required=true reason=[document_ready_for_review]

## 子任务 gate 摘要

- `ST13_01`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:api, doc:design_doc, doc:implementation_doc, doc:open_questions, gate:acceptance_criteria_missing] next_actions=[补齐 acceptance_criteria]
- `ST13_02`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:api, doc:design_doc, doc:implementation_doc, doc:open_questions, gate:acceptance_criteria_missing] next_actions=[补齐 acceptance_criteria]
- `ST13_03`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_04`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_05`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:api, doc:design_doc, doc:implementation_doc, doc:open_questions, gate:acceptance_criteria_missing] next_actions=[补齐 acceptance_criteria]
- `ST13_06`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_07`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_08`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_09`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_10`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_11`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_12`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_13`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_14`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_15`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_16`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_17`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_18`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_19`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_20`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:api, doc:open_questions, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_21`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:api, doc:open_questions, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_22`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:design_doc, doc:implementation_doc, gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths]
- `ST13_23`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=false,state=none,effect=state_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[doc:api, doc:design_doc, doc:implementation_doc, doc:open_questions, gate:acceptance_criteria_missing] next_actions=[补齐 acceptance_criteria]
- `ST13_24`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=true,state=document_layer_recommended,effect=facts_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear, gate:required_tests_missing, policy:formal_window_closed] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths, 补齐 required_tests, 先通过 preflight/open-window 链路确认 formal window]
- `ST13_25`: gate_result=blocked can_open_formal_window=false can_generate_implementation_packet=false can_mark_implementation_ready=false candidate=recommended=true,state=document_layer_recommended,effect=facts_only,means_formal_window_open=false,means_packet_ready=false near_ready=enabled=false,state=none,means_candidate_status_candidate=false top_blockers=[gate:acceptance_criteria_missing, gate:implementation_doc_not_active, gate:implementation_scope_unclear, gate:required_tests_missing, policy:formal_window_closed] next_actions=[补齐 acceptance_criteria, 评审后激活 implementation_doc_state, 补齐 goal/allowed_modify_paths/forbidden_paths, 补齐 required_tests, 先通过 preflight/open-window 链路确认 formal window]

## 按层级汇总的 candidate blockers

### 模块

- 无
### 子任务

- 无

## 按层级汇总的 downstream blockers

### 模块

- [module:M02] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [module:M02] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
### 子任务

- [subtask:ST13_01] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_01 required slot design_doc is missing
- [subtask:ST13_02] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_02 required slot design_doc is missing
- [subtask:ST13_03] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_03 required slot design_doc is missing
- [subtask:ST13_04] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_04 required slot design_doc is missing
- [subtask:ST13_05] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_05 required slot design_doc is missing
- [subtask:ST13_06] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_06 required slot design_doc is missing
- [subtask:ST13_07] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_07 required slot design_doc is missing
- [subtask:ST13_08] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_08 required slot design_doc is missing
- [subtask:ST13_09] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_09 required slot design_doc is missing
- [subtask:ST13_10] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_10 required slot design_doc is missing
- [subtask:ST13_11] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_11 required slot design_doc is missing
- [subtask:ST13_12] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_12 required slot design_doc is missing
- [subtask:ST13_13] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_13 required slot design_doc is missing
- [subtask:ST13_14] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_14 required slot design_doc is missing
- [subtask:ST13_15] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_15 required slot design_doc is missing
- [subtask:ST13_16] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_16 required slot design_doc is missing
- [subtask:ST13_17] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_17 required slot design_doc is missing
- [subtask:ST13_18] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_18 required slot design_doc is missing
- [subtask:ST13_19] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_19 required slot design_doc is missing
- [subtask:ST13_22] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_22 required slot design_doc is missing
- [subtask:ST13_23] reason_code=missing_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST13_23 required slot design_doc is missing
- [subtask:ST13_01] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_01 required slot implementation_doc is missing
- [subtask:ST13_02] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_02 required slot implementation_doc is missing
- [subtask:ST13_03] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_03 required slot implementation_doc is missing
- [subtask:ST13_04] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_04 required slot implementation_doc is missing
- [subtask:ST13_05] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_05 required slot implementation_doc is missing
- [subtask:ST13_06] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_06 required slot implementation_doc is missing
- [subtask:ST13_07] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_07 required slot implementation_doc is missing
- [subtask:ST13_08] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_08 required slot implementation_doc is missing
- [subtask:ST13_09] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_09 required slot implementation_doc is missing
- [subtask:ST13_10] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_10 required slot implementation_doc is missing
- [subtask:ST13_11] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_11 required slot implementation_doc is missing
- [subtask:ST13_12] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_12 required slot implementation_doc is missing
- [subtask:ST13_13] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_13 required slot implementation_doc is missing
- [subtask:ST13_14] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_14 required slot implementation_doc is missing
- [subtask:ST13_15] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_15 required slot implementation_doc is missing
- [subtask:ST13_16] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_16 required slot implementation_doc is missing
- [subtask:ST13_17] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_17 required slot implementation_doc is missing
- [subtask:ST13_18] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_18 required slot implementation_doc is missing
- [subtask:ST13_19] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_19 required slot implementation_doc is missing
- [subtask:ST13_22] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_22 required slot implementation_doc is missing
- [subtask:ST13_23] reason_code=missing_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST13_23 required slot implementation_doc is missing
- [subtask:ST13_01] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [subtask:ST13_02] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [subtask:ST13_05] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [subtask:ST13_20] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [subtask:ST13_21] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [subtask:ST13_23] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [subtask:ST13_01] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
- [subtask:ST13_02] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
- [subtask:ST13_05] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
- [subtask:ST13_20] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
- [subtask:ST13_21] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
- [subtask:ST13_23] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
- [subtask:ST13_01] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST13_01 upstream module M02 is not downstream ready
- [subtask:ST13_02] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST13_02 upstream module M02 is not downstream ready
- [subtask:ST13_05] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST13_05 upstream module M02 is not downstream ready
- [subtask:ST13_20] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST13_20 upstream module M02 is not downstream ready
- [subtask:ST13_21] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST13_21 upstream module M02 is not downstream ready
- [subtask:ST13_23] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST13_23 upstream module M02 is not downstream ready

## 按层级汇总的 implementation blockers

### 子任务

- [subtask:ST13_01] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_01 implementation doc is missing acceptance criteria
- [subtask:ST13_02] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_02 implementation doc is missing acceptance criteria
- [subtask:ST13_03] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_03 implementation doc is missing acceptance criteria
- [subtask:ST13_04] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_04 implementation doc is missing acceptance criteria
- [subtask:ST13_05] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_05 implementation doc is missing acceptance criteria
- [subtask:ST13_06] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_06 implementation doc is missing acceptance criteria
- [subtask:ST13_07] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_07 implementation doc is missing acceptance criteria
- [subtask:ST13_08] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_08 implementation doc is missing acceptance criteria
- [subtask:ST13_09] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_09 implementation doc is missing acceptance criteria
- [subtask:ST13_10] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_10 implementation doc is missing acceptance criteria
- [subtask:ST13_11] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_11 implementation doc is missing acceptance criteria
- [subtask:ST13_12] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_12 implementation doc is missing acceptance criteria
- [subtask:ST13_13] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_13 implementation doc is missing acceptance criteria
- [subtask:ST13_14] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_14 implementation doc is missing acceptance criteria
- [subtask:ST13_15] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_15 implementation doc is missing acceptance criteria
- [subtask:ST13_16] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_16 implementation doc is missing acceptance criteria
- [subtask:ST13_17] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_17 implementation doc is missing acceptance criteria
- [subtask:ST13_18] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_18 implementation doc is missing acceptance criteria
- [subtask:ST13_19] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_19 implementation doc is missing acceptance criteria
- [subtask:ST13_20] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_20 implementation doc is missing acceptance criteria
- [subtask:ST13_21] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_21 implementation doc is missing acceptance criteria
- [subtask:ST13_22] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_22 implementation doc is missing acceptance criteria
- [subtask:ST13_23] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_23 implementation doc is missing acceptance criteria
- [subtask:ST13_24] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_24 implementation doc is missing acceptance criteria
- [subtask:ST13_25] reason_code=acceptance_criteria_missing ref=gate:acceptance_criteria_missing kind=gate message=subtask ST13_25 implementation doc is missing acceptance criteria
- [subtask:ST13_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_01
- [subtask:ST13_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_02
- [subtask:ST13_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_03
- [subtask:ST13_04] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_04
- [subtask:ST13_05] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_05
- [subtask:ST13_06] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_06
- [subtask:ST13_07] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_07
- [subtask:ST13_08] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_08
- [subtask:ST13_09] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_09
- [subtask:ST13_10] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_10
- [subtask:ST13_11] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_11
- [subtask:ST13_12] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_12
- [subtask:ST13_13] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_13
- [subtask:ST13_14] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_14
- [subtask:ST13_15] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_15
- [subtask:ST13_16] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_16
- [subtask:ST13_17] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_17
- [subtask:ST13_18] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_18
- [subtask:ST13_19] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_19
- [subtask:ST13_20] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_20
- [subtask:ST13_21] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_21
- [subtask:ST13_22] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_22
- [subtask:ST13_23] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_23
- [subtask:ST13_24] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_24
- [subtask:ST13_25] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal_window_open=false prevents implementation packet generation and implementation-ready for subtask ST13_25
- [subtask:ST13_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_01 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_02 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_03 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_04] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_04 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_05] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_05 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_06] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_06 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_07] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_07 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_08] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_08 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_09] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_09 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_10] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_10 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_11] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_11 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_12] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_12 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_13] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_13 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_14] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_14 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_15] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_15 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_16] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_16 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_17] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_17 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_18] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_18 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_19] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_19 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_20] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_20 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_21] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_21 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_22] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_22 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_23] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_23 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_24] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_24 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_25] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST13_25 IMPLEMENTATION document exists does not imply implementation-ready or packet-ready; implementation_doc_state is not active_working_doc
- [subtask:ST13_01] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_01 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_02] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_02 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_03] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_03 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_04] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_04 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_05] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_05 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_06] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_06 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_07] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_07 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_08] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_08 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_09] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_09 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_10] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_10 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_11] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_11 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_12] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_12 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_13] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_13 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_14] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_14 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_15] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_15 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_16] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_16 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_17] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_17 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_18] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_18 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_19] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_19 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_20] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_20 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_21] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_21 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_22] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_22 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_23] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_23 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_24] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_24 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_25] reason_code=implementation_scope_unclear ref=gate:implementation_scope_unclear kind=gate message=subtask ST13_25 implementation scope is incomplete: goal, allowed_modify_paths, forbidden_paths
- [subtask:ST13_01] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_01 implementation doc is missing required tests
- [subtask:ST13_02] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_02 implementation doc is missing required tests
- [subtask:ST13_03] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_03 implementation doc is missing required tests
- [subtask:ST13_04] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_04 implementation doc is missing required tests
- [subtask:ST13_05] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_05 implementation doc is missing required tests
- [subtask:ST13_06] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_06 implementation doc is missing required tests
- [subtask:ST13_07] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_07 implementation doc is missing required tests
- [subtask:ST13_08] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_08 implementation doc is missing required tests
- [subtask:ST13_09] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_09 implementation doc is missing required tests
- [subtask:ST13_10] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_10 implementation doc is missing required tests
- [subtask:ST13_11] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_11 implementation doc is missing required tests
- [subtask:ST13_12] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_12 implementation doc is missing required tests
- [subtask:ST13_13] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_13 implementation doc is missing required tests
- [subtask:ST13_14] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_14 implementation doc is missing required tests
- [subtask:ST13_15] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_15 implementation doc is missing required tests
- [subtask:ST13_16] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_16 implementation doc is missing required tests
- [subtask:ST13_17] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_17 implementation doc is missing required tests
- [subtask:ST13_18] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_18 implementation doc is missing required tests
- [subtask:ST13_19] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_19 implementation doc is missing required tests
- [subtask:ST13_20] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_20 implementation doc is missing required tests
- [subtask:ST13_21] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_21 implementation doc is missing required tests
- [subtask:ST13_22] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_22 implementation doc is missing required tests
- [subtask:ST13_23] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_23 implementation doc is missing required tests
- [subtask:ST13_24] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_24 implementation doc is missing required tests
- [subtask:ST13_25] reason_code=required_tests_missing ref=gate:required_tests_missing kind=gate message=subtask ST13_25 implementation doc is missing required tests

## 文档阻塞项

### 文档

- 无

## OQ 门控摘要

### 计数
- observe_only.clear: 0
- observe_only.review_only: 25
- candidate_gate.clear: 0
- candidate_gate.review_only: 0
- candidate_gate.candidate_blocker: 0
- readiness_gate.clear: 0
- readiness_gate.review_only: 0
- readiness_gate.readiness_blocker: 0

## 未关闭轮次

- 无

## 轮次变化摘要

- 无

## 下一轮议程

### 议程 1: 文档待评审
- entity: document:DOC-PLAN-CURRENT-REPO-2026-04-25
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 文档评审确认依据
- suggested_owner: document-owner

### 议程 2: review_required 的 near-open 实体
- entity: module:M01
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 3: review_required 的 near-open 实体
- entity: module:M03
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 4: review_required 的 near-open 实体
- entity: module:M04
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 5: review_required 的 near-open 实体
- entity: module:M05
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 6: review_required 的 near-open 实体
- entity: module:M06
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 7: review_required 的 near-open 实体
- entity: module:M07
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 8: review_required 的 near-open 实体
- entity: module:M08
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 9: review_required 的 near-open 实体
- entity: module:M09
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

### 议程 10: review_required 的 near-open 实体
- entity: module:M10
- current_state: review_required=true, hard_blocker_count=0
- blocking_reason_codes: 无
- required_evidence: 评审确认依据
- suggested_owner: module-owner

## 说明与解释边界
- 这是仅供报告使用的派生输出，不代表已确认的治理状态。
- 本报告是只读的解释性快照，不是 DOC_STATE 文件的真值来源。
- 本报告不能直接作为 readiness 判断或自动 open-window 的信号。
- 不要使用该文件执行状态回写，也不要把它当作 confirm-transition 的触发依据。
