import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = REPO_ROOT / "tests"
DOC_POLICY_PATH = REPO_ROOT / "docs" / "00-governance" / "TEST_POLICY.md"
ALLOWED_FILES = {
    TEST_ROOT / "doc_governor" / "test_temp_artifacts.py",
    TEST_ROOT / "test_temp_artifact_policy.py",
}
TEMP_DIR_NAME_REGEX = r"^(?:_?tmp|temp)(?:[-_].*)?$"
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
        re.compile(r"Path\(__file__\)[^\n]*[\"'](?:_?tmp|temp)(?:[-_].*)?[\"']"),
        "测试不得在仓库目录下直接拼接 _tmp/tmp/temp 目录名；请改用 ManagedTempArtifacts。",
    ),
    (
        re.compile(r"\bPath\s*\(\s*[\"'](?:_?tmp|temp)(?:[-_][^\"']*)?[\"']\s*\)"),
        "测试不得直接构造 Path('tmp...') / Path(\"tmp...\")；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
    ),
    (
        re.compile(r"\b(?:os\.)?mkdir\s*\(\s*[\"'](?:_?tmp|temp)(?:[-_][^\"']*)?[\"']"),
        "测试不得直接 mkdir('tmp...') / os.mkdir('tmp...')；请改用 ManagedTempArtifacts / ManagedTempArtifactsTestCase。",
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
        policy_targets = list(TEST_ROOT.rglob("test_*.py"))
        conftest_path = TEST_ROOT / "conftest.py"
        if conftest_path.exists():
            policy_targets.append(conftest_path)
        for path in sorted(set(policy_targets)):
            text = path.read_text(encoding="utf-8")
            violations.extend(_collect_policy_violations(path, text))

        self.assertEqual([], violations, "\n".join(violations))

    def test_policy_messages_do_not_suggest_banned_pytest_temp_fixtures(self) -> None:
        messages = "\n".join(message for _, message in PROHIBITED_PATTERNS)
        self.assertNotIn("pytest tmp_path", messages)
        self.assertNotIn("pytest 提供的 `tmp_path` / `tmp_path_factory`", messages)

    def test_test_policy_doc_matches_managed_temp_strategy(self) -> None:
        text = DOC_POLICY_PATH.read_text(encoding="utf-8")
        self.assertIn("`ManagedTempArtifacts` / `ManagedTempArtifactsTestCase`", text)
        self.assertIn("不得直接使用 `tmp_path` / `tmp_path_factory`", text)
        self.assertIn("AI_FOR_INTERVIEWER_KEEP_TEST_ARTIFACTS", text)
        self.assertIn("AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS", text)
        self.assertIn("tests/test_temp_artifact_policy.py", text)
        self.assertIn("tests/doc_governor/test_temp_artifacts.py", text)
        self.assertNotIn("或 pytest 提供的 `tmp_path` / `tmp_path_factory`", text)

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

    def test_temp_dir_name_regex_covers_extended_variants(self) -> None:
        pattern = re.compile(TEMP_DIR_NAME_REGEX)
        should_match = [
            "tmp",
            "_tmp",
            "temp",
            "tmp-readiness-verify",
            "tmp_inspect",
            "tmp_official_scope",
            "tmp_xxx",
            "tmp-xxx",
            "_tmp_xxx",
            "temp_xxx",
            "temp-xxx",
        ]
        should_not_match = [
            ".tmp",
            "template",
            "attempt",
            "tmpx",
            "tempx",
            "prod_tmp",
            "my-temp",
        ]
        for name in should_match:
            self.assertIsNotNone(pattern.fullmatch(name), name)
        for name in should_not_match:
            self.assertIsNone(pattern.fullmatch(name), name)

    def test_policy_rejects_extended_tmp_temp_directory_literals(self) -> None:
        variants = [
            "tmp-readiness-verify",
            "tmp_inspect",
            "tmp_official_scope",
            "tmp_xxx",
            "tmp-xxx",
            "_tmp_xxx",
            "temp_xxx",
            "temp-xxx",
        ]
        for name in variants:
            source = f'''
from pathlib import Path

def test_demo():
    p = Path(__file__).parent / "{name}"
    return p
'''
            sample_name = name.replace("-", "_")
            violations = _collect_policy_violations(
                TEST_ROOT / f"policy_tmp_name_{sample_name}.py",
                source,
            )
            self.assertTrue(
                any("ManagedTempArtifacts" in item for item in violations),
                (name, violations),
            )

    def test_policy_rejects_direct_path_tmp_constructor(self) -> None:
        source = """
from pathlib import Path

def test_demo():
    p = Path("tmp-readiness-verify")
    return p
"""
        violations = _collect_policy_violations(
            TEST_ROOT / "policy_path_tmp_constructor.py",
            source,
        )
        self.assertTrue(
            any("Path('tmp...')" in item or 'Path("tmp...")' in item for item in violations),
            violations,
        )

    def test_policy_rejects_direct_mkdir_tmp_literal(self) -> None:
        source = """
import os

def test_demo():
    os.mkdir("tmp_inspect")
"""
        violations = _collect_policy_violations(
            TEST_ROOT / "policy_mkdir_tmp_literal.py",
            source,
        )
        self.assertTrue(any("mkdir('tmp...')" in item for item in violations), violations)


if __name__ == "__main__":
    unittest.main()
