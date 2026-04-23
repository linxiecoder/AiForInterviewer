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
_TRUE_VALUES = {"1", "true", "yes", "on"}
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DOC_GOVERNOR_WATCH_ROOT = _REPO_ROOT / "tests" / "doc_governor"


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


def _snapshot_child_directories(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {child.name for child in root.iterdir() if child.is_dir()}


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


@dataclass(frozen=True)
class DirectoryWatchSpec:
    root: Path
    ignore_name_patterns: tuple[str, ...] = ()

    def resolved(self) -> "DirectoryWatchSpec":
        return DirectoryWatchSpec(
            root=self.root.resolve(),
            ignore_name_patterns=tuple(self.ignore_name_patterns),
        )


class DirectoryLeakGuard:
    def __init__(self, watch_specs: list[DirectoryWatchSpec]) -> None:
        self._watch_snapshots: list[tuple[DirectoryWatchSpec, set[str]]] = [
            (spec.resolved(), _snapshot_child_directories(spec.root.resolve()))
            for spec in watch_specs
        ]

    @classmethod
    def for_roots(cls, roots: list[str | Path] | None = None) -> "DirectoryLeakGuard":
        specs = [DirectoryWatchSpec(root=Path(root)) for root in (roots or [])]
        return cls(specs)

    def find_unexpected_directories(self) -> list[str]:
        leak_messages: list[str] = []
        for spec, before in self._watch_snapshots:
            after = _snapshot_child_directories(spec.root)
            leaked = sorted(
                name
                for name in (after - before)
                if not any(fnmatch.fnmatch(name, pattern) for pattern in spec.ignore_name_patterns)
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


def create_repo_temp_dir_guard(repo_root: str | Path | None = None) -> DirectoryLeakGuard:
    root = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT
    return DirectoryLeakGuard(
        [
            DirectoryWatchSpec(
                root=root,
                ignore_name_patterns=(".pytest_cache", "pytest-cache-files-*"),
            ),
            DirectoryWatchSpec(
                root=root / "tests" / "doc_governor",
                ignore_name_patterns=("__pycache__",),
            ),
        ]
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
        configured_root = os.environ.get(TEST_TEMP_ROOT_ENV)
        root_value = temp_root if temp_root is not None else configured_root
        self.artifacts_root = (
            Path(root_value)
            if root_value is not None
            else Path(tempfile.gettempdir()) / DEFAULT_TEST_TEMP_ROOT_NAME
        ).resolve()
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
