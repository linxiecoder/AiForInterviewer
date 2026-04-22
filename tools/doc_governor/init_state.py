from __future__ import annotations

from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .schema import OFFICIAL_STATE_PATH, SCHEMA_VERSION, make_default_confirmed_state
from .validate import validate_state_file


def init_official_state(
    *,
    bootstrap_input: str,
    dry_run: bool,
    actor: str | None,
    reason: str | None,
    force_overwrite: bool,
) -> tuple[int, list[Diagnostic]]:
    del actor, reason

    bootstrap_path = Path(bootstrap_input).resolve()
    official_output = Path(OFFICIAL_STATE_PATH).resolve()
    diagnostics: list[Diagnostic] = []

    if official_output.exists() and not force_overwrite:
        diagnostics.append(
            make_diagnostic(
                code="INIT_OFFICIAL_STATE_EXISTS",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="docs/governance/DOC_STATE.yaml",
                message="Official state file already exists. Use --force-overwrite to replace it.",
                evidence=[
                    make_evidence(
                        type="file_check",
                        path=official_output.as_posix(),
                        ref="exists",
                        value=True,
                    )
                ],
            )
        )
        return 1, diagnostics

    diagnostics = validate_state_file(bootstrap_path)
    if _has_error(diagnostics):
        return 1, diagnostics

    try:
        import yaml
    except ImportError as exc:
        diagnostics.append(
            make_diagnostic(
                code="INIT_PYYAML_UNAVAILABLE",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="python.dependencies.yaml",
                message="PyYAML is required for init-official-state.",
                evidence=[
                    make_evidence(
                        type="dependency",
                        path="python",
                        ref="import yaml",
                        value=str(exc),
                    )
                ],
            )
        )
        return 1, diagnostics

    bootstrap_text = bootstrap_path.read_text(encoding="utf-8")
    bootstrap_state = yaml.safe_load(bootstrap_text)
    if not isinstance(bootstrap_state, dict):
        diagnostics.append(
            make_diagnostic(
                code="INIT_INVALID_BOOTSTRAP_FORMAT",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path=bootstrap_path.as_posix(),
                message="Bootstrap state is not a mapping.",
                evidence=[
                    make_evidence(
                        type="file_parse",
                        path=bootstrap_path.as_posix(),
                        ref="root_type",
                        value=type(bootstrap_state).__name__,
                    )
                ],
            )
        )
        return 1, diagnostics

    official_state = _build_official_state(bootstrap_state)

    if dry_run:
        return 0, diagnostics

    official_output.parent.mkdir(parents=True, exist_ok=True)
    try:
        official_output.write_text(
            yaml.safe_dump(
                official_state,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            ),
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        diagnostics.append(
            make_diagnostic(
                code="INIT_OFFICIAL_STATE_WRITE_FAILED",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="docs/governance/DOC_STATE.yaml",
                message="Failed to write official DOC_STATE.yaml.",
                evidence=[
                    make_evidence(
                        type="file_write",
                        path=official_output.as_posix(),
                        ref="write",
                        value=str(exc),
                    )
                ],
            )
        )
        return 1, diagnostics

    return 0, diagnostics


def _build_official_state(bootstrap_state: dict[str, object]) -> dict[str, object]:
    schema_version = bootstrap_state.get("schema_version")
    if not isinstance(schema_version, int):
        schema_version = SCHEMA_VERSION

    official_state: dict[str, object] = {
        "schema_version": schema_version,
        "global_policy": _copy_dict(bootstrap_state.get("global_policy", {})),
        "oqs": _build_official_oqs(bootstrap_state.get("oqs", {})),
        "modules": {},
        "subtasks": {},
    }

    for module_id, module in (bootstrap_state.get("modules") or {}).items():
        if not isinstance(module, dict):
            continue
        module_meta = module.get("meta") if isinstance(module.get("meta"), dict) else {}
        module_facts = module.get("facts") if isinstance(module.get("facts"), dict) else {}
        official_state["modules"][module_id] = {
            "meta": _copy_dict(module_meta),
            "facts": _copy_sanitized_facts(module_facts),
            "state": {"confirmed": make_default_confirmed_state("module")},
        }

    for subtask_id, subtask in (bootstrap_state.get("subtasks") or {}).items():
        if not isinstance(subtask, dict):
            continue
        subtask_meta = subtask.get("meta") if isinstance(subtask.get("meta"), dict) else {}
        subtask_facts = subtask.get("facts") if isinstance(subtask.get("facts"), dict) else {}
        official_state["subtasks"][subtask_id] = {
            "meta": _copy_dict(subtask_meta),
            "facts": _copy_sanitized_facts(subtask_facts),
            "state": {"confirmed": make_default_confirmed_state("subtask")},
        }

    return official_state


def _build_official_oqs(raw_oqs: object) -> dict[str, Any]:
    oqs: dict[str, Any] = {}
    if not isinstance(raw_oqs, dict):
        return oqs

    for oq_id, oq_entry in raw_oqs.items():
        if not isinstance(oq_entry, dict):
            continue
        sanitized = _sanitize_mapping(oq_entry)
        oqs[str(oq_id)] = sanitized
    return oqs


def _copy_sanitized_facts(raw_facts: dict[str, object]) -> dict[str, object]:
    facts = _sanitize_mapping(raw_facts)
    if isinstance(facts.get("docs"), dict):
        facts["docs"] = _copy_dict(facts["docs"])
    return facts


def _sanitize_mapping(raw: dict[str, Any]) -> dict[str, Any]:
    excluded_prefixes = ("derived_", "computed_", "recommended_")
    filtered: dict[str, Any] = {}
    for key, value in raw.items():
        if key == "summary" or str(key).startswith(excluded_prefixes):
            continue
        filtered[str(key)] = _copy_dict(value)
    return filtered


def _copy_dict(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _copy_dict(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_copy_dict(item) for item in value]
    return value


def _has_error(diagnostics: list[Diagnostic]) -> bool:
    return any(item.severity == "error" for item in diagnostics)
