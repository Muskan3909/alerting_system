# app/routers/teams.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.services.team_service import TeamService
from app.models.user import User
from .dependencies import get_current_user, get_current_admin_user, get_team_service

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new team (Admin only)"""
    try:
        team = team_service.create_team(team_data)
        # Add member_count for response
        team_dict = team.__dict__.copy()
        team_dict['member_count'] = 0
        return team_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_member_count: bool = Query(True),
    search: Optional[str] = Query(None),
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_user)
):
    """List all teams"""
    if search:
        teams_data = team_service.search_teams(search, limit)
        # Convert to dict format with member counts
        teams = []
        for team in teams_data:
            team_dict = team.__dict__.copy()
            if include_member_count:
                team_dict['member_count'] = team_service.get_team_member_count(team.id)
            else:
                team_dict['member_count'] = 0
            teams.append(team_dict)
        return teams
    
    if include_member_count:
        teams = team_service.get_teams_with_member_count(skip=skip, limit=limit)
        return teams
    else:
        teams = team_service.get_active_teams(skip=skip, limit=limit)
        return [dict(team.__dict__, member_count=0) for team in teams]

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_user)
):
    """Get team by ID"""
    team = team_service.get_by_id(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Add member count
    member_count = team_service.get_team_member_count(team_id)
    team_dict = team.__dict__.copy()
    team_dict['member_count'] = member_count
    
    return team_dict

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Update team (Admin only)"""
    try:
        updated_team = team_service.update_team(team_id, team_data)
        if not updated_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Add member count
        member_count = team_service.get_team_member_count(team_id)
        team_dict = updated_team.__dict__.copy()
        team_dict['member_count'] = member_count
        
        return team_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{team_id}")
async def deactivate_team(
    team_id: int,
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Deactivate team and remove all members (Admin only)"""
    success = team_service.deactivate_team(team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return {"message": "Team deactivated successfully"}

@router.post("/{team_id}/members/{user_id}")
async def add_member_to_team(
    team_id: int,
    user_id: int,
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Add a user to a team (Admin only)"""
    success = team_service.add_member_to_team(user_id, team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add member to team. User or team may not exist."
        )
    return {"message": "Member added to team successfully"}

@router.delete("/members/{user_id}")
async def remove_member_from_team(
    user_id: int,
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Remove a user from their current team (Admin only)"""
    success = team_service.remove_member_from_team(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "Member removed from team successfully"}

@router.get("/{team_id}/members")
async def get_team_members_list(
    team_id: int,
    team_service: TeamService = Depends(get_team_service),
    current_user: User = Depends(get_current_user)
):
    """Get all members of a specific team"""
    # Users can view their own team or admins can view any team
    if not current_user.is_admin and current_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own team members"
        )
    
    members = team_service.get_team_members(team_id)
    return members