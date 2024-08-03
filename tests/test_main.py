import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from database import Base

# Configure test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create a new SQLAlchemy engine instance
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a configured "Session" class
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create the database tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

def test_create_user(test_db):
    response = client.post(
        "/users/",
        json={
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "email": "johndoe@example.com",
            "city": "New York",
            "interests": ["reading", "traveling", "swimming"]
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "johndoe@example.com"

def test_read_users(test_db):
    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "johndoe@example.com"

def test_read_user(test_db):
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["email"] == "johndoe@example.com"

def test_update_user(test_db):
    response = client.put(
        "/users/1",
        json={
            "name": "John Updated",
            "age": 31,
            "gender": "male",
            "email": "johnupdated@example.com",
            "city": "New York",
            "interests": ["reading", "traveling", "swimming"]
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "johnupdated@example.com"

def test_find_matches(test_db):
    client.post(
        "/users/",
        json={
            "name": "Jane Doe",
            "age": 28,
            "gender": "female",
            "email": "janedoe@example.com",
            "city": "Los Angeles",
            "interests": ["reading", "yoga", "swimming"]
        },
    )
    response = client.get("/users/2/matches")
    assert response.status_code == 200
    matches = response.json()
    assert len(matches) > 0
    assert matches[0]["email"] == "johnupdated@example.com"

def test_delete_user(test_db):
    response = client.delete("/users/1")
    assert response.status_code == 200
    response = client.get("/users/1")
    assert response.status_code == 404