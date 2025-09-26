# app/services/base_service.py
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import Generic, TypeVar, Type, List, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')  # Database model type
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)

class BaseService(ABC, Generic[T, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class implementing common CRUD operations
    Following the Repository pattern for database operations
    """
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get a single record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def get_count(self) -> int:
        """Get total count of records"""
        return self.db.query(self.model).count()
    
    def create(self, obj_data: CreateSchemaType) -> T:
        """Create a new record"""
        db_obj = self.model(**obj_data.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: int, obj_data: UpdateSchemaType) -> Optional[T]:
        """Update an existing record"""
        db_obj = self.get_by_id(id)
        if db_obj:
            update_data = obj_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
    
    def exists(self, id: int) -> bool:
        """Check if record exists"""
        return self.db.query(self.model).filter(self.model.id == id).first() is not None