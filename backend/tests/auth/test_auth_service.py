import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.services.auth_service import AuthService, token_encryption
from backend.app.models.user import User
from backend.app.models.github_token import GitHubToken
from datetime import datetime, timezone, timedelta

# Setup in-memory DB for testing
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    Base.metadata.drop_all(bind=engine)
    session.close()

@pytest.fixture
def auth_service(db):
    return AuthService(db)

@pytest.fixture
def mock_user(db):
    user = User(
        github_id="12345",
        username="testuser",
        email="test@example.com",
        avatar_url="http://example.com/avatar.png"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.mark.asyncio
async def test_find_or_create_user(auth_service, db):
    github_user = {"id": 12345, "login": "testuser", "avatar_url": "http://example.com/avatar.png"}
    emails = [{"email": "test@example.com", "primary": True, "verified": True}]

    # First call should create user
    user = auth_service.find_or_create_user(github_user, emails)
    assert user.username == "testuser"
    assert user.github_id == "12345"

    # Second call should find existing user
    user2 = auth_service.find_or_create_user(github_user, emails)
    assert user.id == user2.id

@pytest.mark.asyncio
async def test_store_and_get_token(auth_service, mock_user, db):
    token_data = {
        "access_token": "gho_test_access_token",
        "refresh_token": "ghr_test_refresh_token",
        "token_type": "bearer",
        "scope": "repo",
        "expires_in": 3600
    }

    # Store token
    stored_token = auth_service.store_tokens(mock_user, token_data)
    assert stored_token is not None

    # Retrieve token
    retrieved_token = auth_service.get_valid_access_token(mock_user.id)
    assert retrieved_token == "gho_test_access_token"

@pytest.mark.asyncio
async def test_token_encryption(mock_user):
    # Verify encryption actually happens in DB
    from sqlalchemy.orm import Session
    # Note: we need a real session here or just test token_encryption class
    raw_text = "secret_token_123"
    encrypted = token_encryption.encrypt(raw_text)
    assert encrypted != raw_text
    assert token_encryption.decrypt(encrypted) == raw_text

@pytest.mark.asyncio
async def test_revoke_tokens(auth_service, mock_user, db):
    token_data = {
        "access_token": "gho_test_access_token",
        "refresh_token": "ghr_test_refresh_token",
        "token_type": "bearer",
        "scope": "repo",
    }
    auth_service.store_tokens(mock_user, token_data)

    # Revoke
    success = auth_service.revoke_tokens(mock_user.id)
    assert success is True

    # Verify token is gone
    token = auth_service.get_valid_access_token(mock_user.id)
    assert token is None
