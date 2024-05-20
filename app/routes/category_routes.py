#category_routes.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_current_active_admin
from app.database import get_db
from app.models import Category as CategoryModel, User as UserModel
from app.schemas import Category, CategoryCreate, CategoryUpdate, Variable

router = APIRouter()

# Créer une catégorie (POST)
@router.post("/", response_model=Category)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    db_category = CategoryModel(**category.dict(), owner_id=current_user.id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Obtenir toutes les catégories (GET)
@router.get("/", response_model=List[Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    if current_user.is_admin:
        categories = db.query(CategoryModel).offset(skip).limit(limit).all()
    else:
        categories = db.query(CategoryModel).filter(CategoryModel.owner_id == current_user.id).offset(skip).limit(limit).all()
    return categories

# Obtenir une catégorie par ID (GET)
@router.get("/{category_id}", response_model=Category)
def read_category(category_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if not current_user.is_admin and category.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this category")
    return category

# Mettre à jour une catégorie (PUT)
@router.put("/{category_id}", response_model=Category)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    db_category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if not current_user.is_admin and db_category.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this category")
    for attr, value in category.dict(exclude_unset=True).items():
        setattr(db_category, attr, value)
    db.commit()
    db.refresh(db_category)
    return db_category

# Supprimer une catégorie (DELETE)
@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int, 
    action: str = Query(..., description="Action to take: 'delete' or 'reassign'"),
    new_category_id: int = Query(None, description="New category ID for reassignment (required if action is 'reassign')"),
    db: Session = Depends(get_db)  # Changement ici
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if action == "delete":
        # Suppression en cascade (gérée automatiquement par SQLAlchemy grâce à la relation définie)
        db.delete(category)
        db.commit()
        return {"message": "Category and associated variables deleted"}
    elif action == "reassign":
        if new_category_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New category ID is required for reassignment")
        new_category = db.query(Category).filter(Category.id == new_category_id).first()
        if not new_category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New category not found")

        variables = db.query(Variable).filter(Variable.category_id == category_id).all()
        for variable in variables:
            variable.category_id = new_category_id
        db.delete(category)  # Supprimer l'ancienne catégorie
        db.commit()
        return {"message": "Category deleted and variables reassigned to new category"}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action. Choose 'delete' or 'reassign'")

# Routes supplémentaires pour l'administrateur

# Obtenir toutes les catégories d'un utilisateur (GET)
@router.get("/users/{user_id}/categories/", response_model=List[Category])
def read_user_categories(user_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_admin)):
    categories = db.query(CategoryModel).filter(CategoryModel.owner_id == user_id).all()
    return categories

# Supprimer toutes les catégories d'un utilisateur (DELETE)
@router.delete("/users/{user_id}/categories/", status_code=204)
def delete_all_user_categories(user_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_admin)):
    db.query(CategoryModel).filter(CategoryModel.owner_id == user_id).delete()
    db.commit()
