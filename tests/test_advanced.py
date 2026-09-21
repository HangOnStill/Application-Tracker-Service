import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def employer(client, name="Northstar Systems"):
    response = client.post("/api/v1/employers", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def application(client, employer_id, role_title, **fields):
    response = client.post(
        "/api/v1/applications",
        json={"employer_id": employer_id, "role_title": role_title, **fields},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_paginated_search_keeps_legacy_list_and_reports_metadata(client):
    first_employer = employer(client)
    second_employer = employer(client, "Cedar Labs")
    application(client, first_employer, "Backend Developer", work_mode="remote")
    application(client, first_employer, "Data Engineer", work_mode="remote")
    application(client, second_employer, "Firmware Engineer", work_mode="onsite")

    params = {"employer_id": first_employer, "sort_by": "role_title", "sort_order": "asc", "limit": 1}
    first_page = client.get("/api/v1/applications/page", params=params)
    assert first_page.status_code == 200, first_page.text
    assert first_page.json()["total"] == 2
    assert first_page.json()["has_more"] is True
    assert first_page.json()["items"][0]["role_title"] == "Backend Developer"

    second_page = client.get("/api/v1/applications/page", params={**params, "offset": 1})
    assert second_page.status_code == 200
    assert second_page.json()["items"][0]["role_title"] == "Data Engineer"
    assert second_page.json()["has_more"] is False

    legacy = client.get("/api/v1/applications", params={"employer_id": first_employer})
    assert legacy.status_code == 200
    assert len(legacy.json()) == 2


def test_deadline_sort_and_invalid_query_validation(client):
    employer_id = employer(client)
    application(client, employer_id, "No deadline")
    application(client, employer_id, "Soon", deadline="2026-10-03T12:00:00Z")
    application(client, employer_id, "Later", deadline="2026-10-09T12:00:00Z")

    response = client.get("/api/v1/applications/page", params={"sort_by": "deadline", "sort_order": "asc"})
    assert response.status_code == 200, response.text
    assert [item["role_title"] for item in response.json()["items"]] == ["Soon", "Later", "No deadline"]

    invalid = client.get(
        "/api/v1/applications/page",
        params={"deadline_after": "2026-10-10T00:00:00Z", "deadline_before": "2026-10-01T00:00:00Z"},
    )
    assert invalid.status_code == 422
    assert client.get("/api/v1/applications/page", params={"sort_by": "unsafe"}).status_code == 422


def test_search_treats_sql_wildcards_as_literal_text(client):
    employer_id = employer(client)
    application(client, employer_id, "50% Engineer")
    application(client, employer_id, "Regular Engineer")
    response = client.get("/api/v1/applications/page", params={"search": "%"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["role_title"] == "50% Engineer"


def test_pipeline_summary_counts_open_deadlines_only(client):
    employer_id = employer(client)
    overdue = application(client, employer_id, "Overdue", deadline="2026-09-30T12:00:00Z")
    soon = application(client, employer_id, "Due soon", deadline="2026-10-03T12:00:00Z", status="applied")
    application(client, employer_id, "Later", deadline="2026-10-15T12:00:00Z")
    application(client, employer_id, "Rejected", deadline="2026-10-04T12:00:00Z", status="rejected")

    response = client.get(
        "/api/v1/analytics/pipeline",
        params={"as_of": "2026-10-01T12:00:00Z", "window_days": 7},
    )
    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["total"] == 4
    assert summary["active"] == 3
    assert summary["by_status"]["interested"] == 2
    assert summary["by_status"]["applied"] == 1
    assert summary["by_status"]["rejected"] == 1
    assert summary["overdue_deadlines"] == 1
    assert summary["due_soon"] == 1
    assert [item["application_id"] for item in summary["upcoming_deadlines"]] == [soon["id"]]
    assert overdue["id"] != soon["id"]

    assert client.get("/api/v1/analytics/pipeline", params={"as_of": "2026-10-01T12:00:00"}).status_code == 422


def test_api_key_protects_data_routes_but_not_health(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "synthetic-test-key")
    get_settings.cache_clear()
    try:
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/employers").status_code == 401
        assert client.get("/api/v1/employers", headers={"X-API-Key": "wrong"}).status_code == 401
        assert client.get("/api/v1/employers", headers={"X-API-Key": "synthetic-test-key"}).status_code == 200
    finally:
        monkeypatch.delenv("API_KEY", raising=False)
        get_settings.cache_clear()


def test_production_refuses_to_start_without_api_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="API_KEY must be configured"):
            with TestClient(app):
                pass
    finally:
        monkeypatch.delenv("APP_ENV", raising=False)
        get_settings.cache_clear()


def test_status_cannot_be_silently_changed_by_patch(client):
    employer_id = employer(client)
    item = application(client, employer_id, "Backend Developer")
    assert client.patch(f"/api/v1/applications/{item['id']}", json={"status": "offer"}).status_code == 422
    assert client.patch(f"/api/v1/applications/{item['id']}", json={"role_title": None}).status_code == 422
    assert client.get(f"/api/v1/applications/{item['id']}").json()["status"] == "interested"
