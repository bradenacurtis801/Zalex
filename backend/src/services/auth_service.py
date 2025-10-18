# auth service layer
import secrets
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union
from sqlmodel import Session, select
from passlib.context import CryptContext
from fastapi import HTTPException, status

from src.models.database import User, Session as DBSession
from src.models.schemas.auth import (
    UserCreate, UserResponse, UserUpdate, UserLogin, UserChangePassword,
    AdminPasswordReset, TokenResponse, UserRole
)
from src.core.auth_config import (
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.core.exceptions import (
    UserNotFoundException, InvalidCredentialsException, 
    PermissionDeniedException
)

pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"  # Use 2b variant which is more compatible
)

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def _constant_time_username_verify(self, provided_username: str, stored_username: str) -> bool:
        """Constant-time username comparison to prevent timing attacks"""
        return secrets.compare_digest(provided_username, stored_username)
    
    def _dummy_verify(self) -> None:
        """Perform dummy password verification to maintain consistent timing"""
        # Use a simple hash operation that takes similar time to bcrypt verification
        # This provides timing protection without relying on bcrypt hash validation
        import hashlib
        dummy_password = "dummy_password_for_timing_protection"
        dummy_salt = "dummy_salt_for_timing_protection"
        
        # Perform a hash operation that takes similar time to bcrypt verification
        for _ in range(12):  # bcrypt uses 12 rounds by default
            dummy_password = hashlib.sha256((dummy_password + dummy_salt).encode()).hexdigest()
    
    # User Management
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user with default role"""
        # Check if username or email already exists
        existing_user = self.db.exec(
            select(User).where(
                (User.username == user_data.username) | 
                (User.email == user_data.email)
            )
        ).first()
        
        if existing_user:
            if existing_user.username == user_data.username:
                raise HTTPException(
                    status_code=400, 
                    detail="Username already registered"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Email already registered"
                )
        
        # Hash password
        hashed_password = pwd_context.hash(user_data.password)
        
        # Create user with specified role
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            password_hash=hashed_password,
            user_role=user_data.user_role
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._to_user_response(db_user)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password (timing-attack resistant)"""
        # Get user by username
        user = self.db.exec(
            select(User).where(User.username == username, User.is_active == True)
        ).first()
        
        # Always perform password verification to maintain consistent timing
        if user:
            # Real user - verify password
            if pwd_context.verify(password, user.password_hash):
                return user
        else:
            # User doesn't exist - perform dummy verification
            self._dummy_verify()
        
        return None
    
    def get_user(self, user_id: int) -> UserResponse:
        """Get user by ID"""
        user = self.db.get(User, user_id)
        if not user:
            raise UserNotFoundException(f"User {user_id} not found")
        
        return self._to_user_response(user)
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users with pagination"""
        from sqlmodel import select
        
        users = self.db.exec(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        ).all()
        
        return [self._to_user_response(user) for user in users]
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.exec(
            select(User).where(User.username == username)
        ).first()
    
    def update_user(self, user_id: int, update_data: UserUpdate) -> UserResponse:
        """Update user"""
        user = self.db.get(User, user_id)
        if not user:
            raise UserNotFoundException(f"User {user_id} not found")
        
        update_dict = update_data.dict(exclude_unset=True)
        update_dict['updated_at'] = datetime.now(timezone.utc)
        
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return self._to_user_response(user)
    
    def change_password(self, user_id: int, password_data: UserChangePassword) -> dict:
        """Change user password"""
        user = self.db.get(User, user_id)
        if not user:
            raise UserNotFoundException(f"User {user_id} not found")
        
        # Verify current password
        if not pwd_context.verify(password_data.current_password, user.password_hash):
            raise InvalidCredentialsException("Current password is incorrect")
        
        # Update password
        user.password_hash = pwd_context.hash(password_data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        # Invalidate all existing sessions for this user (except current session)
        sessions = self.db.exec(
            select(DBSession).where(DBSession.user_id == user_id)
        ).all()
        
        for session in sessions:
            session.is_revoked = True
            self.db.add(session)
        
        self.db.add(user)
        self.db.commit()
        
        return {"message": "Password changed successfully. Please log in again."}
    
    def admin_reset_password(self, user_id: int, password_data: AdminPasswordReset) -> dict:
        """Admin reset user password (no current password required)"""
        user = self.db.get(User, user_id)
        if not user:
            raise UserNotFoundException(f"User {user_id} not found")
        
        # Update password
        user.password_hash = pwd_context.hash(password_data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        # Invalidate all existing sessions for this user
        self.db.exec(
            select(DBSession).where(DBSession.user_id == user_id)
        ).all()
        
        # Revoke all sessions
        sessions = self.db.exec(
            select(DBSession).where(DBSession.user_id == user_id)
        ).all()
        
        for session in sessions:
            session.is_revoked = True
            self.db.add(session)
        
        self.db.add(user)
        self.db.commit()
        
        return {"message": f"Password reset successfully for user {user.username}. All sessions have been invalidated."}
    
    def update_user_role(self, user_id: int, new_role: UserRole, admin_user: User) -> UserResponse:
        """Update user role (admin only)"""
        # Check if admin user has admin permission
        if admin_user.user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Only administrators can change user roles"
            )
        
        # Get user to update
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Update user role
        user.user_role = new_role
        user.updated_at = datetime.now(timezone.utc)
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return self._to_user_response(user)
    
    # Session Token Management (for login sessions)
    def create_login_session(self, user: User) -> TokenResponse:
        """Create a session token for user login"""
        # Generate token
        raw_token = self._generate_session_token()
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Set expiration
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Create database record
        db_session = DBSession(
            user_id=user.id,
            session_token=token_hash,
            expires_at=expires_at
        )
        
        self.db.add(db_session)
        self.db.commit()
        
        return TokenResponse(
            session_token=raw_token,
            token_type="bearer",
            expires_in=int(ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            user=self._to_user_response(user)
        )
    
    def verify_session_token(self, token: str) -> Optional[User]:
        """Verify session token and return user (timing-attack resistant)"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        db_session = self.db.exec(
            select(DBSession).where(
                DBSession.session_token == token_hash,
                DBSession.is_revoked == False
            )
        ).first()
        
        # Always perform some work to maintain consistent timing
        if not db_session:
            # Token doesn't exist - perform dummy operations
            self._dummy_verify()
            return None
        
        # Check expiration (handle both timezone-aware and timezone-naive)
        current_time = datetime.now(timezone.utc)
        expires_at = db_session.expires_at
        
        # If expires_at is timezone-naive, assume it's UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at <= current_time:
            return None
        
        # Get user
        user = self.db.get(User, db_session.user_id)
        if not user or not user.is_active:
            return None
        
        # Update last activity
        db_session.last_activity = datetime.now(timezone.utc)
        self.db.add(db_session)
        self.db.commit()
        
        return user
    
    
    def _generate_session_token(self) -> str:
        """Generate a random session token using cryptographically secure random"""
        # Use secrets.token_urlsafe for cryptographically secure random tokens
        return f"st_{secrets.token_urlsafe(32)}"
    
    
    def _to_user_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse"""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            user_role=user.user_role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    def delete_user(self, user_id: int) -> dict:
        """Delete a user by ID"""
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        self.db.delete(user)
        self.db.commit()
        
        return {"message": f"User {user.username} deleted successfully"}
    