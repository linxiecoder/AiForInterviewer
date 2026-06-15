from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKIPPED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".local",
    ".venv",
    ".understand-anything",
    "archive",
    "dist",
    "docs/goals",
    "docs/tmp",
    "evals/reports",
    "node_modules",
    "tmp",
}
TEXT_SUFFIXES = {
    ".css",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
}


def _token(*parts: str) -> str:
    return "_".join(parts)


FORBIDDEN_TOKENS = (
    _token("generate", "next", "question"),
    _token("next", "question", "agent"),
    _token("next", "question", "schema"),
    _token("next", "question", "prompt"),
    _token("next", "question", "metadata"),
)


def _is_skipped(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    text = relative.as_posix()
    return any(text == skipped or text.startswith(f"{skipped}/") for skipped in SKIPPED_DIRS)


def test_question_generation_semantics_are_collapsed_to_feedback_intent_path() -> None:
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or _is_skipped(path) or path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN_TOKENS:
            if token in content:
                hits.append(f"{path.relative_to(ROOT)}: {token}")

    assert hits == []
