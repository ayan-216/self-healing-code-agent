from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_audit_trigger_and_metrics_flow():
    # 1. Trigger Audit
    res = client.post("/api/v1/audits/trigger", json={
        "repo_path": ".",
        "repo_name": "test/api-repo"
    })
    assert res.status_code == 200
    audit_id = res.json()["audit_session_id"]
    assert audit_id is not None

    # 2. Query Audit Status
    res_get = client.get(f"/api/v1/audits/{audit_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == audit_id

    # 3. List Repositories
    res_repos = client.get("/api/v1/repositories/")
    assert res_repos.status_code == 200
    assert len(res_repos.json()) >= 1

    # 4. Check Metrics
    res_metrics = client.get("/api/v1/metrics/")
    assert res_metrics.status_code == 200
    assert "total_audits_evaluated" in res_metrics.json()
