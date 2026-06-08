"""Shared pytest fixtures — in-memory SQLite and seeded demo data."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app
from app.inventory.models import Category, Product
from app.users import service as user_service
from app.users.models import User, UserProfile
from app.users.schemas import UserCreate, UserProfileUpdate


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    admin = user_service.create_user(
        session,
        UserCreate(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            role="admin",
        ),
    )
    user_service.upsert_profile(
        session, admin.id, UserProfileUpdate(display_name="Admin", department="IT")
    )

    regular = user_service.create_user(
        session,
        UserCreate(
            username="alice",
            email="alice@example.com",
            password="alicepass123",
            role="user",
        ),
    )
    profile = UserProfile(user_id=regular.id, display_name="Alice", bio="Engineer")
    session.add(profile)
    session.commit()

    electronics = Category(name="Electronics", description="Gadgets")
    session.add(electronics)
    session.commit()

    products = [
        Product(sku="SKU-001", name="Cable", quantity=2, reorder_level=5, category_id=electronics.id),
        Product(sku="SKU-002", name="Mouse", quantity=50, reorder_level=10, category_id=electronics.id),
        Product(sku="SKU-003", name="Keyboard", quantity=3, reorder_level=5, category_id=electronics.id),
    ]
    session.add_all(products)
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def admin_token(client) -> str:
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "admin", "password": "adminpass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def user_token(client) -> str:
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "alice", "password": "alicepass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
