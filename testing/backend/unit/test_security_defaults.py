"""Deployment defaults and coarse guard must not leak clinical error context."""
import logging

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.routing import Route

from backend.core.config import Settings, settings
from backend.main import app, global_exception_handler


def test_origins_are_explicit():
    assert "*" not in Settings().ALLOWED_ORIGINS
    with pytest.raises(ValueError, match="explicit origins"):
        Settings(ALLOWED_ORIGINS=["*"])


def test_optional_token_denies_history_and_reports(monkeypatch):
    monkeypatch.setattr(settings, "API_TOKEN", "test-only-secret")
    with TestClient(app) as client:
        for path in ("/api/v1/history", "/api/v1/assessments/unknown/report", "/api/v1/benchmarks"):
            denied = client.get(path)
            assert denied.status_code == 401
            assert denied.headers["Cache-Control"] == "no-store"
            assert denied.headers["X-Content-Type-Options"] == "nosniff"
        # A correct token reaches routing; an unknown endpoint is now 404, not 401.
        assert client.get("/api/v1/unknown", headers={"Authorization": "Bearer test-only-secret"}).status_code == 404
        assert client.get("/health").status_code != 401


def test_cors_rejects_unlisted_origin_and_allows_preflight(monkeypatch):
    monkeypatch.setattr(settings, "API_TOKEN", "test-only-secret")
    with TestClient(app) as client:
        for origin, allowed in (("http://localhost:5173", True), ("https://untrusted.example", False)):
            response = client.options("/api/v1/predict", headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            })
            assert response.status_code == (200 if allowed else 400)
            assert response.headers.get("Access-Control-Allow-Origin") == (origin if allowed else None)


def test_unhandled_route_error_does_not_escape_to_server_logger(caplog):
    def failing_endpoint(request):
        raise ValueError("private-glucose-value=321")

    route = Route("/privacy-test-only", failing_endpoint)
    app.router.routes.append(route)
    try:
        with caplog.at_level(logging.ERROR), TestClient(app) as client:
            # Default TestClient re-raises server exceptions if they escape.
            response = client.get("/privacy-test-only")
        assert response.status_code == 500
        assert "private-glucose-value" not in response.text + caplog.text
        assert all(record.exc_info is None for record in caplog.records)
    finally:
        app.router.routes.remove(route)


@pytest.mark.asyncio
async def test_error_logs_exclude_payload_path_and_traceback(caplog):
    request = Request({"type": "http", "path": "/patient/private-identifier", "method": "POST", "headers": []})
    with caplog.at_level(logging.ERROR, logger="CardioVision"):
        response = await global_exception_handler(request, ValueError("private-glucose-value=321"))
    assert response.status_code == 500
    assert "ValueError" in caplog.text
    assert "private-identifier" not in caplog.text
    assert "private-glucose-value" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)
