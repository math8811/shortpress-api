#dependencies.py
from fastapi import Depends
from app.auth import get_current_user
from app.database import get_db
from app.models import User


def get_db_session():
    return Depends(get_db)


def get_current_user_dependency():
    return Depends(get_current_user)


def get_current_active_user(current_user: User = Depends(get_current_user)):
    logger.info("Entering get_current_active_user")
    logger.debug(f"Current user: {current_user}")  # Log l'objet User pour inspection
    if not current_user.is_active:
        logger.warning("Inactive user detected")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_admin(current_user: User = Depends(get_current_active_user)):
    logger.info("Entering get_current_active_admin")
    if not current_user.is_admin:
        logger.warning("Non-admin user trying to access admin route")
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user