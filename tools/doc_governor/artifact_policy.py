from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Pattern

from .schema import MODULE_DOC_SLOTS, SUBTASK_DOC_SLOTS


DEFAULT_MODULE_DIR_RE = re.compile(r"^(M\d{2})-[a-z0-9][a-z0-9-]*$")
DEFAULT_SUBTASK_DIR_RE = re.compile(r"^(ST\d{2}_\d{2})-[a-z0-9][a-z0-9-]*$")


DEFAULT_DOC_HEADINGS = {
    "requirements": ("背景", "目标"),
    "design": ("目标", "范围"),
    "api": ("接口", "约束"),
    "schema": ("数据", "约束"),
    "logic": ("流程", "异常"),
    "dependencies": ("上游", "下游"),
    "open_questions": ("问题", "影响"),
    "execution_log": ("本轮", "结论"),
    "design_doc": ("目标", "方案"),
    "implementation_doc": ("步骤", "验证"),
}


@dataclass(frozen=True)
class AssetSlot:
    filename: str
    doc_kind: str
    required_headings: tuple[str, ...] = ()


def _default_module_slots() -> dict[str, AssetSlot]:
    slots: dict[str, AssetSlot] = {}
    for slot_name, filename in MODULE_DOC_SLOTS.items():
        slots[slot_name] = AssetSlot(
            filename=filename,
            doc_kind=f"module_{slot_name}",
            required_headings=DEFAULT_DOC_HEADINGS.get(slot_name, ()),
        )
    return slots


def _default_subtask_slots() -> dict[str, AssetSlot]:
    slots: dict[str, AssetSlot] = {}
    for slot_name, filename in SUBTASK_DOC_SLOTS.items():
        if slot_name == "design_doc":
            doc_kind = "subtask_design"
        else:
            doc_kind = "subtask_implementation"
        slots[slot_name] = AssetSlot(
            filename=filename,
            doc_kind=doc_kind,
            required_headings=DEFAULT_DOC_HEADINGS.get(slot_name, ()),
        )
    return slots


@dataclass(frozen=True)
class ArtifactPolicy:
    modules_root: str = "docs/modules"
    required_root_docs: tuple[str, ...] = (
        "AGENTS.md",
        "MODULE_INDEX.md",
        "TASK_INDEX.md",
        "OPEN_QUESTIONS.md",
        "docs/DOC_GOVERNANCE.md",
    )
    module_slots: dict[str, AssetSlot] = field(default_factory=_default_module_slots)
    subtask_slots: dict[str, AssetSlot] = field(default_factory=_default_subtask_slots)
    module_dir_pattern: Pattern[str] = DEFAULT_MODULE_DIR_RE
    subtask_dir_pattern: Pattern[str] = DEFAULT_SUBTASK_DIR_RE
    module_index_file: str = "MODULE_INDEX.md"
    module_index_id_headers: tuple[str, ...] = (
        "模块ID",
        "Module ID",
        "module_id",
        "ID",
    )
    module_index_path_headers: tuple[str, ...] = (
        "路径",
        "模块路径",
        "模块目录",
        "path",
    )
    subtask_index_file: str = "MODULE_TASK_INDEX.md"
    subtask_index_id_headers: tuple[str, ...] = (
        "Task ID",
        "子任务ID",
        "task_id",
    )
    subtask_index_parent_headers: tuple[str, ...] = (
        "父任务",
        "所属模块",
        "parent",
        "module_id",
    )
    subtask_index_path_headers: tuple[str, ...] = (
        "对应文档路径",
        "路径",
        "文档路径",
        "path",
    )
    ignored_path_globs: tuple[str, ...] = (
        "**/__pycache__/**",
        "**/.pytest_cache/**",
    )


def build_default_artifact_policy() -> ArtifactPolicy:
    return ArtifactPolicy()
