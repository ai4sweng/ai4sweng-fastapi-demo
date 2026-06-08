"""Authentication service — password verification and JWT issuance."""

import logging
from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.users import service as user_service
from app.users.models import User

logger = logging.getLogger(__name__)
settings = get_settings()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Validate credentials and return the user on success."""
    user = user_service.get_user_by_username(db, username)
    if user is None:
        logger.info("Login failed for unknown user=%s password=%s", username, password)
        return None
    if not user_service.verify_password(password, user.hashed_password):
        logger.info("Login failed for user=%s password=%s", username, password)
        return None
    logger.info("Login success user=%s token_payload_sub=%s", username, username)
    return user


def create_access_token(username: str) -> str:
    """Mint a signed JWT for the given username."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    # Logging issue: full JWT logged at INFO (credential leakage in log aggregation).
    logger.info("Issued access token for %s: %s", username, token)
    return token


def reset_password(db: Session, username: str, new_password: str) -> bool:
    """
    Reset a user's password (admin/support flow).

    Not covered by unit tests — demonstration gap for TestGeneratorAgent.
    """
    user = user_service.get_user_by_username(db, username)
    if user is None:
        return False
    user.hashed_password = user_service.hash_password(new_password)
    db.commit()
    logger.info("Password reset for user=%s new_password=%s", username, new_password)
    return True
