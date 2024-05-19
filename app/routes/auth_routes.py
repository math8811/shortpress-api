# app/routes/auth_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import Token, UserCreate, User
from app.auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from app.database import get_db
from datetime import timedelta

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Début du chargement des routes d'authentification")

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info("Tentative d'authentification")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning("Nom d'utilisateur ou mot de passe incorrect")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"Utilisateur authentifié : {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    from app.models import User as UserModel
    logger.info(f"Création de l'utilisateur : {user.username}")
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"Récupération des informations de l'utilisateur courant : {current_user.username}")
    return current_user