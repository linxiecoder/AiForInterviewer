from __future__ import annotations

import re


REQUIREMENT_ID_RE = re.compile(r"^RQ\d{2}$")
MODULE_ID_RE = re.compile(r"^M\d{2}$")
SUBTASK_ID_RE = re.compile(r"^ST\d{2}_\d{2}$")

REQUIREMENT_PATH_TOKEN_RE = re.compile(r"^(RQ\d{2})(?:-|$|/)")
MODULE_PATH_TOKEN_RE = re.compile(r"^(M\d{2})(?:-|$|/)")
SUBTASK_PATH_TOKEN_RE = re.compile(r"^(ST\d{2}_\d{2})(?:-|$|/)")

MODULE_DIR_RE = re.compile(r"^(M\d{2})-")
SUBTASK_DIR_RE = re.compile(r"^(ST\d{2}_\d{2})-")

REQUIREMENT_SCOPE_ROOT_CLUSTER = "root_requirement_cluster"
REQUIREMENT_SCOPE_DIRECTORY = "requirement_dir"
REQUIREMENT_SCOPE_KINDS = (
    REQUIREMENT_SCOPE_ROOT_CLUSTER,
    REQUIREMENT_SCOPE_DIRECTORY,
)


def normalize_repo_relative_path(path: str | None) -> str | None:
    if path is None:
        return None
    normalized = str(path).strip().replace("\\", "/")
    if normalized in {"", ".", "./"}:
        return "."
    normalized = normalized.strip("/")
    return normalized or "."


def extract_requirement_id_from_path(path: str | None) -> str | None:
    return _extract_id_from_path(path, REQUIREMENT_PATH_TOKEN_RE)


def extract_module_id_from_path(path: str | None) -> str | None:
    return _extract_id_from_path(path, MODULE_PATH_TOKEN_RE)


def extract_subtask_id_from_path(path: str | None) -> str | None:
    return _extract_id_from_path(path, SUBTASK_PATH_TOKEN_RE)


def is_valid_requirement_path(
    *,
    requirement_id: str,
    path: str | None,
    scope_kind: str,
) -> bool:
    normalized = normalize_repo_relative_path(path)
    if normalized is None:
        return False

    if scope_kind == REQUIREMENT_SCOPE_ROOT_CLUSTER:
        return normalized == "."

    if scope_kind == REQUIREMENT_SCOPE_DIRECTORY:
        if not normalized.startswith("docs/requirements/"):
            return False
        return extract_requirement_id_from_path(normalized) == requirement_id

    return False


def _extract_id_from_path(path: str | None, token_re: re.Pattern[str]) -> str | None:
    normalized = normalize_repo_relative_path(path)
    if normalized is None:
        return None
    for part in normalized.split("/"):
        match = token_re.match(part)
        if match:
            return match.group(1)
    return None
