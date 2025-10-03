
import pytest
from flask import json
from unittest.mock import patch

@pytest.fixture
def mock_firebase_service():
    """Mock the firebase service."""
    with patch("app.api.auth.firebase_service") as mock:
        yield mock

@pytest.fixture
def mock_password_security():
    """Mock the password security functions."""
    with patch("app.api.auth.password_security") as mock:
        mock.check_password_strength.return_value = {"valid": True}
        yield mock

@pytest.fixture
def mock_anonymization_service():
    """Mock the anonymization service."""
    with patch("app.api.auth.anonymization_service") as mock:
        mock.generate_anonymous_id.return_value = "test_user_id"
        yield mock

def test_register_success(client, mock_firebase_service, mock_password_security, mock_anonymization_service):
    """Test successful user registration."""
    mock_firebase_service.get_user_profile.return_value = None
    mock_firebase_service.create_user_profile.return_value = "test_user_id"

    data = {
        "email": "test@example.com",
        "password": "ValidPassword123!",
        "terms_accepted": True
    }
    response = client.post("/api/auth/register", data=json.dumps(data), content_type="application/json")

    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert response_data["message"] == "Registration successful"
    assert response_data["user_id"] == "test_user_id"

def test_register_existing_user(client, mock_firebase_service, mock_password_security, mock_anonymization_service):
    """Test registration with an existing email."""
    mock_firebase_service.get_user_profile.return_value = {"id": "test_user_id"}

    data = {
        "email": "test@example.com",
        "password": "ValidPassword123!",
        "terms_accepted": True
    }
    response = client.post("/api/auth/register", data=json.dumps(data), content_type="application/json")

    assert response.status_code == 409
    response_data = json.loads(response.data)
    assert response_data["error"] == "User already exists"

def test_login_success(client, mock_firebase_service, mock_password_security, mock_anonymization_service):
    """Test successful user login."""
    mock_firebase_service.get_user_profile.return_value = {
        "id": "test_user_id",
        "password_hash": "hashed_password",
        "onboarding_completed": True
    }
    mock_password_security.verify_password.return_value = True

    data = {
        "email": "test@example.com",
        "password": "ValidPassword123!"
    }
    response = client.post("/api/auth/login", data=json.dumps(data), content_type="application/json")

    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["message"] == "Login successful"
    assert response_data["user_id"] == "test_user_id"

def test_login_invalid_credentials(client, mock_firebase_service, mock_password_security, mock_anonymization_service):
    """Test login with invalid credentials."""
    mock_firebase_service.get_user_profile.return_value = {
        "id": "test_user_id",
        "password_hash": "hashed_password"
    }
    mock_password_security.verify_password.return_value = False

    data = {
        "email": "test@example.com",
        "password": "InvalidPassword"
    }
    response = client.post("/api/auth/login", data=json.dumps(data), content_type="application/json")

    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert response_data["error"] == "Invalid credentials"

def test_login_non_existent_user(client, mock_firebase_service, mock_anonymization_service):
    """Test login with a non-existent user."""
    mock_firebase_service.get_user_profile.return_value = None

    data = {
        "email": "nonexistent@example.com",
        "password": "SomePassword"
    }
    response = client.post("/api/auth/login", data=json.dumps(data), content_type="application/json")

    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert response_data["error"] == "Invalid credentials"
