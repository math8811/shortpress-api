import sys
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI

from app.database import Base, engine
from app.routes import auth_routes, variable_routes, category_routes, admin_routes

# Charger les variables d'environnement
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")

# Ajouter explicitement le répertoire parent au `PYTHONPATH`
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Début du chargement de la configuration")

app = FastAPI()

# Crée les tables si elles n'existent pas
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Création des tables réussie")
except Exception as e:
    logger.error(f"Erreur lors de la création des tables : {e}")

# Inclure les routeurs
for router_module, prefix, tag in [
    (auth_routes, "/auth", "auth"),
    (variable_routes, "/variables", "variables"),
    (category_routes, "/categories", "categories"),
    (admin_routes, "/admin/categories", "admin"),
]:
    try:
        app.include_router(router_module.router, prefix=prefix, tags=[tag])
        logger.info(f"Routeur {tag} chargé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du chargement du routeur {tag} : {e}")
        raise  # Lever une exception pour arrêter le démarrage

@app.get("/", response_model=dict)
async def root() -> dict:
    return {"message": "Welcome to the ShortPress API"}
