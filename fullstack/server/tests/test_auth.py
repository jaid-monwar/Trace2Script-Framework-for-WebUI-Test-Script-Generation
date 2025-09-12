import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

sys.path.append(".")

from src.api.main import app
from src.api.models.user import User
from src.api.services.security import hash_password


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    hashed_password = hash_password("testpassword")
    test_user = User(username="testuser", hashed_password=hashed_password)
    session.add(test_user)
    session.commit()
    
    client = TestClient(app)
    yield client


def test_login_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client: TestClient):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Incorrect username or password"


def test_protected_endpoint(client: TestClient):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "testpassword"},
    )
    token = response.json()["access_token"]
    
    response = client.get(
        "/api/v1/hello/protected",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, testuser!"
    assert data["protected"] is True


def test_protected_endpoint_no_token(client: TestClient):
    response = client.get("/api/v1/hello/protected")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Not authenticated"