from app.main import create_app


FORBIDDEN_ROUTE_PARTS = {
    "export",
    "download",
    "upload",
    "pdf",
    "docx",
    "files",
}


def test_route_inventory_keeps_health_and_contract_baseline() -> None:
    app = create_app()
    paths = {route.path for route in app.routes if hasattr(route, "path")}

    assert "/api/v1/health" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/contract-baseline" in paths
    assert "/api/v1/auth/session" not in paths


def test_route_inventory_registers_job_match_analysis_routes() -> None:
    app = create_app()
    paths = {route.path for route in app.routes if hasattr(route, "path")}

    assert "/api/v1/job-match-analyses" in paths
    assert "/api/v1/job-match-analyses/{analysis_id}" in paths
    assert "/api/v1/job-match-analyses/latest" in paths


def test_route_inventory_registers_polish_core_routes() -> None:
    app = create_app()
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods_by_path.setdefault(route.path, set()).update(route.methods or set())

    assert "/api/v1/polish-topics" in paths
    assert "/api/v1/polish-sessions" in paths
    assert {"GET", "POST"}.issubset(methods_by_path["/api/v1/polish-sessions"])
    assert "/api/v1/polish-sessions/{session_id}" in paths
    assert "/api/v1/polish-sessions/{session_id}/questions" in paths
    assert {"POST"}.issubset(methods_by_path["/api/v1/polish-sessions/{session_id}/questions"])
    assert "/api/v1/polish-sessions/{session_id}/feedback/{feedback_id}/next-question" in paths
    assert "/api/v1/polish-sessions/{session_id}/answers" in paths
    assert "/api/v1/polish-sessions/{session_id}/feedback" in paths
    assert "/api/v1/polish-sessions/{session_id}/progress-tree/generate" in paths
    assert {"POST"}.issubset(methods_by_path["/api/v1/polish-sessions/{session_id}/progress-tree/generate"])
    assert "/api/v1/polish-candidates" in paths
    assert "/api/v1/polish-candidates/{candidate_id}" in paths
    assert {"GET"}.issubset(methods_by_path["/api/v1/polish-candidates"])
    assert {"GET"}.issubset(methods_by_path["/api/v1/polish-candidates/{candidate_id}"])
    assert "/api/v1/polish-candidates/{candidate_id}/confirm" in paths
    assert "/api/v1/polish-candidates/{candidate_id}/dismiss" in paths
    assert "/api/v1/polish-candidates/{candidate_id}/merge" in paths
    assert "/api/v1/polish-candidates/{candidate_id}/archive" in paths
    assert {"POST"}.issubset(methods_by_path["/api/v1/polish-candidates/{candidate_id}/confirm"])
    assert {"POST"}.issubset(methods_by_path["/api/v1/polish-candidates/{candidate_id}/dismiss"])
    assert {"POST"}.issubset(methods_by_path["/api/v1/polish-candidates/{candidate_id}/merge"])
    assert {"POST"}.issubset(methods_by_path["/api/v1/polish-candidates/{candidate_id}/archive"])


def test_baseline_route_inventory_has_no_export_download_or_upload_routes() -> None:
    app = create_app()
    api_paths = [
        route.path.lower()
        for route in app.routes
        if hasattr(route, "path") and route.path.startswith("/api/v1")
    ]

    assert api_paths
    assert not [
        path
        for path in api_paths
        for forbidden in FORBIDDEN_ROUTE_PARTS
        if forbidden in path
    ]
