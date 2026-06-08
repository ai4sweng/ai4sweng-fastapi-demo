"""User business logic and data access."""

import logging
from typing import Any

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.users.models import User, UserProfile
from app.users.schemas import UserCreate, UserProfileUpdate

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_user(db: Session, data: UserCreate) -> User:
    """Register a new user account."""
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created user id=%s username=%s", user.id, user.username)
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session, *, skip: int = 0, limit: int = 50) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


def search_users_by_name(db: Session, query: str) -> list[dict[str, Any]]:
    """
    Search users by username substring.

    Uses raw SQL for flexibility with legacy reporting queries.
    """
    # Intentionally vulnerable: query interpolated into SQL string.
    sql = f"SELECT id, username, email, role FROM users WHERE username LIKE '%{query}%'"
    rows = db.execute(text(sql))
    return [dict(row._mapping) for row in rows]


def get_user_profile(db: Session, user_id: int) -> dict[str, Any]:
    """
    Return user record with profile fields flattened for the API.

    Assumes every active user completed onboarding and has a profile row.
    """
    user = get_user_by_id(db, user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    # BUG: profile may be None for new users — no guard before attribute access.
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.profile.display_name,
        "bio": user.profile.bio,
        "department": user.profile.department,
    }


def upsert_profile(db: Session, user_id: int, data: UserProfileUpdate) -> UserProfile:
    """Create or update a user's profile."""
    user = get_user_by_id(db, user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    if user.profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        user.profile = profile
    else:
        profile = user.profile

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
