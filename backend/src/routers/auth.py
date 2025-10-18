# Authentication router for ScanPro
from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from src.services.auth_service import AuthService
from src.models.schemas.auth import (
    UserCreate, UserResponse, UserUpdate, UserLogin, UserChangePassword,
    AdminPasswordReset, TokenResponse
)
from src.models.database import User, UserRole
from src.dependencies import get_auth_service, get_current_user, require_admin
from src.core.exceptions import InvalidCredentialsException

router = APIRouter()

# Public authentication endpoints
@router.post("/login", response_model=TokenResponse)
def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Login and get session token"""
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise InvalidCredentialsException("Incorrect username or password")
    
    return auth_service.create_login_session(user)

# Admin-only endpoints
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Create a new user (admin only)"""
    return auth_service.create_user(user_data)

# Protected endpoints (require authentication)
@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        user_role=current_user.user_role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.post("/change-password")
def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change current user's password"""
    return auth_service.change_password(current_user.id, password_data)

# Admin-only endpoints
@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
) -> List[UserResponse]:
    """Get all users (admin only)"""
    return auth_service.get_all_users(skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Get user by ID (admin only)"""
    return auth_service.get_user(user_id)

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Update user (admin only) - cannot change own role"""
    if user_id == current_user.id and update_data.user_role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    return auth_service.update_user(user_id, update_data)

@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Update user role (admin only) - cannot change own role"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    return auth_service.update_user_role(user_id, role, current_user)

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Delete user (admin only) - cannot delete self"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    return auth_service.delete_user(user_id)

@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    password_data: AdminPasswordReset,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset user password (admin only) - no current password required"""
    return auth_service.admin_reset_password(user_id, password_data)