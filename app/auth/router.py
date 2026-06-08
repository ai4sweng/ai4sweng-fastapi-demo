"""Authentication HTTP routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.schemas import LoginRequest, PasswordResetRequest, TokenResponse
from app.database import get_db
from app.dependencies import require_admin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = service.authenticate_user(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = service.create_access_token(user.username)
    return TokenResponse(access_token=token)


@router.post("/login/json", response_model=TokenResponse)
def login_json(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = service.authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = service.create_access_token(user.username)
    return TokenResponse(access_token=token)


@router.post("/reset-password")
def reset_password(
    body: PasswordResetRequest,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not service.reset_password(db, body.username, body.new_password):
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "password_updated"}
