import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import Base, get_db
from app.config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture
def test_user(client, test_user_data):
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 200
    return response.json()

@pytest.fixture
def auth_headers(test_user):
    return {
        "Authorization": f"Bearer {test_user['access_token']}"
    }