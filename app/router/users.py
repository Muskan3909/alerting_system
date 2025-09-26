# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.services.user_service import UserService
from app.models.user import User
from .dependencies import get_current_user, get_current_admin_user, get_user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new user (Admin only)"""
    try:
        user = user_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user information"""
    try:
        # Users can only update their own non-admin fields
        restricted_data = user_data.model_copy()
        if not current_user.is_admin:
            restricted_data.is_admin = None
        
        updated_user = user_service.update_user(current_user.id, restricted_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    team_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    """List users (Admin only)"""
    if team_id:
        users = user_service.get_users_by_team(team_id)
    elif active_only:
        users = user_service.get_active_users(skip=skip, limit=limit)
    else:
        users = user_service.get_all(skip=skip, limit=limit)
    
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Get user by ID (Admin only)"""
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Update user by ID (Admin only)"""
    try:
        updated_user = user_service.update_user(user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Deactivate user (Admin only)"""
    success = user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deactivated successfully"}

@router.post("/login", response_model=UserResponse)
async def login(
    login_data: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """Simple login by email (MVP - no password required)"""
    user = user_service.authenticate_user(login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or inactive user"
        )
    return user

@router.get("/team/{team_id}/members", response_model=List[UserResponse])
async def get_team_members(
    team_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """Get all members of a team"""
    # Users can view their own team or admins can view any team
    if not current_user.is_admin and current_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own team members"
        )
    
    members = user_service.get_users_by_team(team_id)
    return members