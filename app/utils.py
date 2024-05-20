# app/utils.py

import re
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import Variable


def resolve_nested_variables(variable_value: str, db: Session) -> str:
    """
    Résout les variables imbriquées dans une chaîne de caractères.
    """
    pattern = r"\{\{(.*?)\}\}"
    matches = re.findall(pattern, variable_value)

    for match in matches:
        # Validation de la syntaxe
        if not re.match(r"^[a-zA-Z0-9_]+$", match):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid variable reference syntax: '{match}'")

        referenced_variable = db.query(Variable).filter(Variable.name == match).first()
        if referenced_variable:
            resolved_value = resolve_nested_variables(referenced_variable.value, db)
            variable_value = variable_value.replace(f"{{{{{match}}}}}", resolved_value)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Referenced variable '{match}' not found")

    return variable_value
