from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.schemas import Variable, VariableCreate, VariableUpdate
from app.models import Variable as VariableModel, User
from app.auth import get_current_active_user, get_current_active_admin
from app.database import get_db
from app.utils import resolve_nested_variables

router = APIRouter()

# GET /variables/
@router.get("/variables/", response_model=List[Variable])
async def read_variables(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  
):
    if current_user.is_admin:
        variables = db.query(VariableModel).offset(skip).limit(limit).all()
    else:
        variables = db.query(VariableModel).filter(VariableModel.owner_id == current_user.id).offset(skip).limit(limit).all()

    # Résolution des variables imbriquées pour chaque variable
    for variable in variables:
        variable.display_value = resolve_nested_variables(variable.value, db)

    return variables

# GET /variables/{variable_id}
@router.get("/variables/{variable_id}", response_model=Variable)
async def read_variable(
    variable_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    variable = db.query(VariableModel).filter(VariableModel.id == variable_id).first()
    if variable is None:
        raise HTTPException(status_code=404, detail="Variable not found")
    if not current_user.is_admin and variable.owner_id != current_user.id: 
        raise HTTPException(status_code=403, detail="Not authorized to access this variable")

    # Résolution de la variable imbriquée (si nécessaire)
    variable.display_value = resolve_nested_variables(variable.value, db)

    return variable


# GET /variables/{variable_id}/resolved
@router.get("/variables/{variable_id}/resolved", response_model=Variable)
async def read_resolved_variable(
    variable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    variable = db.query(VariableModel).filter(VariableModel.id == variable_id).first()
    if variable is None:
        raise HTTPException(status_code=404, detail="Variable not found")
    if not current_user.is_admin and variable.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this variable")

    try:
        resolved_value = resolve_nested_variables(variable.value, db)
    except HTTPException as e:
        raise e  # Relève l'exception de la fonction resolve_nested_variables
    except Exception as e:  # Attraper d'autres erreurs potentielles
        raise HTTPException(status_code=500, detail=f"Error resolving variable: {str(e)}") 

    return Variable(id=variable.id, name=variable.name, value=variable.value, display_value=resolved_value, category_id=variable.category_id, created_at=variable.created_at, updated_at=variable.updated_at, owner_id=variable.owner_id)


# GET /variables/by-identifier/{identifier}/resolved
@router.get("/variables/by-identifier/{identifier}/resolved", response_model=Variable)
async def read_resolved_variable_by_identifier(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    variable = db.query(VariableModel).filter(VariableModel.identifier == identifier).first()
    if variable is None:
        raise HTTPException(status_code=404, detail="Variable not found")
    if not current_user.is_admin and variable.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this variable")
    
    try:
        resolved_value = resolve_nested_variables(variable.value, db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving variable: {str(e)}")

    return Variable(id=variable.id, name=variable.name, identifier=variable.identifier, value=variable.value, display_value=resolved_value, category_id=variable.category_id, created_at=variable.created_at, updated_at=variable.updated_at, owner_id=variable.owner_id)

# POST /variables/
@router.post("/variables/", response_model=Variable)
async def create_variable(
    variable: VariableCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    if db.query(VariableModel).filter(VariableModel.identifier == variable.identifier, VariableModel.owner_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Variable identifier already exists")
    db_variable = VariableModel(
        **variable.dict(),
        owner_id=current_user.id,
    )
    db.add(db_variable)
    db.commit()
    db.refresh(db_variable)
    return db_variable

# PUT /variables/{variable_id}
@router.put("/variables/{variable_id}", response_model=Variable)
async def update_variable(
    variable_id: int,
    variable: VariableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  
):
    db_variable = db.query(VariableModel).filter(VariableModel.id == variable_id).first()
    if db_variable is None:
        raise HTTPException(status_code=404, detail="Variable not found")
    if not current_user.is_admin and db_variable.owner_id != current_user.id:  
        raise HTTPException(status_code=403, detail="Not authorized to update this variable")

    for attr, value in variable.dict(exclude_unset=True).items():
        setattr(db_variable, attr, value)
    db_variable.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_variable)
    return db_variable

# DELETE /variables/{variable_id}
@router.delete("/variables/{variable_id}", status_code=204)
async def delete_variable(
    variable_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)  
):
    db_variable = db.query(VariableModel).filter(VariableModel.id == variable_id).first()
    if db_variable is None:
        raise HTTPException(status_code=404, detail="Variable not found")
    if not current_user.is_admin and db_variable.owner_id != current_user.id: 
        raise HTTPException(status_code=403, detail="Not authorized to delete this variable")
    
    db.delete(db_variable)
    db.commit()

# Routes supplémentaires pour l'administrateur

# GET /users/{user_id}/variables/
@router.get("/users/{user_id}/variables/", response_model=List[Variable])
async def read_user_variables(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),  # Uniquement pour les admins
):
    variables = db.query(VariableModel).filter(VariableModel.owner_id == user_id).all()
    return variables

# DELETE /users/{user_id}/variables/
@router.delete("/users/{user_id}/variables/", status_code=204)
async def delete_all_user_variables(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_admin)  # Uniquement pour les admins
):
    db.query(VariableModel).filter(VariableModel.owner_id == user_id).delete()
    db.commit()
