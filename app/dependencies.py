from fastapi import Depends
from app.auth import get_current_user
from app.database import get_db
from app.models import User


def get_db_session():
    return Depends(get_db)


def get_current_user_dependency():
    return Depends(get_current_user)


def get_currentt_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_admin(current_user: User = Depends(get_currentt_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
