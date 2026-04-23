import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = REPO_ROOT / "tests"
ALLOWED_FILES = {
    TEST_ROOT / "doc_governor" / "test_temp_artifacts.py",
    TEST_ROOT / "test_temp_artifact_policy.py",
}
PROHIBITED_PATTERNS = (
    (
        re.compile(r"\btempfile\.gettempdir\s*\("),
        "测试不得直接调用 tempfile.gettempdir()；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"\btempfile\.mkdtemp\s*\("),
        "测试不得直接调用 tempfile.mkdtemp()；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"\bTemporaryDirectory\s*\("),
        "测试不得直接使用 TemporaryDirectory；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"\btempfile\.NamedTemporaryFile\s*\("),
        "测试不得直接使用 NamedTemporaryFile；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"\btempfile\.mkstemp\s*\("),
        "测试不得直接调用 tempfile.mkstemp()；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"\btempfile\.TemporaryFile\s*\("),
        "测试不得直接使用 TemporaryFile；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"\b(?:tmp_path|tmp_path_factory|pytester|runpytest(?:_subprocess)?)\b"),
        "测试不得直接使用 pytest 临时目录/pytester 夹具；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"shutil\.rmtree\s*\("),
        "测试不得手写 rmtree 清理测试目录；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"Path\(__file__\)[^\n]*[\"'](?:_tmp|tmp|temp)[\"']"),
        "测试不得在仓库目录下直接拼接 _tmp/tmp/temp 目录名；请改用 ManagedTempArtifacts。",
    ),
)


def _collect_policy_violations(path: Path, text: str) -> list[str]:
    violations: list[str] = []
    if path in ALLOWED_FILES:
        return violations

    relative = path.relative_to(REPO_ROOT).as_posix()
    for pattern, message in PROHIBITED_PATTERNS:
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            violations.append(f"{relative}:{line_no}: {message}")
    return violations


class TestTempArtifactPolicyTests(unittest.TestCase):
    def test_tests_do_not_reintroduce_forbidden_temp_dir_patterns(self) -> None:
        violations: list[str] = []
        for path in sorted(TEST_ROOT.rglob("test_*.py")):
            text = path.read_text(encoding="utf-8")
            violations.extend(_collect_policy_violations(path, text))

        self.assertEqual([], violations, "\n".join(violations))

    def test_policy_rejects_pytest_temp_fixtures(self) -> None:
        source = """
import pytest


def test_demo(tmp_path, pytester):
    tmp_path.mkdir()
    pytester.makepyfile("pass")
"""
        violations = _collect_policy_violations(
            TEST_ROOT / "policy_fixture_sample.py",
            source,
        )
        self.assertTrue(
            any("pytest 临时目录/pytester" in item for item in violations),
            violations,
        )

    def test_policy_rejects_named_temporary_file_and_rmtree(self) -> None:
        source = """
import shutil
import tempfile


def test_demo():
    temp = tempfile.NamedTemporaryFile(delete=False)
    shutil.rmtree(temp.name)
"""
        violations = _collect_policy_violations(
            TEST_ROOT / "policy_named_tempfile_sample.py",
            source,
        )
        self.assertTrue(any("NamedTemporaryFile" in item for item in violations), violations)
        self.assertTrue(any("rmtree" in item for item in violations), violations)


if __name__ == "__main__":
    unittest.main()
