# app/initial_data.py
import logging
import os

from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserCreate
from app.auth import get_password_hash

# Configurer le logging
logger = logging.getLogger(__name__)

def init_db(engine):
    """
    Initialise la base de données en créant le superutilisateur.
    """
    logger.info("Début de l'initialisation de la base de données")
    try:
        from app.database import Base
    except ImportError as e:
        logger.error(f"Erreur lors de l'importation du module Base : {e}")
        raise

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables : {e}")
        raise

    logger.info("Tables créées avec succès")
    
    db = Session(engine)

    user = db.query(User).filter(User.is_superuser == True).first()
    if not user:
        try:
            user_in = UserCreate(
                email=os.getenv("FIRST_SUPERUSER_EMAIL"),
                password=os.getenv("FIRST_SUPERUSER_PASSWORD"),
                is_superuser=True,
            )
            user = User(
                **user_in.dict(exclude={"password"}),
                hashed_password=get_password_hash(user_in.password),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Superutilisateur créé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création du superutilisateur : {e}")
            raise
