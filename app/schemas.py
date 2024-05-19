# schemas.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

print("Chargement du fichier schemas.py")

class Token(BaseModel):
    access_token: str = Field(..., description="Jeton d'accès pour l'authentification")
    token_type: str = Field(..., description="Type de jeton, généralement 'bearer'")

class TokenData(BaseModel):
    username: Optional[str] = Field(None, description="Nom d'utilisateur associé au jeton")

class UserCreate(BaseModel):
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")

class User(BaseModel):
    id: int = Field(..., description="Identifiant unique de l'utilisateur")
    username: str = Field(..., description="Nom d'utilisateur")
    is_admin: bool = Field(..., description="Indique si l'utilisateur est administrateur")

    class Config:
        orm_mode = True

class CategoryBase(BaseModel):
    name: str = Field(..., description="Nom de la catégorie")

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int = Field(..., description="Identifiant unique de la catégorie")
    owner_id: int = Field(..., description="Identifiant de l'utilisateur propriétaire")

    class Config:
        orm_mode = True

class VariableBase(BaseModel):
    name: str = Field(..., description="Nom de la variable")
    identifier: str = Field(..., description="Identifiant unique de la variable")
    value: str = Field(..., description="Valeur brute de la variable")  # Champ pour la valeur brute
    category_id: Optional[int] = Field(None, description="Identifiant de la catégorie associée")
    parent_variable_id: Optional[int] = None  # Optionnel car une variable peut ne pas avoir de parent

class VariableCreate(VariableBase):
    pass

class VariableUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Nom de la variable")
    value: Optional[str] = Field(None, description="Valeur brute de la variable")  # Champ pour la valeur brute
    category_id: Optional[int] = Field(None, description="Identifiant de la catégorie associée")

class Variable(VariableBase):
    id: int = Field(..., description="Identifiant unique de la variable")
    display_value: str = Field(..., alias="value", description="Valeur de la variable avec les variables imbriquées résolues")
    parent_variable: Optional["Variable"] = None
    created_at: datetime = Field(..., description="Date et heure de création")
    updated_at: datetime = Field(..., description="Date et heure de la dernière modification")
    owner_id: int = Field(..., description="Identifiant de l'utilisateur propriétaire")

    class Config:
        orm_mode = True

        @staticmethod
        def schema_extra(schema, model):
            # Supprimer le champ "value" du schéma, car il est maintenant redondant avec "display_value"
            del schema["properties"]["value"]