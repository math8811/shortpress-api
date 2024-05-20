from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_admin
from app.database import get_db
from app.models import Category as CategoryModel, User as UserModel
from app.schemas import Category

admin_router = APIRouter()

@admin_router.get("/users/{user_id}/categories/", response_model=List[Category])
def read_user_categories(user_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_admin)):
    """
    Récupère toutes les catégories appartenant à un utilisateur spécifique.
    
    Uniquement accessible aux administrateurs.
    """

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    categories = db.query(CategoryModel).filter(CategoryModel.owner_id == user_id).all()
    return categories

@admin_router.delete("/users/{user_id}/categories/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_user_categories(user_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_admin)):
    """
    Supprime toutes les catégories appartenant à un utilisateur spécifique.

    Uniquement accessible aux administrateurs.
    """

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.query(CategoryModel).filter(CategoryModel.owner_id == user_id).delete()
    db.commit()
