# app/services/user_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from app.models.user import User
from app.models.team import Team
from app.schemas.user import UserCreate, UserUpdate
from .base_service import BaseService

class UserService(BaseService[User, UserCreate, UserUpdate]):
    """
    Service class for User operations
    Handles user management and authentication logic
    """
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email address"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return (self.db.query(User)
                .filter(User.is_active == True)
                .offset(skip)
                .limit(limit)
                .all())
    
    def get_users_by_team(self, team_id: int) -> List[User]:
        """Get all users in a specific team"""
        return (self.db.query(User)
                .filter(and_(User.team_id == team_id, User.is_active == True))
                .all())
    
    def get_admin_users(self) -> List[User]:
        """Get all admin users"""
        return (self.db.query(User)
                .filter(and_(User.is_admin == True, User.is_active == True))
                .all())
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with validation"""
        # Check if email already exists
        existing_user = self.get_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Validate team exists if team_id provided
        if user_data.team_id:
            team = self.db.query(Team).filter(Team.id == user_data.team_id).first()
            if not team:
                raise ValueError(f"Team with id {user_data.team_id} does not exist")
        
        return self.create(user_data)
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user with validation"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Check email uniqueness if email is being changed
        if user_data.email and user_data.email != user.email:
            existing_user = self.get_by_email(user_data.email)
            if existing_user:
                raise ValueError(f"User with email {user_data.email} already exists")
        
        # Validate team exists if team_id is being changed
        if user_data.team_id:
            team = self.db.query(Team).filter(Team.id == user_data.team_id).first()
            if not team:
                raise ValueError(f"Team with id {user_data.team_id} does not exist")
        
        return self.update(user_id, user_data)
    
    def authenticate_user(self, email: str) -> Optional[User]:
        """Simple authentication by email (MVP - no passwords)"""
        user = self.get_by_email(email)
        if user and user.is_active:
            return user
        return None
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user instead of hard delete"""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            return True
        return False
    
    def get_users_count_by_team(self) -> dict:
        """Get count of users per team"""
        result = (self.db.query(Team.id, Team.name, User.id)
                 .outerjoin(User, Team.id == User.team_id)
                 .filter(User.is_active == True)
                 .all())
        
        team_counts = {}
        for team_id, team_name, user_id in result:
            if team_name not in team_counts:
                team_counts[team_name] = 0
            if user_id:
                team_counts[team_name] += 1
                
        return team_counts