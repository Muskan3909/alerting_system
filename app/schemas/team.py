# app/schemas/team.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    
    class Config:
        from_attributes = True