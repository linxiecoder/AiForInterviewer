import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"


def test_domain_layer_does_not_import_framework_or_infrastructure() -> None:
    violations = _find_forbidden_imports(
        APP_ROOT / "domain",
        forbidden_prefixes=("fastapi", "sqlalchemy", "pydantic", "app.infrastructure"),
    )

    assert violations == []


def test_api_layer_does_not_import_db_models_or_llm_transport() -> None:
    violations = _find_forbidden_imports(
        APP_ROOT / "api",
        forbidden_prefixes=("app.infrastructure.db.models", "app.infrastructure.llm"),
    )

    assert violations == []


def test_application_layer_does_not_import_fastapi_or_infrastructure() -> None:
    violations = _find_forbidden_imports(
        APP_ROOT / "application",
        forbidden_prefixes=("fastapi", "sqlalchemy", "app.infrastructure"),
    )

    assert violations == []


def test_auth_layers_keep_required_boundaries() -> None:
    domain_violations = _find_forbidden_imports(
        APP_ROOT / "domain" / "auth",
        forbidden_prefixes=("fastapi", "sqlalchemy", "pydantic", "app.infrastructure"),
    )
    application_violations = _find_forbidden_imports(
        APP_ROOT / "application" / "auth",
        forbidden_prefixes=("fastapi",),
    )
    api_violations = _find_forbidden_imports(
        APP_ROOT / "api" / "v1" / "auth.py",
        forbidden_prefixes=("app.infrastructure.db.models",),
    )

    assert domain_violations == []
    assert application_violations == []
    assert api_violations == []


def test_no_unbounded_utils_file_exists() -> None:
    assert list((APP_ROOT).rglob("utils.py")) == []


def test_pr2_ai_runtime_persistence_does_not_import_concrete_runtime_or_providers() -> None:
    concrete_runtime = "lang" + "graph"
    concrete_chain = "lang" + "chain"
    violations = _find_forbidden_imports(
        APP_ROOT / "infrastructure" / "db" / "repositories" / "ai_runtime",
        forbidden_prefixes=(
            concrete_runtime,
            concrete_chain,
            "app.application.agents",
            "app.infrastructure.ai_runtime." + concrete_runtime,
            "app.infrastructure.llm",
            "openai",
            "anthropic",
        ),
    )
    model_violations = _find_forbidden_imports(
        APP_ROOT / "infrastructure" / "db" / "models" / "ai_runtime.py",
        forbidden_prefixes=(concrete_runtime, concrete_chain, "app.infrastructure.llm", "openai", "anthropic"),
    )

    assert violations == []
    assert model_violations == []


def test_core_business_layers_do_not_import_ai_runtime_internals() -> None:
    violations = _find_forbidden_imports(
        APP_ROOT / "domain",
        forbidden_prefixes=(
            "app.infrastructure.db.models.ai_runtime",
            "app.infrastructure.db.repositories.ai_runtime",
        ),
    )
    violations.extend(
        _find_forbidden_imports(
            APP_ROOT / "application",
            forbidden_prefixes=(
                "app.infrastructure.db.models.ai_runtime",
                "app.infrastructure.db.repositories.ai_runtime",
            ),
        )
    )

    assert violations == []


def test_pr3_application_ai_runtime_keeps_contract_boundary() -> None:
    concrete_runtime = "lang" + "graph"
    concrete_chain = "lang" + "chain"
    violations = _find_forbidden_imports(
        APP_ROOT / "application" / "ai_runtime",
        forbidden_prefixes=(
            concrete_runtime,
            concrete_chain,
            "sqlalchemy",
            "app.infrastructure",
            "openai",
            "anthropic",
        ),
    )

    assert violations == []


def test_pr5_business_graph_boundary_does_not_import_concrete_runtime() -> None:
    concrete_runtime = "lang" + "graph"
    concrete_chain = "lang" + "chain"
    business_graph_dir = "business_" + "graphs"

    assert (APP_ROOT / "infrastructure" / "ai_runtime" / concrete_runtime).exists()
    assert sorted(
        path.name for path in (APP_ROOT / "application" / "ai_runtime" / business_graph_dir).glob("*.py")
    ) == ["__init__.py", "local_multi_agent_orchestrator.py", "polish_feedback_graph.py", "polish_question_graph.py"]
    assert _find_forbidden_imports(
        APP_ROOT / "application",
        forbidden_prefixes=(concrete_runtime, concrete_chain),
    ) == []
    assert _find_forbidden_imports(
        APP_ROOT / "api",
        forbidden_prefixes=(concrete_runtime, concrete_chain),
    ) == []
    assert _find_forbidden_imports(
        APP_ROOT / "domain",
        forbidden_prefixes=(concrete_runtime, concrete_chain),
    ) == []


def test_shared_kernel_objects_are_reusable() -> None:
    from app.application.ai_tasks.commands import CreateAiTaskCommand
    from app.application.scoring.commands import CreateScoringTaskCommand
    from app.domain.shared.enums import ScoreType
    from app.domain.shared.refs import ResourceRef

    resume_ref = ResourceRef(resource_type="resume", resource_id="res_demo")

    ai_command = CreateAiTaskCommand(
        task_type="job_match_analysis",
        contract_ids=("P-JOBMATCH-001",),
        input_refs=(resume_ref,),
    )
    scoring_command = CreateScoringTaskCommand(score_type=ScoreType.JOB_MATCH, target_ref=resume_ref)

    assert ai_command.input_refs[0] == scoring_command.target_ref


def _find_forbidden_imports(root: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module_names: list[str] = []
            if isinstance(node, ast.Import):
                module_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_names.append(node.module)
            for module_name in module_names:
                if module_name.startswith(forbidden_prefixes):
                    rel = path.relative_to(REPO_ROOT)
                    violations.append(f"{rel}: {module_name}")
    return violations
