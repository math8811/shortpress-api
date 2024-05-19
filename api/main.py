import sys
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.core.config import settings # Ajout d'un fichier de configuration pour le titre du projet et les préfixes d'API
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
# (Ajustez les origines autorisées en fonction de vos besoins)
origins = ["*"]  # Autoriser toutes les origines (à remplacer en production)

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
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dépendance pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Créer les tables de la base de données si elles n'existent pas
Base.metadata.create_all(bind=engine)

# Inclure les routeurs
app.include_router(auth_routes.router, prefix=settings.API_V1_STR + '/auth', tags=["auth"])
app.include_router(variable_routes.router, prefix=settings.API_V1_STR + '/variables', tags=["variables"])
app.include_router(category_routes.router, prefix=settings.API_V1_STR + '/categories', tags=["categories"])
app.include_router(admin_routes.router, prefix=settings.API_V1_STR + '/admin/categories', tags=["admin"])

# Initialisation de la base de données
from app.initial_data import init_db  # Importer votre script d'initialisation
init_db(engine)


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
