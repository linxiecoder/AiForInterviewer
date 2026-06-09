"""Phase 0 route and capability preservation inventory guards."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

from app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RouteExpectation:
    capability: str
    path: str
    methods: frozenset[str]
    endpoint_module_prefix: str


IMPLEMENTED_ROUTE_EXPECTATIONS = (
    RouteExpectation("Resume", "/api/v1/resumes", frozenset({"GET", "POST"}), "app.api.v1.resumes"),
    RouteExpectation("Resume", "/api/v1/resumes/{resume_id}", frozenset({"GET", "PATCH", "DELETE"}), "app.api.v1.resumes"),
    RouteExpectation("Job", "/api/v1/jobs", frozenset({"GET", "POST"}), "app.api.v1.jobs"),
    RouteExpectation("Job", "/api/v1/jobs/{job_id}", frozenset({"GET", "PATCH", "DELETE"}), "app.api.v1.jobs"),
    RouteExpectation(
        "Binding",
        "/api/v1/resume-job-bindings",
        frozenset({"POST"}),
        "app.api.v1.bindings",
    ),
    RouteExpectation(
        "Binding",
        "/api/v1/resume-job-bindings/{binding_id}",
        frozenset({"DELETE"}),
        "app.api.v1.bindings",
    ),
    RouteExpectation("Assets", "/api/v1/assets", frozenset({"GET", "POST"}), "app.api.v1.assets"),
    RouteExpectation(
        "Assets",
        "/api/v1/assets/{asset_id}",
        frozenset({"GET", "DELETE"}),
        "app.api.v1.assets",
    ),
)


PREFIX_ONLY_SKELETON_MODULES = {
    "ai-tasks": {
        "api_module": "app.api.v1.ai_tasks",
        "api_path": "apps/api/app/api/v1/ai_tasks.py",
        "api_prefix": "/api/v1/ai-tasks",
        "use_case_path": "apps/api/app/application/ai_tasks/use_cases.py",
        "skeleton_marker": "ai_task_skeleton",
    },
    "pressure": {
        "api_module": "app.api.v1.pressure",
        "api_path": "apps/api/app/api/v1/pressure.py",
        "api_prefix": "/api/v1/pressure-sessions",
        "use_case_path": "apps/api/app/application/pressure/use_cases.py",
        "skeleton_marker": "pressure_skeleton",
    },
    "reports": {
        "api_module": "app.api.v1.reports",
        "api_path": "apps/api/app/api/v1/reports.py",
        "api_prefix": "/api/v1/reports",
        "use_case_path": "apps/api/app/application/reports/use_cases.py",
        "skeleton_marker": "report_skeleton",
    },
    "reviews": {
        "api_module": "app.api.v1.reviews",
        "api_path": "apps/api/app/api/v1/reviews.py",
        "api_prefix": "/api/v1/reviews",
        "use_case_path": "apps/api/app/application/reviews/use_cases.py",
        "skeleton_marker": "review_skeleton",
    },
    "scoring": {
        "api_module": "app.api.v1.scoring",
        "api_path": "apps/api/app/api/v1/scoring.py",
        "api_prefix": "/api/v1/scoring-results",
        "use_case_path": "apps/api/app/application/scoring/use_cases.py",
        "skeleton_marker": "scoring_skeleton",
    },
}


CURRENT_ROUTE_CONTRACT_SNAPSHOT = (
    ("GET", "/api/v1/assets", "app.api.v1.assets.list_assets"),
    ("POST", "/api/v1/assets", "app.api.v1.assets.create_asset"),
    ("DELETE", "/api/v1/assets/{asset_id}", "app.api.v1.assets.delete_asset"),
    ("GET", "/api/v1/assets/{asset_id}", "app.api.v1.assets.get_asset"),
    ("POST", "/api/v1/assets/{asset_id}/archive", "app.api.v1.assets.archive_asset"),
    ("POST", "/api/v1/assets/{asset_id}/unarchive", "app.api.v1.assets.unarchive_asset"),
    ("POST", "/api/v1/auth/login", "app.api.v1.auth.login"),
    ("POST", "/api/v1/auth/logout", "app.api.v1.auth.logout"),
    ("GET", "/api/v1/auth/me", "app.api.v1.auth.me"),
    ("GET", "/api/v1/contract-baseline", "app.api.v1.contract_baseline.get_contract_baseline"),
    ("GET", "/api/v1/health", "app.api.v1.health.health"),
    ("POST", "/api/v1/job-match-analyses", "app.api.v1.job_match_analyses.create_job_match_analysis"),
    ("GET", "/api/v1/job-match-analyses/latest", "app.api.v1.job_match_analyses.get_latest_job_match_analysis"),
    ("GET", "/api/v1/job-match-analyses/{analysis_id}", "app.api.v1.job_match_analyses.get_job_match_analysis"),
    ("GET", "/api/v1/jobs", "app.api.v1.jobs.list_jobs"),
    ("POST", "/api/v1/jobs", "app.api.v1.jobs.create_job"),
    ("DELETE", "/api/v1/jobs/{job_id}", "app.api.v1.jobs.delete_job"),
    ("GET", "/api/v1/jobs/{job_id}", "app.api.v1.jobs.get_job"),
    ("PATCH", "/api/v1/jobs/{job_id}", "app.api.v1.jobs.patch_job"),
    ("GET", "/api/v1/polish-candidates", "app.api.v1.polish_candidates.list_polish_candidates"),
    ("GET", "/api/v1/polish-candidates/{candidate_id}", "app.api.v1.polish_candidates.get_polish_candidate"),
    ("POST", "/api/v1/polish-candidates/{candidate_id}/archive", "app.api.v1.polish_candidates.archive_polish_candidate"),
    ("POST", "/api/v1/polish-candidates/{candidate_id}/confirm", "app.api.v1.polish_candidates.confirm_polish_candidate"),
    ("POST", "/api/v1/polish-candidates/{candidate_id}/dismiss", "app.api.v1.polish_candidates.dismiss_polish_candidate"),
    ("POST", "/api/v1/polish-candidates/{candidate_id}/merge", "app.api.v1.polish_candidates.merge_polish_candidate"),
    ("GET", "/api/v1/polish-sessions", "app.api.v1.polish.list_polish_sessions"),
    ("POST", "/api/v1/polish-sessions", "app.api.v1.polish.create_polish_session"),
    ("GET", "/api/v1/polish-sessions/{session_id}", "app.api.v1.polish.get_polish_session"),
    ("POST", "/api/v1/polish-sessions/{session_id}/answers", "app.api.v1.polish.create_polish_answer"),
    ("POST", "/api/v1/polish-sessions/{session_id}/delete", "app.api.v1.polish.soft_delete_polish_session"),
    ("POST", "/api/v1/polish-sessions/{session_id}/end", "app.api.v1.polish.end_polish_session"),
    ("POST", "/api/v1/polish-sessions/{session_id}/feedback", "app.api.v1.polish.create_polish_feedback_task"),
    ("POST", "/api/v1/polish-sessions/{session_id}/progress-tree/generate", "app.api.v1.polish.generate_initial_polish_progress_tree"),
    ("POST", "/api/v1/polish-sessions/{session_id}/progress-tree/state", "app.api.v1.polish.refresh_polish_progress_tree_state"),
    ("POST", "/api/v1/polish-sessions/{session_id}/questions", "app.api.v1.polish.create_polish_question_task"),
    ("POST", "/api/v1/polish-sessions/{session_id}/questions/{question_id}/complete", "app.api.v1.polish.complete_polish_question"),
    ("POST", "/api/v1/polish-sessions/{session_id}/report", "app.api.v1.polish.generate_polish_session_report"),
    ("GET", "/api/v1/polish-topics", "app.api.v1.polish.list_polish_topics"),
    ("POST", "/api/v1/resume-job-bindings", "app.api.v1.bindings.create_binding"),
    ("DELETE", "/api/v1/resume-job-bindings/{binding_id}", "app.api.v1.bindings.delete_binding"),
    ("GET", "/api/v1/resumes", "app.api.v1.resumes.list_resumes"),
    ("POST", "/api/v1/resumes", "app.api.v1.resumes.create_resume"),
    ("DELETE", "/api/v1/resumes/{resume_id}", "app.api.v1.resumes.delete_resume"),
    ("GET", "/api/v1/resumes/{resume_id}", "app.api.v1.resumes.get_resume"),
    ("PATCH", "/api/v1/resumes/{resume_id}", "app.api.v1.resumes.patch_resume"),
    ("GET", "/api/v1/training-suggestions", "app.api.v1.training.list_training_suggestions"),
    ("POST", "/api/v1/training-suggestions/{recommendation_id}/dismiss", "app.api.v1.training.dismiss_training_suggestion"),
    ("POST", "/api/v1/training-suggestions/{recommendation_id}/tasks", "app.api.v1.training.start_training_task"),
    ("POST", "/api/v1/training-suggestions/{recommendation_id}/tasks/{task_id}/complete", "app.api.v1.training.complete_training_task"),
    ("GET", "/api/v1/weaknesses", "app.api.v1.weaknesses.list_weaknesses"),
    ("DELETE", "/api/v1/weaknesses/{weakness_id}", "app.api.v1.weaknesses.delete_weakness"),
    ("GET", "/api/v1/weaknesses/{weakness_id}", "app.api.v1.weaknesses.get_weakness"),
    ("POST", "/api/v1/weaknesses/{weakness_id}/status", "app.api.v1.weaknesses.update_weakness_status"),
)


def test_current_route_contract_snapshot_matches_phase0_baseline() -> None:
    assert _route_contract_snapshot() == CURRENT_ROUTE_CONTRACT_SNAPSHOT


def test_declared_implemented_route_capabilities_have_real_handlers() -> None:
    routes = _routes_by_path()

    for expectation in IMPLEMENTED_ROUTE_EXPECTATIONS:
        assert expectation.path in routes, expectation
        methods = {
            method
            for route in routes[expectation.path]
            for method in _route_methods(route)
        }
        assert expectation.methods <= methods, expectation
        endpoint_modules = {
            route.endpoint.__module__
            for route in routes[expectation.path]
            if _route_methods(route) & expectation.methods
        }
        assert endpoint_modules
        assert all(
            module.startswith(expectation.endpoint_module_prefix)
            for module in endpoint_modules
        ), expectation


def test_prefix_only_skeleton_modules_are_detected_but_not_registered_as_routes() -> None:
    app_paths = {route.path for route in create_app().routes if getattr(route, "path", "").startswith("/api/v1")}

    for capability, expected in PREFIX_ONLY_SKELETON_MODULES.items():
        module = importlib.import_module(expected["api_module"])
        router = getattr(module, "router")
        assert router.prefix == expected["api_prefix"].removeprefix("/api/v1"), capability
        assert router.routes == [], capability
        assert expected["api_prefix"] not in app_paths, capability
        assert not any(path.startswith(f"{expected['api_prefix']}/") for path in app_paths), capability

        route_source = (REPO_ROOT / expected["api_path"]).read_text(encoding="utf-8")
        assert "APIRouter" in route_source, capability
        assert "@router." not in route_source, capability

        use_case_source = (REPO_ROOT / expected["use_case_path"]).read_text(encoding="utf-8")
        assert expected["skeleton_marker"] in use_case_source, capability


def _route_contract_snapshot() -> tuple[tuple[str, str, str], ...]:
    snapshot: list[tuple[str, str, str]] = []
    for route in create_app().routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/v1"):
            continue
        endpoint = getattr(route, "endpoint", None)
        endpoint_ref = f"{endpoint.__module__}.{endpoint.__name__}"
        for method in sorted(_route_methods(route)):
            snapshot.append((method, path, endpoint_ref))
    return tuple(sorted(snapshot, key=lambda item: (item[1], item[0], item[2])))


def _routes_by_path() -> dict[str, list[object]]:
    routes: dict[str, list[object]] = {}
    for route in create_app().routes:
        path = getattr(route, "path", "")
        if path.startswith("/api/v1"):
            routes.setdefault(path, []).append(route)
    return routes


def _route_methods(route: object) -> set[str]:
    methods = getattr(route, "methods", None) or set()
    return set(methods) - {"HEAD", "OPTIONS"}
