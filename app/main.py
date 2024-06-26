import sys
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.config import settings
from app.routes import auth_routes, variable_routes, category_routes, admin_routes

# Charger les variables d'environnement
load_dotenv()

if not os.getenv("SECRET_KEY"):
    raise ValueError("SECRET_KEY environment variable not set")

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Ajout de CORS pour permettre les requêtes cross-origin
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la base de données (utiliser le dialecte MySQL)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=True)  # Activer les logs SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dépendance pour obtenir une session de base de données
def get_db():
    try:
        logger.info(f"Tentative de connexion à la base de données : {DATABASE_URL}")
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Erreur de connexion à la base de données : {e}")
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données")
    finally:
        db.close()


# Créer les tables de la base de données si elles n'existent pas
try:
    logger.info("Tentative de création des tables de la base de données")
    Base.metadata.create_all(bind=engine)
    logger.info("Création des tables réussie")
except Exception as e:
    logger.error(f"Erreur lors de la création des tables : {e}")
    raise  # Remonter l'erreur pour arrêter le démarrage

# Inclure les routeurs
app.include_router(auth_routes.router, prefix=settings.API_V1_STR + '/auth', tags=["auth"])
app.include_router(variable_routes.router, prefix=settings.API_V1_STR + '/variables', tags=["variables"])
app.include_router(category_routes.router, prefix=settings.API_V1_STR + '/categories', tags=["categories"])
app.include_router(admin_routes.router, prefix=settings.API_V1_STR + '/admin/categories', tags=["admin"])

# Initialisation de la base de données
logger.info("Tentative d'initialisation des données de la base de données")
try:
    from app.initial_data import init_db  # Importer votre script d'initialisation
    init_db(engine)
    logger.info("Initialisation des données réussie")
except Exception as e:
    logger.error(f"Erreur lors de l'initialisation de la base de données : {e}")
    raise

# Gestion des erreurs 404
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"message": "Not Found"},
    )


# Route racine
@app.get("/", response_model=dict)
async def root() -> dict:
    return {"message": "Welcome to the ShortPress API"}


@app.get("/test_db")
async def test_db(db: Session = Depends(get_db)):
    try:
        result = db.execute("SELECT 1")
        if result.fetchone()[0] == 1:
            return {"db_connection": "success"}
        else:
            return {"db_connection": "failed"}
    except Exception as e:
        logger.error(f"Erreur lors du test de la connexion à la base de données : {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")
