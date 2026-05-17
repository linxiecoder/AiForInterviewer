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
    assert "/api/v1/contract-baseline" in paths


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

