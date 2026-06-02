import ast
from pathlib import Path

import pytest

from app.application.llm.errors import LlmTransportConfigurationError
from app.infrastructure.llm.runtime import build_llm_transport_from_env


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
TEST_ROOT = REPO_ROOT / "tests"
FAKE_TRANSPORT_MODULE = "app.infrastructure.llm.fake_transport"
FAKE_CONTRACTS_MODULE = "app.infrastructure.llm.contracts"
INFRA_FAKE_PATH = APP_ROOT / "infrastructure" / "llm" / "fake_transport.py"
TEST_FAKE_FACADE_PATH = TEST_ROOT / "fakes" / "llm_transport.py"
LLM_RUNTIME_TEST_PATH = TEST_ROOT / "api" / "test_llm_runtime.py"


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _read_python_source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _fake_provider_name() -> str:
    return "".join(("fa", "ke"))


def _module_import_violations(path: Path) -> list[str]:
    tree = ast.parse(_read_python_source(path), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in {
            FAKE_TRANSPORT_MODULE,
            FAKE_CONTRACTS_MODULE,
        }:
            violations.append(f"{_relative(path)}:{node.lineno}: from {node.module} import ...")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {FAKE_TRANSPORT_MODULE, FAKE_CONTRACTS_MODULE}:
                    violations.append(f"{_relative(path)}:{node.lineno}: import {alias.name}")
    return violations


def _production_fake_name_violations(path: Path) -> list[str]:
    tree = ast.parse(_read_python_source(path), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == FAKE_TRANSPORT_MODULE:
            violations.append(f"{_relative(path)}:{node.lineno}: imports infrastructure fake transport")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == FAKE_TRANSPORT_MODULE:
                    violations.append(f"{_relative(path)}:{node.lineno}: imports infrastructure fake transport")
        elif isinstance(node, ast.Name) and node.id in {
            "FakeLlmTransport",
            "SUPPORTED_FAKE_TASK_TYPES",
        }:
            violations.append(f"{_relative(path)}:{node.lineno}: uses {node.id}")
        elif isinstance(node, ast.alias) and node.name in {
            "FakeLlmTransport",
            "SUPPORTED_FAKE_TASK_TYPES",
        }:
            violations.append(f"{_relative(path)}:{node.lineno}: imports {node.name}")
    return violations


def _llm_provider_fake_env_violations(path: Path) -> list[str]:
    tree = ast.parse(_read_python_source(path), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "setenv"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "LLM_PROVIDER"
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "fake"
        ):
            violations.append(f"{_relative(path)}:{node.lineno}: monkeypatch.setenv LLM_PROVIDER=fake")
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Attribute)
                and target.value.attr == "environ"
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == "LLM_PROVIDER"
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and node.value.value == "fake"
        ):
            violations.append(f"{_relative(path)}:{node.lineno}: os.environ LLM_PROVIDER=fake")
    return violations


def test_runtime_rejects_fake_provider_from_env_still(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", _fake_provider_name())

    with pytest.raises(LlmTransportConfigurationError):
        build_llm_transport_from_env()


def test_llm_infrastructure_package_does_not_export_fake_transport() -> None:
    import app.infrastructure.llm as llm_pkg

    assert not hasattr(llm_pkg, "FakeLlmTransport")
    assert "FakeLlmTransport" not in getattr(llm_pkg, "__all__", ())


def test_production_code_does_not_import_fake_transport_outside_fake_module() -> None:
    violations: list[str] = []
    for path in _python_files(APP_ROOT):
        if path == INFRA_FAKE_PATH:
            continue
        violations.extend(_production_fake_name_violations(path))

    assert violations == []


def test_tests_use_test_fake_facade_instead_of_infrastructure_fake_import() -> None:
    violations: list[str] = []
    for path in _python_files(TEST_ROOT):
        if path == TEST_FAKE_FACADE_PATH:
            continue
        violations.extend(_module_import_violations(path))

    assert violations == []


def test_no_api_success_path_uses_llm_provider_fake_env() -> None:
    violations: list[str] = []
    for path in _python_files(TEST_ROOT):
        if path == LLM_RUNTIME_TEST_PATH:
            continue
        violations.extend(_llm_provider_fake_env_violations(path))

    assert violations == []
