from fastapi.testclient import TestClient
from main import app


def test_metrics_endpoint():
    client = TestClient(app)
    r = client.get("/metrics")
    # FastAPI router returns the Prometheus metrics response
    assert r.status_code == 200
    assert "python_info" in r.text or "http_requests_total" in r.text

