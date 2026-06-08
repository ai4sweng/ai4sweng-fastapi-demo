"""User management HTTP routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.users import service
from app.users.models import User
from app.users.schemas import (
    UserCreate,
    UserProfileRead,
    UserProfileUpdate,
    UserRead,
    UserWithProfile,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(data: UserCreate, db: Session = Depends(get_db)) -> User:
    if service.get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return service.create_user(db, data)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("", response_model=list[UserRead])
def list_all_users(
    skip: int = 0,
    limit: int = 50,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    return service.list_users(db, skip=skip, limit=limit)


@router.get("/search")
def search_users(
    q: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    return service.search_users_by_name(db, q)


@router.get("/{user_id}/profile")
def read_user_profile(user_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return service.get_user_profile(db, user_id)
    except AttributeError:
        raise HTTPException(status_code=404, detail="Profile not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{user_id}/profile", response_model=UserProfileRead)
def update_user_profile(
    user_id: int,
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileRead:
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    profile = service.upsert_profile(db, user_id, data)
    return UserProfileRead.model_validate(profile, from_attributes=True)


@router.get("/{user_id}", response_model=UserWithProfile)
def read_user(user_id: int, db: Session = Depends(get_db)) -> UserWithProfile:
    user = service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    profile = None
    if user.profile:
        profile = UserProfileRead.model_validate(user.profile)
    return UserWithProfile(user=UserRead.model_validate(user), profile=profile)
