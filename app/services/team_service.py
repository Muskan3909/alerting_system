# app/services/team_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate
from .base_service import BaseService

class TeamService(BaseService[Team, TeamCreate, TeamUpdate]):
    """
    Service class for Team operations
    Handles team management and member relationships
    """
    
    def __init__(self, db: Session):
        super().__init__(db, Team)
    
    def get_by_name(self, name: str) -> Optional[Team]:
        """Find team by name"""
        return self.db.query(Team).filter(Team.name == name).first()
    
    def get_active_teams(self, skip: int = 0, limit: int = 100) -> List[Team]:
        """Get all active teams"""
        return (self.db.query(Team)
                .filter(Team.is_active == True)
                .offset(skip)
                .limit(limit)
                .all())
    
    def get_teams_with_member_count(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get teams with their member counts"""
        result = (self.db.query(
                    Team.id,
                    Team.name,
                    Team.description,
                    Team.is_active,
                    Team.created_at,
                    Team.updated_at,
                    func.count(User.id).label('member_count')
                )
                .outerjoin(User, and_(Team.id == User.team_id, User.is_active == True))
                .filter(Team.is_active == True)
                .group_by(Team.id)
                .offset(skip)
                .limit(limit)
                .all())
        
        teams = []
        for row in result:
            teams.append({
                'id': row.id,
                'name': row.name,
                'description': row.description,
                'is_active': row.is_active,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'member_count': row.member_count
            })
        
        return teams
    
    def create_team(self, team_data: TeamCreate) -> Team:
        """Create a new team with validation"""
        # Check if team name already exists
        existing_team = self.get_by_name(team_data.name)
        if existing_team:
            raise ValueError(f"Team with name '{team_data.name}' already exists")
        
        return self.create(team_data)
    
    def update_team(self, team_id: int, team_data: TeamUpdate) -> Optional[Team]:
        """Update team with validation"""
        team = self.get_by_id(team_id)
        if not team:
            return None
        
        # Check name uniqueness if name is being changed
        if team_data.name and team_data.name != team.name:
            existing_team = self.get_by_name(team_data.name)
            if existing_team:
                raise ValueError(f"Team with name '{team_data.name}' already exists")
        
        return self.update(team_id, team_data)
    
    def get_team_members(self, team_id: int) -> List[User]:
        """Get all members of a specific team"""
        return (self.db.query(User)
                .filter(and_(User.team_id == team_id, User.is_active == True))
                .all())
    
    def add_member_to_team(self, user_id: int, team_id: int) -> bool:
        """Add a user to a team"""
        user = self.db.query(User).filter(User.id == user_id).first()
        team = self.get_by_id(team_id)
        
        if not user or not team:
            return False
        
        user.team_id = team_id
        self.db.commit()
        return True
    
    def remove_member_from_team(self, user_id: int) -> bool:
        """Remove a user from their current team"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.team_id = None
        self.db.commit()
        return True
    
    def deactivate_team(self, team_id: int) -> bool:
        """Deactivate team and remove all members from it"""
        team = self.get_by_id(team_id)
        if not team:
            return False
        
        # Remove all members from the team
        self.db.query(User).filter(User.team_id == team_id).update({User.team_id: None})
        
        # Deactivate the team
        team.is_active = False
        self.db.commit()
        return True
    
    def get_team_member_count(self, team_id: int) -> int:
        """Get the number of active members in a team"""
        return (self.db.query(User)
                .filter(and_(User.team_id == team_id, User.is_active == True))
                .count())
    
    def search_teams(self, search_term: str, limit: int = 10) -> List[Team]:
        """Search teams by name or description"""
        return (self.db.query(Team)
                .filter(and_(
                    Team.is_active == True,
                    Team.name.ilike(f"%{search_term}%") | 
                    Team.description.ilike(f"%{search_term}%")
                ))
                .limit(limit)
                .all())