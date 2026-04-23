from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .requirement_scan import scan_requirements


def build_requirement_link_suggestions(
    *,
    state_path: str | Path,
    entity_id: str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    repo_root = _resolve_repo_root(state_path)

    requirements = _as_dict(state.get("requirements"))
    modules = _as_dict(state.get("modules"))
    subtasks = _as_dict(state.get("subtasks"))
    selected_task_ids, selected_scope = _select_task_ids(
        state=state,
        entity_id=entity_id,
    )
    if not selected_task_ids:
        raise ValueError("no subtasks available for requirement-link suggestions")

    scan_result = scan_requirements(
        repo_root=repo_root,
        modules=modules,
        subtasks=subtasks,
    )
    scanned_requirements = _as_dict(scan_result.get("requirements"))

    resolved_candidates: list[dict[str, Any]] = []
    ambiguous_candidates: list[dict[str, Any]] = []
    unresolved_tasks: list[dict[str, Any]] = []
    evidence_by_task: dict[str, list[dict[str, Any]]] = {}

    for task_id in selected_task_ids:
        state_task = _as_dict(subtasks.get(task_id))
        meta = _as_dict(state_task.get("meta"))
        module_id = str(meta.get("module_id", "")).strip()
        task_path = str(meta.get("path", "")).strip()

        candidate_map: dict[str, dict[str, Any]] = {}
        all_evidence: list[dict[str, Any]] = []

        for requirement_id, requirement in requirements.items():
            requirement = _as_dict(requirement)
            requirement_meta = _as_dict(requirement.get("meta"))
            requirement_facts = _as_dict(requirement.get("facts"))

            if task_id in _as_string_list(requirement_facts.get("task_ids")):
                _add_candidate_evidence(
                    candidate_map=candidate_map,
                    requirement_id=requirement_id,
                    weight=1.0,
                    source="official_requirement_task_ids",
                    strength="strong",
                    message="official requirement 的 facts.task_ids 直接包含该 task",
                )
            if module_id and module_id in _as_string_list(requirement_facts.get("module_ids")):
                _add_candidate_evidence(
                    candidate_map=candidate_map,
                    requirement_id=requirement_id,
                    weight=0.78,
                    source="official_requirement_module_ids",
                    strength="medium",
                    message="official requirement 的 facts.module_ids 包含该 task 所属模块",
                )
            requirement_path = str(requirement_meta.get("path", "")).strip()
            if _path_prefix_match(requirement_path=requirement_path, task_path=task_path):
                _add_candidate_evidence(
                    candidate_map=candidate_map,
                    requirement_id=requirement_id,
                    weight=0.55,
                    source="official_requirement_path_prefix",
                    strength="medium",
                    message="task path is under the requirement path prefix",
                )

        if not requirements:
            for requirement_id, requirement in scanned_requirements.items():
                requirement = _as_dict(requirement)
                requirement_meta = _as_dict(requirement.get("meta"))
                requirement_facts = _as_dict(requirement.get("facts"))
                if str(requirement_meta.get("scope_kind", "")).strip() == "root_requirement_cluster":
                    _add_candidate_evidence(
                        candidate_map=candidate_map,
                        requirement_id=requirement_id,
                        weight=0.34,
                        source="requirement_scan_root_cluster",
                        strength="weak",
                        message="requirement_scan 给出了根 requirement cluster 候选",
                    )
                    if module_id and task_path:
                        _add_candidate_evidence(
                            candidate_map=candidate_map,
                            requirement_id=requirement_id,
                            weight=0.33,
                            source="task_module_context_available",
                            strength="weak",
                            message="task 具备模块和路径上下文，可落在当前根 requirement cluster 下",
                        )
                    if module_id and module_id in _as_string_list(requirement_facts.get("module_ids")):
                        _add_candidate_evidence(
                            candidate_map=candidate_map,
                            requirement_id=requirement_id,
                            weight=0.08,
                            source="requirement_scan_module_list",
                            strength="weak",
                            message="requirement_scan 的 module 列表覆盖了该 task 所属模块",
                        )
                    if task_id in _as_string_list(requirement_facts.get("task_ids")):
                        _add_candidate_evidence(
                            candidate_map=candidate_map,
                            requirement_id=requirement_id,
                            weight=0.08,
                            source="requirement_scan_task_list",
                            strength="weak",
                            message="requirement_scan 的 task 列表覆盖了该 task id",
                        )

        ranked_candidates = sorted(
            (
                {
                    "requirement_id": requirement_id,
                    "score": round(float(data["score"]), 2),
                    "evidence": data["evidence"],
                }
                for requirement_id, data in candidate_map.items()
            ),
            key=lambda item: (-float(item["score"]), str(item["requirement_id"])),
        )
        for item in ranked_candidates:
            all_evidence.extend(_as_list_of_dicts(item.get("evidence")))
        evidence_by_task[task_id] = all_evidence

        if not ranked_candidates:
            unresolved_tasks.append(
                {
                    "task_id": task_id,
                    "candidate_requirement_ids": [],
                    "selected_requirement_id": None,
                    "confidence": _confidence("low", 0.18),
                    "evidence": [],
                    "needs_manual_confirmation": True,
                    "reason": "当前没有足够可用的 requirement 证据",
                }
            )
            continue

        top = ranked_candidates[0]
        top_score = float(top["score"])
        top_requirement_id = str(top["requirement_id"])
        candidate_requirement_ids = [str(item["requirement_id"]) for item in ranked_candidates]
        exact_official_match = any(
            item.get("source") == "official_requirement_task_ids"
            for item in _as_list_of_dicts(top.get("evidence"))
        )

        if len(ranked_candidates) > 1:
            second_score = float(ranked_candidates[1]["score"])
        else:
            second_score = -1.0
        score_gap = top_score - second_score

        if exact_official_match and score_gap >= 0.2:
            resolved_candidates.append(
                {
                    "task_id": task_id,
                    "candidate_requirement_ids": candidate_requirement_ids,
                    "selected_requirement_id": top_requirement_id,
                    "confidence": _confidence("high", min(0.98, 0.82 + top_score / 5)),
                    "evidence": top["evidence"],
                    "needs_manual_confirmation": False,
                    "reason": "official requirement 已直接引用该 task",
                }
            )
            continue

        if top_score >= 0.65 and score_gap >= 0.15:
            resolved_candidates.append(
                {
                    "task_id": task_id,
                    "candidate_requirement_ids": candidate_requirement_ids,
                    "selected_requirement_id": top_requirement_id,
                    "confidence": _confidence("medium", min(0.82, 0.5 + top_score / 3)),
                    "evidence": top["evidence"],
                    "needs_manual_confirmation": True,
                    "reason": "当前已有一个更强候选，但证据仍需人工确认",
                }
            )
            continue

        close_candidates = [
            item for item in ranked_candidates if abs(float(item["score"]) - top_score) <= 0.14
        ]
        if top_score >= 0.45 and len(close_candidates) > 1:
            ambiguous_candidates.append(
                {
                    "task_id": task_id,
                    "candidate_requirement_ids": [
                        str(item["requirement_id"]) for item in close_candidates
                    ],
                    "selected_requirement_id": None,
                    "confidence": _confidence("medium", 0.58),
                    "evidence": all_evidence,
                    "needs_manual_confirmation": True,
                    "reason": "多个 requirement 候选仍然过于接近，当前不宜自动判定唯一答案",
                }
            )
            continue

        unresolved_tasks.append(
            {
                "task_id": task_id,
                "candidate_requirement_ids": candidate_requirement_ids,
                "selected_requirement_id": None,
                "confidence": _confidence("low", min(0.44, 0.18 + top_score / 4)),
                "evidence": all_evidence,
                "needs_manual_confirmation": True,
                "reason": "现有证据仍然偏弱，不建议直接补 requirement 关系",
            }
        )

    next_actions = _build_next_actions(
        resolved_candidates=resolved_candidates,
        ambiguous_candidates=ambiguous_candidates,
        unresolved_tasks=unresolved_tasks,
    )
    confidence = _build_overall_confidence(
        selected_task_count=len(selected_task_ids),
        resolved_candidates=resolved_candidates,
        ambiguous_candidates=ambiguous_candidates,
        unresolved_tasks=unresolved_tasks,
    )

    return {
        "summary": {
            "selected_entity_id": entity_id or "ALL",
            "selected_scope": selected_scope,
            "selected_task_count": len(selected_task_ids),
            "resolved_count": len(resolved_candidates),
            "ambiguous_count": len(ambiguous_candidates),
            "unresolved_count": len(unresolved_tasks),
            "direct_linkable_count": sum(
                1 for item in resolved_candidates if not bool(item.get("needs_manual_confirmation"))
            ),
            "manual_confirmation_count": sum(
                1 for item in resolved_candidates if bool(item.get("needs_manual_confirmation"))
            )
            + len(ambiguous_candidates)
            + len(unresolved_tasks),
        },
        "resolved_candidates": resolved_candidates,
        "ambiguous_candidates": ambiguous_candidates,
        "unresolved_tasks": unresolved_tasks,
        "evidence_by_task": evidence_by_task,
        "next_actions": next_actions,
        "confidence": confidence,
    }


def render_requirement_link_suggestions_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    direct_resolved = [
        item
        for item in _as_list_of_dicts(payload.get("resolved_candidates"))
        if not bool(item.get("needs_manual_confirmation"))
    ]
    manual_resolved = [
        item
        for item in _as_list_of_dicts(payload.get("resolved_candidates"))
        if bool(item.get("needs_manual_confirmation"))
    ]
    lines = [
        "# 任务 requirement 关系建议",
        "",
        "## 摘要",
        f"- 选择范围: {summary.get('selected_scope', '')}",
        f"- 目标实体: {summary.get('selected_entity_id', '')}",
        f"- 纳入分析 task 数量: {summary.get('selected_task_count', 0)}",
        f"- 已解析建议: {summary.get('resolved_count', 0)}",
        f"- 需人工确认: {summary.get('manual_confirmation_count', 0)}",
        f"- 证据不足: {summary.get('unresolved_count', 0)}",
        "",
        "## 可直接采用的建议",
    ]
    for item in direct_resolved:
        lines.append(
            f"- {item.get('task_id', '')}: {item.get('selected_requirement_id', '')} | {item.get('reason', '')}"
        )

    lines.extend(["", "## 倾向性建议（仍需人工确认）"])
    for item in manual_resolved:
        lines.append(
            f"- {item.get('task_id', '')}: {item.get('selected_requirement_id', '')} | {item.get('reason', '')}"
        )

    lines.extend(["", "## 多候选需人工确认"])
    for item in _as_list_of_dicts(payload.get("ambiguous_candidates")):
        candidates = ", ".join(_as_string_list(item.get("candidate_requirement_ids")))
        lines.append(f"- {item.get('task_id', '')}: {candidates} | {item.get('reason', '')}")

    lines.extend(["", "## 证据不足"])
    for item in _as_list_of_dicts(payload.get("unresolved_tasks")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('reason', '')}")

    lines.extend(["", "## 下一步建议"])
    for item in _as_list_of_dicts(payload.get("next_actions")):
        lines.append(f"- {item.get('title', '')}: {item.get('detail', '')}")

    return "\n".join(lines) + "\n"


def write_requirement_link_suggestions_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_requirement_link_suggestions_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_next_actions(
    *,
    resolved_candidates: list[dict[str, Any]],
    ambiguous_candidates: list[dict[str, Any]],
    unresolved_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    direct_ids = [
        item["task_id"]
        for item in resolved_candidates
        if not bool(item.get("needs_manual_confirmation"))
    ]
    if direct_ids:
        actions.append(
            {
                "title": "可直接补 requirement 关系",
                "detail": ", ".join(direct_ids[:8]),
            }
        )
    manual_ids = [
        item["task_id"]
        for item in resolved_candidates
        if bool(item.get("needs_manual_confirmation"))
    ] + [item["task_id"] for item in ambiguous_candidates]
    if manual_ids:
        actions.append(
            {
                "title": "先人工确认再补关系",
                "detail": ", ".join(manual_ids[:8]),
            }
        )
    if unresolved_tasks:
        actions.append(
            {
                "title": "暂不建议自动补关系",
                "detail": ", ".join(item["task_id"] for item in unresolved_tasks[:8]),
            }
        )
    if not actions:
        actions.append(
            {
                "title": "当前没有可输出建议",
                "detail": "未发现需要 requirement-link 建议的 task。",
            }
        )
    return actions


def _build_overall_confidence(
    *,
    selected_task_count: int,
    resolved_candidates: list[dict[str, Any]],
    ambiguous_candidates: list[dict[str, Any]],
    unresolved_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    if selected_task_count <= 0:
        return _confidence("low", 0.1)
    score = 0.2
    score += 0.55 * (len(resolved_candidates) / selected_task_count)
    score += 0.15 * (len(ambiguous_candidates) / selected_task_count)
    if unresolved_tasks:
        score -= 0.12 * (len(unresolved_tasks) / selected_task_count)
    score = max(0.1, min(0.95, round(score, 2)))
    if score >= 0.8:
        level = "high"
    elif score >= 0.55:
        level = "medium"
    else:
        level = "low"
    return _confidence(level, score)


def _select_task_ids(
    *,
    state: dict[str, Any],
    entity_id: str | None,
) -> tuple[list[str], str]:
    subtasks = _as_dict(state.get("subtasks"))
    modules = _as_dict(state.get("modules"))
    requirements = _as_dict(state.get("requirements"))

    if not entity_id:
        return sorted(subtasks.keys()), "all_tasks"

    if entity_id in subtasks:
        return [entity_id], "task"

    if entity_id in modules:
        task_ids = []
        for task_id, subtask in subtasks.items():
            meta = _as_dict(_as_dict(subtask).get("meta"))
            if str(meta.get("module_id", "")).strip() == entity_id:
                task_ids.append(task_id)
        if not task_ids:
            raise ValueError(f"模块下没有可分析的 subtask: {entity_id}")
        return sorted(task_ids), "module"

    if entity_id in requirements:
        facts = _as_dict(_as_dict(requirements.get(entity_id)).get("facts"))
        task_ids = [task_id for task_id in _as_string_list(facts.get("task_ids")) if task_id in subtasks]
        if not task_ids:
            raise ValueError(f"requirement 下没有可分析的 subtask: {entity_id}")
        return sorted(task_ids), "requirement"

    raise ValueError(f"未找到 entity-id: {entity_id}")


def _resolve_repo_root(state_path: Path) -> Path:
    normalized = state_path.resolve()
    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    return normalized.parent


def _load_state(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ValueError(f"加载 state 文件需要 PyYAML: {exc}") from exc

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"未找到 state 文件: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("state 文件内容必须是映射结构")
    return raw


def _add_candidate_evidence(
    *,
    candidate_map: dict[str, dict[str, Any]],
    requirement_id: str,
    weight: float,
    source: str,
    strength: str,
    message: str,
) -> None:
    entry = candidate_map.setdefault(requirement_id, {"score": 0.0, "evidence": []})
    entry["score"] = float(entry["score"]) + weight
    evidence = _as_list_of_dicts(entry.get("evidence"))
    evidence.append(
        {
            "requirement_id": requirement_id,
            "source": source,
            "strength": strength,
            "weight": round(weight, 2),
            "message": message,
        }
    )
    entry["evidence"] = evidence


def _path_prefix_match(*, requirement_path: str, task_path: str) -> bool:
    requirement_path = requirement_path.strip()
    task_path = task_path.strip()
    if not requirement_path or not task_path or requirement_path == ".":
        return False
    normalized_requirement = requirement_path.rstrip("/") + "/"
    return task_path.startswith(normalized_requirement)


def _confidence(level: str, score: float) -> dict[str, Any]:
    return {"level": level, "score": round(float(score), 2)}


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return _dedupe_strings([str(item).strip() for item in value if str(item).strip()])


def _as_list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dedupe_strings(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered
