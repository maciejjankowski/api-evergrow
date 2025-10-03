
import pytest
from flask import json
from app import create_app

def test_create_app():
    """Test that the app is created correctly."""
    app = create_app("testing")
    assert app is not None
    assert app.config["TESTING"] is True

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
