import fnmatch
import os
import re
import shutil
import tempfile
import unittest
import uuid
from dataclasses import dataclass
from pathlib import Path


KEEP_TEST_ARTIFACTS_ENV = "AI_FOR_INTERVIEWER_KEEP_TEST_ARTIFACTS"
TEST_TEMP_ROOT_ENV = "AI_FOR_INTERVIEWER_TEST_TEMP_ROOT"
ALLOW_TEST_DIR_LEAKS_ENV = "AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS"
DEFAULT_TEST_TEMP_ROOT_NAME = "ai-for-interviewer-test-artifacts"
TEMP_DIR_NAME_REGEX = r"^(?:_?tmp|temp)(?:[-_].*)?$"
_TRUE_VALUES = {"1", "true", "yes", "on"}
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DOC_GOVERNOR_WATCH_ROOT = _REPO_ROOT / "tests" / "doc_governor"
_TEMP_DIR_NAME_PATTERN = re.compile(TEMP_DIR_NAME_REGEX)
_TEMP_DIR_SCAN_IGNORES = (
    ".git",
    ".venv",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return slug or "test"


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name, "")
    return value.strip().lower() in _TRUE_VALUES


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _snapshot_child_directories(root: Path, *, recursive: bool = False) -> set[str]:
    if not root.exists():
        return set()
    if not recursive:
        return {child.name for child in root.iterdir() if child.is_dir()}
    return {
        child.relative_to(root).as_posix()
        for child in root.rglob("*")
        if child.is_dir()
    }


def _matches_any_pattern(value: str, patterns: tuple[str, ...]) -> bool:
    basename = Path(value).name
    return any(
        fnmatch.fnmatch(value, pattern) or fnmatch.fnmatch(basename, pattern)
        for pattern in patterns
    )


def _prune_empty_parents(start: Path, *, stop_at: Path) -> None:
    current = start.resolve()
    boundary = stop_at.resolve()
    if not _is_within(current, boundary) and current != boundary:
        raise ValueError(f"cleanup path {current} is outside boundary {boundary}")

    while current != boundary:
        if current.exists():
            try:
                next(current.iterdir())
                return
            except StopIteration:
                current.rmdir()
            except FileNotFoundError:
                pass
        current = current.parent


def _is_temp_like_directory_name(name: str) -> bool:
    return _TEMP_DIR_NAME_PATTERN.fullmatch(name) is not None


def scan_temp_like_directories(
    root: str | Path,
    *,
    recursive: bool = False,
    ignore_names: tuple[str, ...] = _TEMP_DIR_SCAN_IGNORES,
) -> list[str]:
    root_path = Path(root).resolve()
    if not root_path.exists():
        return []

    matches: list[str] = []
    if recursive:
        iterator = (path for path in root_path.rglob("*") if path.is_dir())
    else:
        iterator = (path for path in root_path.iterdir() if path.is_dir())

    ignore_set = set(ignore_names)
    for candidate in iterator:
        basename = candidate.name
        if basename in ignore_set:
            continue
        if _is_temp_like_directory_name(basename):
            if recursive:
                matches.append(candidate.relative_to(root_path).as_posix())
            else:
                matches.append(basename)
    return sorted(set(matches))


def find_repo_temp_dir_residuals(repo_root: str | Path | None = None) -> list[str]:
    root = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT
    residuals: list[str] = []

    for name in scan_temp_like_directories(root, recursive=False):
        residuals.append(f"{root}: {name}")

    tests_root = root / "tests"
    for name in scan_temp_like_directories(tests_root, recursive=True):
        residuals.append(f"{tests_root}: {name}")

    return sorted(set(residuals))


@dataclass(frozen=True)
class DirectoryWatchSpec:
    root: Path
    ignore_name_patterns: tuple[str, ...] = ()
    recursive: bool = False

    def resolved(self) -> "DirectoryWatchSpec":
        return DirectoryWatchSpec(
            root=self.root.resolve(),
            ignore_name_patterns=tuple(self.ignore_name_patterns),
            recursive=self.recursive,
        )


class DirectoryLeakGuard:
    def __init__(self, watch_specs: list[DirectoryWatchSpec]) -> None:
        self._watch_snapshots: list[tuple[DirectoryWatchSpec, set[str]]] = [
            (
                spec.resolved(),
                _snapshot_child_directories(spec.root.resolve(), recursive=spec.recursive),
            )
            for spec in watch_specs
        ]

    @classmethod
    def for_roots(cls, roots: list[str | Path] | None = None) -> "DirectoryLeakGuard":
        specs = [DirectoryWatchSpec(root=Path(root)) for root in (roots or [])]
        return cls(specs)

    def find_unexpected_directories(self) -> list[str]:
        leak_messages: list[str] = []
        for spec, before in self._watch_snapshots:
            after = _snapshot_child_directories(spec.root, recursive=spec.recursive)
            leaked = sorted(
                name
                for name in (after - before)
                if not _matches_any_pattern(name, spec.ignore_name_patterns)
            )
            if leaked:
                leak_messages.append(f"{spec.root}: {', '.join(leaked)}")
        return leak_messages

    def assert_clean(self) -> None:
        leak_messages = self.find_unexpected_directories()
        if leak_messages:
            raise AssertionError(
                "unexpected directories remained under watched roots: "
                + " | ".join(leak_messages)
            )


def repo_temp_dir_guard_enabled() -> bool:
    return not _env_flag_enabled(ALLOW_TEST_DIR_LEAKS_ENV)


def managed_temp_root_guard_enabled() -> bool:
    return repo_temp_dir_guard_enabled() and not _env_flag_enabled(KEEP_TEST_ARTIFACTS_ENV)


def resolve_managed_temp_root(temp_root: str | Path | None = None) -> Path:
    configured_root = os.environ.get(TEST_TEMP_ROOT_ENV)
    root_value = temp_root if temp_root is not None else configured_root
    return (
        Path(root_value)
        if root_value is not None
        else Path(tempfile.gettempdir()) / DEFAULT_TEST_TEMP_ROOT_NAME
    ).resolve()


def create_repo_temp_dir_guard(repo_root: str | Path | None = None) -> DirectoryLeakGuard:
    root = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT
    return DirectoryLeakGuard(
        [
            DirectoryWatchSpec(
                root=root,
                ignore_name_patterns=(".pytest_cache",),
            ),
            DirectoryWatchSpec(
                root=root / "tests",
                ignore_name_patterns=("__pycache__",),
                recursive=True,
            ),
        ]
    )


def create_managed_temp_root_guard(
    temp_root: str | Path | None = None,
) -> DirectoryLeakGuard:
    return DirectoryLeakGuard(
        [DirectoryWatchSpec(root=resolve_managed_temp_root(temp_root))]
    )


class ManagedTempArtifacts:
    def __init__(
        self,
        *,
        test_id: str,
        temp_root: str | Path | None = None,
        keep_artifacts: bool | None = None,
        watch_roots: list[str | Path] | None = None,
    ) -> None:
        self.artifacts_root = resolve_managed_temp_root(temp_root)
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.keep_artifacts = (
            _env_flag_enabled(KEEP_TEST_ARTIFACTS_ENV)
            if keep_artifacts is None
            else keep_artifacts
        )
        self.test_id = test_id
        self.owner_root = self.artifacts_root / _slugify(test_id)
        self._created_dirs: list[Path] = []
        self._watch_guard = DirectoryLeakGuard.for_roots(watch_roots)

    def make_temp_dir(self, label: str = "workspace") -> Path:
        self.owner_root.mkdir(parents=True, exist_ok=True)
        path = self.owner_root / f"{_slugify(label)}-{uuid.uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        self._created_dirs.append(path)
        return path

    def cleanup(self) -> None:
        if not self.keep_artifacts:
            for path in sorted(
                {item.resolve() for item in self._created_dirs},
                key=lambda item: len(item.parts),
                reverse=True,
            ):
                shutil.rmtree(path, ignore_errors=True)
            if self.owner_root.exists():
                _prune_empty_parents(self.owner_root, stop_at=self.artifacts_root)

        self._watch_guard.assert_clean()


class ManagedTempArtifactsTestCase(unittest.TestCase):
    managed_temp_dir_label = "workspace"
    managed_temp_root_attr = "temp_root"
    managed_watch_roots: tuple[str | Path, ...] = (_DEFAULT_DOC_GOVERNOR_WATCH_ROOT,)

    def setUp(self) -> None:
        super().setUp()
        self.temp_artifacts = ManagedTempArtifacts(
            test_id=self.id(),
            watch_roots=list(self.managed_watch_roots),
        )
        setattr(
            self,
            self.managed_temp_root_attr,
            self.temp_artifacts.make_temp_dir(self.managed_temp_dir_label),
        )

    def tearDown(self) -> None:
        try:
            if hasattr(self, "temp_artifacts"):
                self.temp_artifacts.cleanup()
        finally:
            super().tearDown()
