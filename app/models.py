# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    variables = relationship("Variable", back_populates="owner")
    is_admin = Column(Boolean, default=False) 

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")
    variables = relationship("Variable", back_populates="category", cascade="all, delete-orphan")

class Variable(Base):
    __tablename__ = "variables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    identifier = Column(String, unique=True, index=True)
    value = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="variables")
    parent_variable_id = Column(Integer, ForeignKey("variables.id"))  # Nouvelle relation
    parent_variable = relationship("Variable", remote_side=[id], backref="child_variables")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="variables")

    def resolve_value(self, db):
        resolved_value = self.value
        variables = db.query(Variable).filter(Variable.owner_id == self.owner_id).all()

        for variable in variables:
            resolved_value = resolved_value.replace(f"{variable.identifier}", variable.value)

        return resolved_value