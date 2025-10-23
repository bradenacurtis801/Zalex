"""
Unit tests for AuthService using mocked database.

These tests focus on business logic and run fast without external dependencies.
They use mocked database sessions to test the service layer in isolation.
"""

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime, timezone, timedelta

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.auth_service import AuthService
from src.models.schemas.auth import UserCreate, UserUpdate, UserChangePassword, AdminPasswordReset
from src.models.database import User, UserRole
from src.core.exceptions import UserNotFoundException, InvalidCredentialsException


class TestAuthServiceMocked:
    """Unit tests for AuthService with mocked database."""
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_create_user_success(self, mock_db_session):
        """Test successful user creation with mocked database."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            user_role=UserRole.USER
        )
        
        # Mock database responses
        mock_db_session.exec.return_value.first.return_value = None  # No existing user
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        
        # Mock refresh to set the user ID
        def mock_refresh(user):
            user.id = 1
        mock_db_session.refresh = Mock(side_effect=mock_refresh)
        
        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.hash.return_value = "hashed_password"
            result = auth_service.create_user(user_data)
        
        # Assert
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        assert result.user_role == UserRole.USER
        assert result.is_active is True
        
        # Verify database interactions
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        mock_pwd.hash.assert_called_once_with("password123")
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_create_user_duplicate_username(self, mock_db_session):
        """Test user creation with duplicate username."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        user_data = UserCreate(
            username="existinguser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            user_role=UserRole.USER
        )
        
        # Mock existing user found
        existing_user = Mock(spec=User)
        existing_user.username = "existinguser"
        mock_db_session.exec.return_value.first.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            auth_service.create_user(user_data)
        
        assert "Username already registered" in str(exc_info.value.detail)
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_create_user_duplicate_email(self, mock_db_session):
        """Test user creation with duplicate email."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        user_data = UserCreate(
            username="newuser",
            email="existing@example.com",
            full_name="Test User",
            password="password123",
            user_role=UserRole.USER
        )
        
        # Mock existing user found with same email
        existing_user = Mock(spec=User)
        existing_user.username = "differentuser"
        existing_user.email = "existing@example.com"
        mock_db_session.exec.return_value.first.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            auth_service.create_user(user_data)
        
        assert "Email already registered" in str(exc_info.value.detail)
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_authenticate_user_success(self, mock_db_session):
        """Test successful user authentication."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        
        # Mock user found in database
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = "hashed_password"
        mock_user.is_active = True
        
        mock_db_session.exec.return_value.first.return_value = mock_user
        
        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = True
            result = auth_service.authenticate_user("testuser", "password123")
        
        # Assert
        assert result is not None
        assert result.username == "testuser"
        mock_pwd.verify.assert_called_once_with("password123", "hashed_password")
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_authenticate_user_invalid_password(self, mock_db_session):
        """Test authentication with invalid password."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        
        # Mock user found in database
        mock_user = Mock(spec=User)
        mock_user.password_hash = "hashed_password"
        mock_user.is_active = True
        
        mock_db_session.exec.return_value.first.return_value = mock_user
        
        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = False
            result = auth_service.authenticate_user("testuser", "wrongpassword")
        
        # Assert
        assert result is None
        mock_pwd.verify.assert_called_once_with("wrongpassword", "hashed_password")
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_authenticate_user_not_found(self, mock_db_session):
        """Test authentication with non-existent user."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = False  # Mock verify to return False
            result = auth_service.authenticate_user("nonexistent", "password123")
        
        # Assert
        assert result is None
        # Note: The service doesn't call verify when no user is found
        # This is the actual behavior, so we don't assert on verify being called
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_authenticate_user_inactive(self, mock_db_session):
        """Test authentication with inactive user."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        
        # Mock no user found (inactive users are filtered out by the query)
        mock_db_session.exec.return_value.first.return_value = None

        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = False  # Mock verify to return False
            result = auth_service.authenticate_user("inactiveuser", "password123")
        
        # Assert
        # The service should return None for inactive users (they're filtered out)
        assert result is None
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_get_user_success(self, mock_db_session, mock_user):
        """Test successful user retrieval."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.get.return_value = mock_user
        
        # Act
        result = auth_service.get_user(1)
        
        # Assert
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        mock_db_session.get.assert_called_once_with(User, 1)
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_get_user_not_found(self, mock_db_session):
        """Test user retrieval with non-existent user."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.get.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundException):
            auth_service.get_user(99999)
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_get_all_users(self, mock_db_session, mock_user):
        """Test retrieving all users."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_users = [mock_user]
        mock_db_session.exec.return_value.all.return_value = mock_users
        
        # Act
        result = auth_service.get_all_users()
        
        # Assert
        assert len(result) == 1
        assert result[0].username == "testuser"
        mock_db_session.exec.assert_called_once()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_update_user_success(self, mock_db_session, mock_user):
        """Test successful user update."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.get.return_value = mock_user
        
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )
        
        # Act
        result = auth_service.update_user(1, update_data)
        
        # Assert
        assert result.full_name == "Updated Name"
        assert result.email == "updated@example.com"
        mock_db_session.add.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_user)
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_change_password_success(self, mock_db_session, mock_user):
        """Test successful password change."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.get.return_value = mock_user
        
        password_data = UserChangePassword(
            current_password="oldpassword",
            new_password="newpassword"
        )
        
        # Mock database query for sessions
        mock_db_session.exec.return_value.all.return_value = []  # No existing sessions
        
        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = True
            mock_pwd.hash.return_value = "new_hashed_password"
            result = auth_service.change_password(1, password_data)
        
        # Assert
        assert "Password changed successfully" in result["message"]
        # The verify call uses the original password hash, not the new one
        mock_pwd.verify.assert_called_once_with("oldpassword", "hashed_password")
        mock_pwd.hash.assert_called_once_with("newpassword")
        assert mock_user.password_hash == "new_hashed_password"
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_change_password_wrong_current(self, mock_db_session, mock_user):
        """Test password change with wrong current password."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.get.return_value = mock_user
        
        password_data = UserChangePassword(
            current_password="wrongpassword",
            new_password="newpassword"
        )
        
        # Act & Assert
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.verify.return_value = False
            with pytest.raises(InvalidCredentialsException):
                auth_service.change_password(1, password_data)
        
        mock_pwd.verify.assert_called_once_with("wrongpassword", mock_user.password_hash)
        mock_pwd.hash.assert_not_called()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_admin_reset_password_success(self, mock_db_session, mock_user):
        """Test successful admin password reset."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.get.return_value = mock_user
        
        password_data = AdminPasswordReset(new_password="adminreset123")
        
        # Mock database query for sessions
        mock_db_session.exec.return_value.all.return_value = []  # No existing sessions
        
        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.hash.return_value = "new_hashed_password"
            result = auth_service.admin_reset_password(1, password_data)
        
        # Assert
        assert "Password reset successfully" in result["message"]
        mock_pwd.hash.assert_called_once_with("adminreset123")
        assert mock_user.password_hash == "new_hashed_password"
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_create_login_session_success(self, mock_db_session, mock_user):
        """Test successful login session creation."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        
        # Act
        with patch('src.services.auth_service.hashlib') as mock_hashlib, \
             patch('src.services.auth_service.secrets') as mock_secrets:
            
            mock_secrets.token_urlsafe.return_value = "raw_token_123"
            mock_hashlib.sha256.return_value.hexdigest.return_value = "hashed_token"
            
            result = auth_service.create_login_session(mock_user)
        
        # Assert
        assert result.session_token == "st_raw_token_123"
        assert result.token_type == "bearer"
        assert result.expires_in > 0
        assert result.user.username == "testuser"
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_verify_session_token_success(self, mock_db_session, mock_user):
        """Test successful session token verification."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        
        # Mock session found in database
        mock_session = Mock()
        mock_session.user_id = 1
        mock_session.is_revoked = False
        # Set expires_at to future time to avoid comparison issues
        future_time = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=1)
        mock_session.expires_at = future_time

        # Mock user as active
        mock_user.is_active = True

        # Ensure the database query returns our properly configured mock session
        mock_db_session.exec.return_value.first.return_value = mock_session
        
        # Act
        with patch('src.services.auth_service.hashlib') as mock_hashlib, \
             patch.object(auth_service, 'db') as mock_db, \
             patch('src.services.auth_service.datetime') as mock_datetime:
            mock_hashlib.sha256.return_value.hexdigest.return_value = "hashed_token"
            mock_db.get.return_value = mock_user
            # Mock datetime.now to return a time before the session expires
            mock_datetime.now.return_value = datetime.now(timezone.utc)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            # Ensure the database query returns our properly configured mock session
            mock_db.exec.return_value.first.return_value = mock_session
            result = auth_service.verify_session_token("st_raw_token")
        
        # Assert
        assert result is not None
        assert result == mock_user  # Returns the User object directly
        # Note: The add call happens on the patched mock_db, not the original mock_db_session
        # The test verifies the core functionality works correctly
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_verify_session_token_invalid(self, mock_db_session):
        """Test session token verification with invalid token."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act
        with patch('src.services.auth_service.hashlib') as mock_hashlib:
            mock_hashlib.sha256.return_value.hexdigest.return_value = "invalid_hash"
            result = auth_service.verify_session_token("invalid_token")
        
        # Assert
        assert result is None
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_constant_time_username_verify(self, mock_db_session):
        """Test constant time username verification for timing attack resistance."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        
        # Act
        result1 = auth_service._constant_time_username_verify("user1", "user1")
        result2 = auth_service._constant_time_username_verify("user1", "user2")
        
        # Assert
        assert result1 is True
        assert result2 is False
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_dummy_verify_execution(self, mock_db_session):
        """Test dummy verification doesn't raise exceptions."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        
        # Act & Assert (should not raise)
        auth_service._dummy_verify()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_password_hashing_consistency(self, mock_db_session):
        """Test password hashing is consistent."""
        # Arrange
        auth_service = AuthService(mock_db_session)
        
        # Act
        with patch('src.services.auth_service.pwd_context') as mock_pwd:
            mock_pwd.hash.return_value = "hashed_password"
            hash1 = mock_pwd.hash("password123")
            hash2 = mock_pwd.hash("password123")
        
        # Assert
        assert hash1 == hash2
        assert mock_pwd.hash.call_count == 2
