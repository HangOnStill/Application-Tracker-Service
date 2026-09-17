def create_employer(client, name="Northstar Systems"):
    response = client.post("/api/v1/employers", json={"name": name, "website": "https://example.com"})
    assert response.status_code == 201
    return response.json()


def create_application(client, employer_id, **overrides):
    payload = {
        "employer_id": employer_id,
        "role_title": "Software Developer Intern",
        "location": "Ottawa, ON",
        "work_mode": "hybrid",
        "term_start": "2027-01-11",
        "term_length_months": 8,
        "status": "interested",
        "deadline": "2026-10-15T23:59:00Z",
        "application_url": "https://example.com/jobs/123",
        "language_requirement": "English",
    }
    payload.update(overrides)
    response = client.post("/api/v1/applications", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_application_and_filter(client):
    employer = create_employer(client)
    application = create_application(client, employer["id"])

    assert application["employer"]["name"] == "Northstar Systems"
    assert application["term_length_months"] == 8

    response = client.get("/api/v1/applications", params={"search": "northstar", "work_mode": "hybrid"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role_title"] == "Software Developer Intern"


def test_status_history_updates_current_status(client):
    employer = create_employer(client)
    application = create_application(client, employer["id"])

    response = client.post(
        f"/api/v1/applications/{application['id']}/status-history",
        json={"status": "applied", "note": "Submitted through synthetic demo portal"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "applied"

    detail = client.get(f"/api/v1/applications/{application['id']}")
    assert detail.json()["status"] == "applied"

    history = client.get(f"/api/v1/applications/{application['id']}/status-history")
    assert history.status_code == 200
    assert len(history.json()) == 2  # creation + explicit transition


def test_duplicate_employer_returns_conflict(client):
    create_employer(client)
    response = client.post("/api/v1/employers", json={"name": "Northstar Systems"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_missing_employer_returns_404(client):
    response = client.post(
        "/api/v1/applications",
        json={"employer_id": 999, "role_title": "Data Intern"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_term_length_requires_start_date(client):
    employer = create_employer(client)
    response = client.post(
        "/api/v1/applications",
        json={
            "employer_id": employer["id"],
            "role_title": "Backend Intern",
            "term_length_months": 8,
        },
    )
    assert response.status_code == 422
