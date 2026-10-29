import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint returns 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_metrics_middleware_header():
    """Test that the metrics middleware adds the process time header."""
    response = client.get("/api/v1/health")
    assert "X-Process-Time" in response.headers

def test_logging_structured_format(caplog):
    """Test that logs are generated in a structured way during a request."""
    with caplog.at_level("INFO"):
        client.get("/api/v1/health")
        # Check if the metrics logger was called
        metrics_logs = [record for record in caplog.records if record.name == "app.metrics"]
        assert len(metrics_logs) > 0
        assert hasattr(metrics_logs[0], "method")
        assert metrics_logs[0].method == "GET"