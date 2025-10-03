
import pytest
from flask import json

def test_get_profile_requires_auth(client):
    """Test that getting a profile requires authentication."""
    response = client.get("/api/user/profile")
    assert response.status_code == 401

def test_update_profile_requires_auth(client):
    """Test that updating a profile requires authentication."""
    response = client.put("/api/user/profile", data=json.dumps({}), content_type="application/json")
    assert response.status_code == 401
