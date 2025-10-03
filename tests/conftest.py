
import pytest
from app import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app("testing")
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
