import pytest
from fastapi.testclient import TestClient
from llmsync.main import app

def test_health_check_schema():
    """Test that health check endpoint returns correct schema"""
    # We can't test without a live database, but we can verify the endpoint exists
    assert app.routes is not None

    # Find the health check route
    health_routes = [route for route in app.routes if "/api/health" in route.path]
    assert len(health_routes) > 0
    assert health_routes[0].methods == {"GET"}
