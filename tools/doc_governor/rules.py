from __future__ import annotations

from .diagnostics import Diagnostic, Evidence, make_diagnostic, make_evidence


def evaluate_rules(state: dict[str, object]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    global_policy = state.get("global_policy", {})
    formal_window_open = False
    if isinstance(global_policy, dict):
        formal_window_open = bool(global_policy.get("formal_window_open", False))

    modules = state.get("modules", {})
    subtasks = state.get("subtasks", {})

    if isinstance(modules, dict):
        for module_id, module in modules.items():
            if not isinstance(module, dict):
                continue
            diagnostics.extend(
                _evaluate_illegal_state_combinations(
                    entity_type="module",
                    entity_id=module_id,
                    state_entity=module,
                )
            )
            diagnostics.extend(
                _evaluate_legacy_lock_gate(
                    entity_type="module",
                    entity_id=module_id,
                    entity=module,
                )
            )

    if isinstance(subtasks, dict):
        for subtask_id, subtask in subtasks.items():
            if not isinstance(subtask, dict):
                continue
            confirmed = _extract_confirmed_state(subtask)
            facts = _extract_facts(subtask)

            diagnostics.extend(
                _evaluate_illegal_state_combinations(
                    entity_type="subtask",
                    entity_id=subtask_id,
                    state_entity=subtask,
                )
            )
            diagnostics.extend(
                _evaluate_legacy_lock_gate(
                    entity_type="subtask",
                    entity_id=subtask_id,
                    entity=subtask,
                )
            )
            diagnostics.extend(
                _evaluate_template_gate(
                    entity_type="subtask",
                    entity_id=subtask_id,
                    facts=facts,
                    confirmed=confirmed,
                )
            )
            diagnostics.extend(
                _evaluate_inactive_template_gate(
                    entity_type="subtask",
                    entity_id=subtask_id,
                    confirmed=confirmed,
                )
            )
            diagnostics.extend(
                _evaluate_formal_window_closed_gate(
                    entity_type="subtask",
                    entity_id=subtask_id,
                    confirmed=confirmed,
                    formal_window_open=formal_window_open,
                )
            )

    return diagnostics


def _evaluate_legacy_lock_gate(
    *,
    entity_type: str,
    entity_id: str,
    entity: dict[str, object],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    facts = _extract_facts(entity)
    confirmed = _extract_confirmed_state(entity)
    if not facts.get("legacy_locked"):
        return diagnostics

    candidate_status = str(confirmed.get("candidate_status", ""))
    review_status = str(confirmed.get("review_status", ""))
    readiness = str(confirmed.get("readiness", ""))

    if candidate_status == "candidate":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_LEGACY_LOCK_CANDIDATE_FORBIDDEN",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{_state_prefix(entity_type, entity_id)}.candidate_status",
                message="Candidate status must remain none under legacy lock",
                evidence=make_evidence(
                    type="state_transition",
                    path=f"{entity_type}:{entity_id}",
                    ref="candidate_status",
                    value=candidate_status,
                ),
            )
        )

    if review_status != "unreviewed":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_LEGACY_LOCK_REVIEW_FORBIDDEN",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{_state_prefix(entity_type, entity_id)}.review_status",
                message="Review status must remain unreviewed under legacy lock",
                evidence=make_evidence(
                    type="state_transition",
                    path=f"{entity_type}:{entity_id}",
                    ref="review_status",
                    value=review_status,
                ),
            )
        )

    if readiness != "blocked":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_LEGACY_LOCK_READINESS_FORBIDDEN",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{_state_prefix(entity_type, entity_id)}.readiness",
                message="Readiness must remain blocked under legacy lock",
                evidence=make_evidence(
                    type="state_transition",
                    path=f"{entity_type}:{entity_id}",
                    ref="readiness",
                    value=readiness,
                ),
            )
        )

    return diagnostics


def _evaluate_formal_window_closed_gate(
    *,
    entity_type: str,
    entity_id: str,
    confirmed: dict[str, object],
    formal_window_open: bool,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if formal_window_open:
        return diagnostics

    candidate_status = str(confirmed.get("candidate_status", ""))
    readiness = str(confirmed.get("readiness", ""))

    if candidate_status == "candidate":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_FORMAL_WINDOW_CLOSED_CANDIDATE_FORBIDDEN",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=_state_path(entity_type, entity_id, "candidate_status"),
                message=(
                    "candidate_status=candidate requires global_policy.formal_window_open=true; "
                    "facts-only candidate previews must not be treated as formal-window-open"
                ),
                evidence=make_evidence(
                    type="policy_check",
                    path=f"{entity_type}:{entity_id}",
                    ref="global_policy.formal_window_open",
                    value=False,
                ),
            )
        )

    if readiness == "implementation_ready":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_FORMAL_WINDOW_CLOSED_IMPLEMENTATION_READY_FORBIDDEN",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=_state_path(entity_type, entity_id, "readiness"),
                message=(
                    "Implementation-ready readiness is not allowed while formal window is "
                    "closed"
                ),
                evidence=make_evidence(
                    type="policy_check",
                    path=f"{entity_type}:{entity_id}",
                    ref="global_policy.formal_window_open",
                    value=False,
                ),
            )
        )

    return diagnostics


def _evaluate_template_gate(
    *,
    entity_type: str,
    entity_id: str,
    facts: dict[str, object],
    confirmed: dict[str, object],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    implementation_like = bool(
        isinstance(facts.get("implementation_doc"), dict)
        and facts["implementation_doc"].get("template_like") is True
    )

    if not implementation_like:
        return diagnostics

    implementation_state = str(confirmed.get("implementation_doc_state", ""))
    if implementation_state == "active_working_doc":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_TEMPLATE_ACTIVE_WORKING_DOC_FORBIDDEN",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=_state_path(entity_type, entity_id, "implementation_doc_state"),
                message="template-like implementation doc cannot be marked active_working_doc",
                evidence=make_evidence(
                    type="fact_check",
                    path=f"{entity_type}:{entity_id}",
                    ref="facts.implementation_doc.template_like",
                    value=True,
                ),
            )
        )

    return diagnostics


def _evaluate_inactive_template_gate(
    *,
    entity_type: str,
    entity_id: str,
    confirmed: dict[str, object],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    implementation_state = str(confirmed.get("implementation_doc_state", ""))
    readiness = str(confirmed.get("readiness", ""))
    if implementation_state == "inactive_template" and readiness == "implementation_ready":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_INACTIVE_TEMPLATE_IMPLEMENTATION_READY_FORBIDDEN",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=_state_path(entity_type, entity_id, "readiness"),
                message=(
                    "Implementation readiness is not allowed when implementation doc is "
                    "inactive template"
                ),
                evidence=make_evidence(
                    type="state_check",
                    path=f"{entity_type}:{entity_id}",
                    ref="state.confirmed.readiness",
                    value=readiness,
                ),
            )
        )
    return diagnostics


def _evaluate_illegal_state_combinations(
    *,
    entity_type: str,
    entity_id: str,
    state_entity: dict[str, object],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    confirmed = _extract_confirmed_state(state_entity)
    candidate_status = str(confirmed.get("candidate_status", ""))
    review_status = str(confirmed.get("review_status", ""))
    readiness = str(confirmed.get("readiness", ""))
    maturity = confirmed.get("maturity")

    if candidate_status == "candidate" and review_status != "pending_confirmation":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_ILLEGAL_STATE_COMBINATION",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=_state_path(entity_type, entity_id, "candidate_status"),
                message=(
                    "candidate status cannot be combined with non-pending confirmation review "
                    "state"
                ),
                evidence=make_evidence(
                    type="state_check",
                    path=f"{entity_type}:{entity_id}",
                    ref="candidate_status/review_status",
                    value={"candidate_status": candidate_status, "review_status": review_status},
                ),
            )
        )

    if candidate_status in {"none", "observe"} and review_status == "approved":
        diagnostics.append(
            _make_rule_diag(
                code="RULE_ILLEGAL_STATE_COMBINATION",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=_state_path(entity_type, entity_id, "review_status"),
                message="approved review is invalid when candidate_status is not candidate",
                evidence=make_evidence(
                    type="state_check",
                    path=f"{entity_type}:{entity_id}",
                    ref="candidate_status/review_status",
                    value={"candidate_status": candidate_status, "review_status": review_status},
                ),
            )
        )

    if readiness == "downstream_ready" and maturity is None:
        diagnostics.append(
            _make_rule_diag(
                code="RULE_ILLEGAL_STATE_COMBINATION",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=_state_path(entity_type, entity_id, "maturity"),
                message="readiness=downstream_ready requires maturity to be set",
                evidence=make_evidence(
                    type="state_check",
                    path=f"{entity_type}:{entity_id}",
                    ref="state.confirmed.maturity",
                    value=None,
                ),
            )
        )

    return diagnostics


def _extract_facts(entity: dict[str, object]) -> dict[str, object]:
    facts = entity.get("facts")
    if isinstance(facts, dict):
        return facts
    return {}


def _extract_confirmed_state(entity: dict[str, object]) -> dict[str, object]:
    state_obj = entity.get("state")
    if not isinstance(state_obj, dict):
        return {}
    confirmed = state_obj.get("confirmed")
    if isinstance(confirmed, dict):
        return confirmed
    return {}


def _make_rule_diag(
    *,
    code: str,
    entity_type: str,
    entity_id: str,
    field_path: str,
    message: str,
    evidence: Evidence,
) -> Diagnostic:
    return make_diagnostic(
        code=code,
        severity="error",
        entity_type=entity_type,
        entity_id=entity_id,
        field_path=field_path,
        message=message,
        evidence=[evidence],
    )


def _state_prefix(entity_type: str, entity_id: str) -> str:
    if entity_type == "module":
        return f"modules.{entity_id}.state.confirmed"
    if entity_type == "subtask":
        return f"subtasks.{entity_id}.state.confirmed"
    return f"{entity_type}.{entity_id}"


def _state_path(entity_type: str, entity_id: str, field: str) -> str:
    return f"{_state_prefix(entity_type, entity_id)}.{field}"
