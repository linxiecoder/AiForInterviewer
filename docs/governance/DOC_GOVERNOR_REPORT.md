# DOC_GOVERNOR_REPORT

## Summary

- modules_review_required: 10
- subtasks_review_required: 2
- modules_blocked_count: 1
- subtasks_blocked_count: 30
- blocked_by_reason_code:
  - formal_window_closed: 30
  - implementation_doc_not_active: 30
  - template_like_required_doc_slot: 60
  - upstream_module_not_ready: 9
- oq_gate_counts:
  - observe_only.clear: 0
  - observe_only.review_only: 25
  - candidate_gate.clear: 0
  - candidate_gate.review_only: 0
  - candidate_gate.candidate_blocker: 0
  - readiness_gate.clear: 0
  - readiness_gate.review_only: 0
  - readiness_gate.readiness_blocker: 0

## Modules Requiring Review

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

## Subtasks Requiring Review

- `ST02_03`: review_required=true reason=[implementation_doc_activation_recommended]
- `ST09_03`: review_required=true reason=[implementation_doc_activation_recommended]

## Candidate blockers by layer

### Modules

- none
### Subtasks

- none

## Downstream blockers by layer

### Modules

- [module:M02] reason_code=template_like_required_doc_slot ref=doc:api kind=doc message=module M02 required slot api template-like
- [module:M02] reason_code=template_like_required_doc_slot ref=doc:open_questions kind=doc message=module M02 required slot open_questions template-like
### Subtasks

- [subtask:ST01_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST01_01 required slot design_doc is template-like
- [subtask:ST01_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST01_02 required slot design_doc is template-like
- [subtask:ST01_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST01_03 required slot design_doc is template-like
- [subtask:ST02_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST02_01 required slot design_doc is template-like
- [subtask:ST02_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST02_02 required slot design_doc is template-like
- [subtask:ST03_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST03_01 required slot design_doc is template-like
- [subtask:ST03_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST03_02 required slot design_doc is template-like
- [subtask:ST03_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST03_03 required slot design_doc is template-like
- [subtask:ST04_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST04_01 required slot design_doc is template-like
- [subtask:ST04_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST04_02 required slot design_doc is template-like
- [subtask:ST04_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST04_03 required slot design_doc is template-like
- [subtask:ST05_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST05_01 required slot design_doc is template-like
- [subtask:ST05_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST05_02 required slot design_doc is template-like
- [subtask:ST05_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST05_03 required slot design_doc is template-like
- [subtask:ST06_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST06_01 required slot design_doc is template-like
- [subtask:ST06_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST06_02 required slot design_doc is template-like
- [subtask:ST06_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST06_03 required slot design_doc is template-like
- [subtask:ST07_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST07_01 required slot design_doc is template-like
- [subtask:ST07_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST07_02 required slot design_doc is template-like
- [subtask:ST07_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST07_03 required slot design_doc is template-like
- [subtask:ST08_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST08_01 required slot design_doc is template-like
- [subtask:ST08_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST08_02 required slot design_doc is template-like
- [subtask:ST08_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST08_03 required slot design_doc is template-like
- [subtask:ST09_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST09_01 required slot design_doc is template-like
- [subtask:ST09_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST09_02 required slot design_doc is template-like
- [subtask:ST10_01] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST10_01 required slot design_doc is template-like
- [subtask:ST10_02] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST10_02 required slot design_doc is template-like
- [subtask:ST10_03] reason_code=template_like_required_doc_slot ref=doc:design_doc kind=doc message=subtask ST10_03 required slot design_doc is template-like
- [subtask:ST01_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST01_01 required slot implementation_doc is template-like
- [subtask:ST01_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST01_02 required slot implementation_doc is template-like
- [subtask:ST01_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST01_03 required slot implementation_doc is template-like
- [subtask:ST02_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST02_01 required slot implementation_doc is template-like
- [subtask:ST02_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST02_02 required slot implementation_doc is template-like
- [subtask:ST02_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST02_03 required slot implementation_doc is template-like
- [subtask:ST03_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST03_01 required slot implementation_doc is template-like
- [subtask:ST03_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST03_02 required slot implementation_doc is template-like
- [subtask:ST03_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST03_03 required slot implementation_doc is template-like
- [subtask:ST04_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST04_01 required slot implementation_doc is template-like
- [subtask:ST04_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST04_02 required slot implementation_doc is template-like
- [subtask:ST04_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST04_03 required slot implementation_doc is template-like
- [subtask:ST05_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST05_01 required slot implementation_doc is template-like
- [subtask:ST05_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST05_02 required slot implementation_doc is template-like
- [subtask:ST05_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST05_03 required slot implementation_doc is template-like
- [subtask:ST06_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST06_01 required slot implementation_doc is template-like
- [subtask:ST06_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST06_02 required slot implementation_doc is template-like
- [subtask:ST06_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST06_03 required slot implementation_doc is template-like
- [subtask:ST07_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST07_01 required slot implementation_doc is template-like
- [subtask:ST07_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST07_02 required slot implementation_doc is template-like
- [subtask:ST07_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST07_03 required slot implementation_doc is template-like
- [subtask:ST08_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST08_01 required slot implementation_doc is template-like
- [subtask:ST08_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST08_02 required slot implementation_doc is template-like
- [subtask:ST08_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST08_03 required slot implementation_doc is template-like
- [subtask:ST09_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST09_01 required slot implementation_doc is template-like
- [subtask:ST09_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST09_02 required slot implementation_doc is template-like
- [subtask:ST09_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST09_03 required slot implementation_doc is template-like
- [subtask:ST10_01] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST10_01 required slot implementation_doc is template-like
- [subtask:ST10_02] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST10_02 required slot implementation_doc is template-like
- [subtask:ST10_03] reason_code=template_like_required_doc_slot ref=doc:implementation_doc kind=doc message=subtask ST10_03 required slot implementation_doc is template-like
- [subtask:ST02_01] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST02_01 upstream module M02 is not downstream ready
- [subtask:ST02_02] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST02_02 upstream module M02 is not downstream ready
- [subtask:ST02_03] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST02_03 upstream module M02 is not downstream ready
- [subtask:ST03_01] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST03_01 upstream module M02 is not downstream ready
- [subtask:ST03_02] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST03_02 upstream module M02 is not downstream ready
- [subtask:ST03_03] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST03_03 upstream module M02 is not downstream ready
- [subtask:ST10_01] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST10_01 upstream module M02 is not downstream ready
- [subtask:ST10_02] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST10_02 upstream module M02 is not downstream ready
- [subtask:ST10_03] reason_code=upstream_module_not_ready ref=module:M02 kind=module message=subtask ST10_03 upstream module M02 is not downstream ready

## Implementation blockers by layer

### Subtasks

- [subtask:ST01_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST01_01
- [subtask:ST01_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST01_02
- [subtask:ST01_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST01_03
- [subtask:ST02_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST02_01
- [subtask:ST02_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST02_02
- [subtask:ST02_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST02_03
- [subtask:ST03_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST03_01
- [subtask:ST03_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST03_02
- [subtask:ST03_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST03_03
- [subtask:ST04_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST04_01
- [subtask:ST04_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST04_02
- [subtask:ST04_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST04_03
- [subtask:ST05_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST05_01
- [subtask:ST05_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST05_02
- [subtask:ST05_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST05_03
- [subtask:ST06_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST06_01
- [subtask:ST06_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST06_02
- [subtask:ST06_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST06_03
- [subtask:ST07_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST07_01
- [subtask:ST07_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST07_02
- [subtask:ST07_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST07_03
- [subtask:ST08_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST08_01
- [subtask:ST08_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST08_02
- [subtask:ST08_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST08_03
- [subtask:ST09_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST09_01
- [subtask:ST09_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST09_02
- [subtask:ST09_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST09_03
- [subtask:ST10_01] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST10_01
- [subtask:ST10_02] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST10_02
- [subtask:ST10_03] reason_code=formal_window_closed ref=policy:formal_window_closed kind=policy message=formal window is closed for subtask ST10_03
- [subtask:ST01_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST01_01 implementation_doc_state is not active_working_doc
- [subtask:ST01_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST01_02 implementation_doc_state is not active_working_doc
- [subtask:ST01_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST01_03 implementation_doc_state is not active_working_doc
- [subtask:ST02_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST02_01 implementation_doc_state is not active_working_doc
- [subtask:ST02_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST02_02 implementation_doc_state is not active_working_doc
- [subtask:ST02_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST02_03 implementation_doc_state is not active_working_doc
- [subtask:ST03_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST03_01 implementation_doc_state is not active_working_doc
- [subtask:ST03_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST03_02 implementation_doc_state is not active_working_doc
- [subtask:ST03_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST03_03 implementation_doc_state is not active_working_doc
- [subtask:ST04_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST04_01 implementation_doc_state is not active_working_doc
- [subtask:ST04_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST04_02 implementation_doc_state is not active_working_doc
- [subtask:ST04_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST04_03 implementation_doc_state is not active_working_doc
- [subtask:ST05_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST05_01 implementation_doc_state is not active_working_doc
- [subtask:ST05_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST05_02 implementation_doc_state is not active_working_doc
- [subtask:ST05_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST05_03 implementation_doc_state is not active_working_doc
- [subtask:ST06_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST06_01 implementation_doc_state is not active_working_doc
- [subtask:ST06_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST06_02 implementation_doc_state is not active_working_doc
- [subtask:ST06_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST06_03 implementation_doc_state is not active_working_doc
- [subtask:ST07_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST07_01 implementation_doc_state is not active_working_doc
- [subtask:ST07_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST07_02 implementation_doc_state is not active_working_doc
- [subtask:ST07_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST07_03 implementation_doc_state is not active_working_doc
- [subtask:ST08_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST08_01 implementation_doc_state is not active_working_doc
- [subtask:ST08_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST08_02 implementation_doc_state is not active_working_doc
- [subtask:ST08_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST08_03 implementation_doc_state is not active_working_doc
- [subtask:ST09_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST09_01 implementation_doc_state is not active_working_doc
- [subtask:ST09_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST09_02 implementation_doc_state is not active_working_doc
- [subtask:ST09_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST09_03 implementation_doc_state is not active_working_doc
- [subtask:ST10_01] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST10_01 implementation_doc_state is not active_working_doc
- [subtask:ST10_02] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST10_02 implementation_doc_state is not active_working_doc
- [subtask:ST10_03] reason_code=implementation_doc_not_active ref=gate:implementation_doc_not_active kind=gate message=subtask ST10_03 implementation_doc_state is not active_working_doc

## OQ gate summary

### counts
- observe_only.clear: 0
- observe_only.review_only: 25
- candidate_gate.clear: 0
- candidate_gate.review_only: 0
- candidate_gate.candidate_blocker: 0
- readiness_gate.clear: 0
- readiness_gate.review_only: 0
- readiness_gate.readiness_blocker: 0

## Notes / interpretation boundary
- This is report-only derived output and does not represent confirmed governance state.
- This report is a read-only interpretation snapshot and is not the source of truth for DOC_STATE files.
- The report cannot be used as a direct readiness or auto-open-window signal.
- Do not use this file for state write-back and do not treat it as an execution trigger for confirm-transition.
