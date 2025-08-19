"""
Unit tests for Pydantic schemas (app.schemas.schemas).
Tests request/response models, validation, and serialization.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    ErrorResponse,
    ValidationErrorResponse,
    MessageResponse,
    DeleteResponse,
)


class TestUserSchemas:
    """Test user-related Pydantic schemas."""
    
    class TestUserCreate:
        """Test UserCreate schema."""
        
        def test_user_create_valid(self):
            """Test valid user creation data."""
            data = {
                "username": "testuser",
                "password": "testpass123"
            }
            user = UserCreate(**data)
            
            assert user.username == "testuser"
            assert user.password == "testpass123"
        
        def test_user_create_json_serialization(self):
            """Test UserCreate JSON serialization."""
            user = UserCreate(username="testuser", password="testpass123")
            json_data = user.model_dump()
            
            assert json_data == {
                "username": "testuser",
                "password": "testpass123"
            }
        
        def test_user_create_from_json(self):
            """Test UserCreate from JSON data."""
            json_data = '{"username": "testuser", "password": "testpass123"}'
            user = UserCreate.model_validate_json(json_data)
            
            assert user.username == "testuser"
            assert user.password == "testpass123"
        
        def test_user_create_missing_username(self):
            """Test UserCreate with missing username."""
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(password="testpass123")
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("username",)
            assert errors[0]["type"] == "missing"
        
        def test_user_create_missing_password(self):
            """Test UserCreate with missing password."""
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(username="testuser")
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("password",)
            assert errors[0]["type"] == "missing"
        
        def test_user_create_empty_username(self):
            """Test UserCreate with empty username."""
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(username="", password="testpass123")
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("username",)
            assert "at least 4 character" in str(errors[0]["msg"])
        
        def test_user_create_empty_password(self):
            """Test UserCreate with empty password."""
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(username="testuser", password="")
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("password",)
            assert "at least 4 character" in str(errors[0]["msg"])
        
        def test_user_create_username_too_short(self):
            """Test UserCreate with username too short (3 chars)."""
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(username="abc", password="testpass123")
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("username",)
            assert "at least 4 character" in str(errors[0]["msg"])
        
        def test_user_create_password_too_short(self):
            """Test UserCreate with password too short (3 chars)."""
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(username="testuser", password="abc")
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("password",)
            assert "at least 4 character" in str(errors[0]["msg"])
        
        def test_user_create_minimum_length_boundary(self):
            """Test UserCreate with exactly minimum length (4 chars)."""
            user = UserCreate(username="abcd", password="pass")
            assert user.username == "abcd"
            assert user.password == "pass"
        
        def test_user_create_username_too_long(self):
            """Test UserCreate with username exceeding max length."""
            long_username = "a" * 51  # Max is 50
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(username=long_username, password="testpass123")
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("username",)
            assert "at most 50 characters" in str(errors[0]["msg"])
        
        @pytest.mark.parametrize("username", [
            "abcd",  # Minimum length (4 chars)
            "a" * 50,  # Maximum length
            "user_with_underscore",
            "user-with-dash",
            "user.with.dots",
            "user123",
            "UserWithMixedCase",
            "user@domain.com",
        ])
        def test_user_create_username_valid_formats(self, username):
            """Test UserCreate with various valid username formats."""
            user = UserCreate(username=username, password="testpass123")
            assert user.username == username
        
        @pytest.mark.parametrize("password", [
            "pass",  # Minimum length (4 chars)
            "password",
            "password123",
            "password_with_underscore",
            "password-with-dash",
            "password.with.dots",
            "Password123!@#",
            "very_long_password_that_exceeds_normal_expectations",
            "пароль123",  # Unicode
        ])
        def test_user_create_password_valid_formats(self, password):
            """Test UserCreate with various valid password formats."""
            user = UserCreate(username="testuser", password=password)
            assert user.password == password
    
    class TestUserLogin:
        """Test UserLogin schema."""
        
        def test_user_login_valid(self):
            """Test valid user login data."""
            login = UserLogin(username="testuser", password="testpass123")
            
            assert login.username == "testuser"
            assert login.password == "testpass123"
        
        def test_user_login_missing_fields(self):
            """Test UserLogin with missing fields."""
            with pytest.raises(ValidationError) as exc_info:
                UserLogin(username="testuser")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("password",) for error in errors)
        
        def test_user_login_json_serialization(self):
            """Test UserLogin JSON serialization."""
            login = UserLogin(username="testuser", password="testpass123")
            json_data = login.model_dump()
            
            assert json_data == {
                "username": "testuser",
                "password": "testpass123"
            }
    
    class TestUserResponse:
        """Test UserResponse schema."""
        
        def test_user_response_valid(self):
            """Test valid user response data."""
            response = UserResponse(username="testuser")
            
            assert response.username == "testuser"
        
        def test_user_response_missing_username(self):
            """Test UserResponse with missing username."""
            with pytest.raises(ValidationError) as exc_info:
                UserResponse()
            
            errors = exc_info.value.errors()
            assert len(errors) == 1
            assert errors[0]["loc"] == ("username",)
        
        def test_user_response_from_model(self, sample_user):
            """Test UserResponse creation from SQLAlchemy model."""
            response = UserResponse.model_validate(sample_user)
            
            assert response.username == sample_user.username
        
        def test_user_response_no_password_exposure(self, sample_user):
            """Test that UserResponse doesn't expose password."""
            response = UserResponse.model_validate(sample_user)
            json_data = response.model_dump()
            
            assert "password" not in json_data
            assert "password_hash" not in json_data
            assert json_data == {"username": sample_user.username}


class TestTokenSchemas:
    """Test token-related Pydantic schemas."""
    
    class TestToken:
        """Test Token schema."""
        
        def test_token_valid(self):
            """Test valid token data."""
            token = Token(access_token="abc123.def456.ghi789")
            
            assert token.access_token == "abc123.def456.ghi789"
            assert token.token_type == "bearer"  # Default value
        
        def test_token_custom_type(self):
            """Test token with custom token type."""
            token = Token(access_token="abc123", token_type="custom")
            
            assert token.token_type == "custom"
        
        def test_token_missing_access_token(self):
            """Test Token with missing access_token."""
            with pytest.raises(ValidationError) as exc_info:
                Token()
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("access_token",) for error in errors)
        
        def test_token_json_serialization(self):
            """Test Token JSON serialization."""
            token = Token(access_token="abc123")
            json_data = token.model_dump()
            
            assert json_data == {
                "access_token": "abc123",
                "token_type": "bearer"
            }
    
    class TestTokenData:
        """Test TokenData schema."""
        
        def test_token_data_valid(self):
            """Test valid token data."""
            token_data = TokenData(username="testuser")
            
            assert token_data.username == "testuser"
        
        def test_token_data_none_username(self):
            """Test TokenData with None username."""
            token_data = TokenData(username=None)
            
            assert token_data.username is None
        
        def test_token_data_no_username(self):
            """Test TokenData without username."""
            token_data = TokenData()
            
            assert token_data.username is None


class TestNoteSchemas:
    """Test note-related Pydantic schemas."""
    
    class TestNoteCreate:
        """Test NoteCreate schema."""
        
        def test_note_create_valid(self):
            """Test valid note creation data."""
            note = NoteCreate(
                title="Test Note",
                content="# Test Note\n\nThis is test content."
            )
            
            assert note.title == "Test Note"
            assert note.content == "# Test Note\n\nThis is test content."
        
        def test_note_create_missing_title(self):
            """Test NoteCreate with missing title."""
            with pytest.raises(ValidationError) as exc_info:
                NoteCreate(content="Test content")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("title",) for error in errors)
        
        def test_note_create_missing_content(self):
            """Test NoteCreate with missing content."""
            with pytest.raises(ValidationError) as exc_info:
                NoteCreate(title="Test Note")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("content",) for error in errors)
        
        def test_note_create_empty_title(self):
            """Test NoteCreate with empty title."""
            with pytest.raises(ValidationError) as exc_info:
                NoteCreate(title="", content="Test content")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("title",) for error in errors)
        
        def test_note_create_title_too_long(self):
            """Test NoteCreate with title exceeding max length."""
            long_title = "a" * 256  # Max is 255
            with pytest.raises(ValidationError) as exc_info:
                NoteCreate(title=long_title, content="Test content")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("title",) for error in errors)
        
        def test_note_create_empty_content_not_allowed(self):
            """Test NoteCreate with empty content (minimum length 4)."""
            with pytest.raises(ValidationError) as exc_info:
                NoteCreate(title="Test Note", content="")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("content",) for error in errors)
        
        def test_note_create_content_too_short(self):
            """Test NoteCreate with content too short (3 chars)."""
            with pytest.raises(ValidationError) as exc_info:
                NoteCreate(title="Test Note", content="abc")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("content",) for error in errors)
        
        def test_note_create_title_too_short(self):
            """Test NoteCreate with title too short (3 chars)."""
            with pytest.raises(ValidationError) as exc_info:
                NoteCreate(title="abc", content="Test content")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("title",) for error in errors)
        
        def test_note_create_minimum_length_boundary(self):
            """Test NoteCreate with exactly minimum length (4 chars)."""
            note = NoteCreate(title="abcd", content="test")
            assert note.title == "abcd"
            assert note.content == "test"
        
        @pytest.mark.parametrize("title", [
            "Shrt",  # Minimum length (4 chars)
            "A" * 255,  # Maximum length
            "Title with spaces",
            "Title-with-dashes",
            "Title_with_underscores",
            "Title.with.dots",
            "Title123",
            "タイトル",  # Unicode
            "🚀 Emoji Title",
        ])
        def test_note_create_title_formats(self, title):
            """Test NoteCreate with various title formats."""
            note = NoteCreate(title=title, content="Test content")
            assert note.title == title
        
        def test_note_create_large_content(self):
            """Test NoteCreate with large content."""
            large_content = "# Large Note\n\n" + ("Content line.\n" * 10000)
            note = NoteCreate(title="Large Note", content=large_content)
            
            assert note.title == "Large Note"
            assert note.content == large_content
            assert len(note.content) > 100000
    
    class TestNoteUpdate:
        """Test NoteUpdate schema."""
        
        def test_note_update_title_only(self):
            """Test NoteUpdate with only title."""
            update = NoteUpdate(title="Updated Title")
            
            assert update.title == "Updated Title"
            assert update.content is None
        
        def test_note_update_content_only(self):
            """Test NoteUpdate with only content."""
            update = NoteUpdate(content="Updated content")
            
            assert update.title is None
            assert update.content == "Updated content"
        
        def test_note_update_both_fields(self):
            """Test NoteUpdate with both title and content."""
            update = NoteUpdate(
                title="Updated Title",
                content="Updated content"
            )
            
            assert update.title == "Updated Title"
            assert update.content == "Updated content"
        
        def test_note_update_empty(self):
            """Test NoteUpdate with no fields."""
            update = NoteUpdate()
            
            assert update.title is None
            assert update.content is None
        
        def test_note_update_empty_values(self):
            """Test NoteUpdate with empty string values (should fail due to min length)."""
            with pytest.raises(ValidationError) as exc_info:
                NoteUpdate(title="", content="")
            
            errors = exc_info.value.errors()
            # Should have errors for both title and content being too short
            error_fields = {error["loc"][0] for error in errors}
            assert "title" in error_fields
            assert "content" in error_fields
        
        def test_note_update_values_too_short(self):
            """Test NoteUpdate with values too short (3 chars)."""
            with pytest.raises(ValidationError) as exc_info:
                NoteUpdate(title="abc", content="def")
            
            errors = exc_info.value.errors()
            error_fields = {error["loc"][0] for error in errors}
            assert "title" in error_fields
            assert "content" in error_fields
        
        def test_note_update_minimum_length_boundary(self):
            """Test NoteUpdate with exactly minimum length (4 chars)."""
            update = NoteUpdate(title="abcd", content="test")
            assert update.title == "abcd"
            assert update.content == "test"
        
        def test_note_update_validation_constraints(self):
            """Test NoteUpdate respects validation constraints."""
            # Title too long
            long_title = "a" * 256
            with pytest.raises(ValidationError):
                NoteUpdate(title=long_title)
        
        def test_note_update_json_serialization(self):
            """Test NoteUpdate JSON serialization with partial data."""
            update = NoteUpdate(title="New Title")
            json_data = update.model_dump(exclude_none=True)
            
            assert json_data == {"title": "New Title"}
            assert "content" not in json_data
    
    class TestNoteResponse:
        """Test NoteResponse schema."""
        
        def test_note_response_valid(self):
            """Test valid note response data."""
            response = NoteResponse(
                id="note-123",
                title="Test Note",
                content="# Test Note\n\nContent",
                createdAt="2023-01-01T12:00:00",
                updatedAt="2023-01-01T12:30:00"
            )
            
            assert response.id == "note-123"
            assert response.title == "Test Note"
            assert response.content == "# Test Note\n\nContent"
            assert response.createdAt == "2023-01-01T12:00:00"
            assert response.updatedAt == "2023-01-01T12:30:00"
        
        def test_note_response_missing_fields(self):
            """Test NoteResponse with missing required fields."""
            with pytest.raises(ValidationError) as exc_info:
                NoteResponse(title="Test Note")
            
            errors = exc_info.value.errors()
            required_fields = {"id", "content", "createdAt", "updatedAt"}
            error_fields = {error["loc"][0] for error in errors}
            
            assert required_fields.intersection(error_fields)
        
        def test_note_response_from_model(self, sample_note):
            """Test NoteResponse creation from SQLAlchemy model."""
            # Manually create response since we need datetime formatting
            response = NoteResponse(
                id=sample_note.id,
                title=sample_note.title,
                content=sample_note.content,
                createdAt=sample_note.created_at.isoformat(),
                updatedAt=sample_note.updated_at.isoformat()
            )
            
            assert response.id == sample_note.id
            assert response.title == sample_note.title
            assert response.content == sample_note.content
            assert isinstance(response.createdAt, str)
            assert isinstance(response.updatedAt, str)
        
        def test_note_response_datetime_formatting(self):
            """Test NoteResponse with various datetime formats."""
            iso_datetime = "2023-01-01T12:00:00.000Z"
            response = NoteResponse(
                id="note-123",
                title="Test Note", 
                content="Content",
                createdAt=iso_datetime,
                updatedAt=iso_datetime
            )
            
            assert response.createdAt == iso_datetime
            assert response.updatedAt == iso_datetime


class TestResponseSchemas:
    """Test response-related Pydantic schemas."""
    
    class TestErrorResponse:
        """Test ErrorResponse schema."""
        
        def test_error_response_valid(self):
            """Test valid error response."""
            error = ErrorResponse(detail="Something went wrong")
            
            assert error.detail == "Something went wrong"
        
        def test_error_response_missing_detail(self):
            """Test ErrorResponse with missing detail."""
            with pytest.raises(ValidationError):
                ErrorResponse()
    
    class TestValidationErrorResponse:
        """Test ValidationErrorResponse schema."""
        
        def test_validation_error_response_basic(self):
            """Test basic validation error response."""
            error = ValidationErrorResponse(detail="Validation failed")
            
            assert error.detail == "Validation failed"
            assert error.errors is None
        
        def test_validation_error_response_with_errors(self):
            """Test validation error response with errors list."""
            errors_list = [
                {"field": "username", "message": "Required"},
                {"field": "password", "message": "Too short"}
            ]
            error = ValidationErrorResponse(
                detail="Validation failed",
                errors=errors_list
            )
            
            assert error.detail == "Validation failed"
            assert error.errors == errors_list
    
    class TestMessageResponse:
        """Test MessageResponse schema."""
        
        def test_message_response_valid(self):
            """Test valid message response."""
            message = MessageResponse(message="Operation successful")
            
            assert message.message == "Operation successful"
        
        def test_message_response_missing_message(self):
            """Test MessageResponse with missing message."""
            with pytest.raises(ValidationError):
                MessageResponse()
    
    class TestDeleteResponse:
        """Test DeleteResponse schema."""
        
        def test_delete_response_valid(self):
            """Test valid delete response."""
            response = DeleteResponse(
                message="Note deleted successfully",
                deleted_id="note-123"
            )
            
            assert response.message == "Note deleted successfully"
            assert response.deleted_id == "note-123"
        
        def test_delete_response_missing_fields(self):
            """Test DeleteResponse with missing fields."""
            with pytest.raises(ValidationError) as exc_info:
                DeleteResponse(message="Deleted")
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("deleted_id",) for error in errors)


class TestSchemaIntegration:
    """Test integration between different schemas."""
    
    def test_user_create_to_response_conversion(self):
        """Test converting UserCreate to UserResponse format."""
        user_create = UserCreate(username="testuser", password="testpass123")
        
        # Simulate what would happen in the API
        user_response_data = {"username": user_create.username}
        user_response = UserResponse(**user_response_data)
        
        assert user_response.username == user_create.username
        # Password should not be in response
        assert not hasattr(user_response, 'password')
    
    def test_note_create_to_response_conversion(self):
        """Test converting NoteCreate to NoteResponse format."""
        note_create = NoteCreate(
            title="Test Note",
            content="# Test Note\n\nContent"
        )
        
        # Simulate what would happen in the API
        current_time = datetime.now().isoformat()
        note_response = NoteResponse(
            id="note-123",
            title=note_create.title,
            content=note_create.content,
            createdAt=current_time,
            updatedAt=current_time
        )
        
        assert note_response.title == note_create.title
        assert note_response.content == note_create.content
        assert note_response.id == "note-123"
    
    def test_note_update_partial_application(self):
        """Test applying NoteUpdate to existing note data."""
        # Original note data
        original_note = NoteResponse(
            id="note-123",
            title="Original Title",
            content="Original content",
            createdAt="2023-01-01T12:00:00",
            updatedAt="2023-01-01T12:00:00"
        )
        
        # Update with only title
        update = NoteUpdate(title="Updated Title")
        
        # Simulate partial update
        updated_data = original_note.model_dump()
        update_data = update.model_dump(exclude_none=True)
        updated_data.update(update_data)
        updated_data["updatedAt"] = "2023-01-01T13:00:00"
        
        updated_note = NoteResponse(**updated_data)
        
        assert updated_note.title == "Updated Title"
        assert updated_note.content == "Original content"  # Unchanged
        assert updated_note.updatedAt != original_note.updatedAt