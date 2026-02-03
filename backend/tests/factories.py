"""
Factory classes for generating test data using factory-boy and Faker.
Provides enterprise-grade test data generation for models and schemas.
"""

from datetime import UTC, datetime
from typing import Any

import factory
from faker import Faker

from app.auth.auth import get_password_hash
from app.models.models import Note, User

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for creating User model instances."""

    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f"user{n:04d}")
    password_hash = factory.LazyAttribute(lambda obj: get_password_hash("testpass123"))
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class UserDataFactory(factory.DictFactory):
    """Factory for creating user data dictionaries for API requests."""

    username = factory.Sequence(lambda n: f"test{n:04d}")
    password = "testpass123"


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances."""

    username = factory.Sequence(lambda n: f"admin{n:04d}")
    password_hash = factory.LazyAttribute(lambda obj: get_password_hash("adminpass123"))


class NoteFactory(factory.Factory):
    """Factory for creating Note model instances."""

    class Meta:
        model = Note

    id = factory.Sequence(lambda n: f"note-{n:04d}")
    user_id = factory.SubFactory(UserFactory)
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4)[:255])
    content = factory.LazyAttribute(lambda obj: f"# {obj.title}\n\n{fake.text(max_nb_chars=500)}")
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


class NoteDataFactory(factory.DictFactory):
    """Factory for creating note data dictionaries for API requests."""

    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4)[:255])
    content = factory.LazyAttribute(lambda obj: f"# {obj.title}\n\n{fake.paragraph(nb_sentences=5)}")


class NoteUpdateDataFactory(factory.DictFactory):
    """Factory for creating note update data dictionaries."""

    title = factory.Maybe(
        "include_title",
        yes_declaration=factory.LazyFunction(lambda: fake.sentence(nb_words=3)[:255]),
        no_declaration=None,
    )
    content = factory.Maybe(
        "include_content",
        yes_declaration=factory.LazyAttribute(lambda obj: f"# Updated Note\n\n{fake.paragraph(nb_sentences=3)}"),
        no_declaration=None,
    )


class MarkdownContentFactory(factory.DictFactory):
    """Factory for generating various markdown content samples."""

    simple = factory.LazyFunction(lambda: f"# {fake.sentence()}\n\n{fake.paragraph()}")

    complex = factory.LazyFunction(
        lambda: f"""# {fake.sentence()}

This note has **bold** and *italic* text.

## {fake.sentence(nb_words=3)}

- {fake.sentence()}
- {fake.sentence()}
- {fake.sentence()}

```python
def {fake.word()}():
    return "{fake.sentence()}"
```

> {fake.sentence()}

[{fake.word()}]({fake.url()})
"""
    )

    no_title = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=3))

    empty = ""

    only_title = factory.LazyFunction(lambda: f"# {fake.sentence()}")

    multiple_h1 = factory.LazyFunction(
        lambda: f"""# {fake.sentence()}

{fake.paragraph()}

# {fake.sentence()}

{fake.paragraph()}
"""
    )

    title_with_formatting = factory.LazyFunction(lambda: f"# **{fake.word()}** with *{fake.word()}*")


class AuthTokenFactory:
    """Factory for creating authentication tokens and headers."""

    @staticmethod
    def create_token_data(username: str = None) -> dict[str, str]:
        """Create token data dictionary."""
        return {"sub": username or fake.user_name()}

    @staticmethod
    def create_auth_headers(token: str) -> dict[str, str]:
        """Create authentication headers dictionary."""
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def create_invalid_headers() -> dict[str, str]:
        """Create invalid authentication headers."""
        return {"Authorization": f"Bearer {fake.uuid4()}"}


class APIResponseFactory(factory.DictFactory):
    """Factory for creating API response data."""

    success_message = factory.LazyFunction(lambda: {"message": fake.sentence()})

    error_response = factory.LazyFunction(lambda: {"detail": fake.sentence()})

    validation_error = factory.LazyFunction(
        lambda: {"detail": "Validation error", "errors": [fake.sentence() for _ in range(fake.random_int(1, 3))]}
    )


class DatabaseTestDataFactory:
    """Factory for creating database test data scenarios."""

    @staticmethod
    def create_user_with_notes(session, num_notes: int = 3) -> tuple[User, list[Note]]:
        """Create a user with multiple notes."""
        user = UserFactory()
        session.add(user)
        session.commit()
        session.refresh(user)

        notes = []
        for i in range(num_notes):
            note = NoteFactory(user_id=user.id, id=f"note-{user.id}-{i + 1}")
            session.add(note)
            notes.append(note)

        session.commit()

        for note in notes:
            session.refresh(note)

        return user, notes

    @staticmethod
    def create_multiple_users_with_notes(session, num_users: int = 2, notes_per_user: int = 2):
        """Create multiple users each with their own notes."""
        return [DatabaseTestDataFactory.create_user_with_notes(session, notes_per_user) for _ in range(num_users)]


class EdgeCaseDataFactory:
    """Factory for creating edge case test data."""

    @staticmethod
    def long_string(length: int = 1000) -> str:
        """Generate a long string for testing limits."""
        return fake.text(max_nb_chars=length)

    @staticmethod
    def empty_values() -> dict[str, Any]:
        """Generate various empty value scenarios."""
        return {
            "empty_string": "",
            "none_value": None,
            "whitespace": "   ",
            "tab_newline": "\t\n",
        }

    @staticmethod
    def invalid_user_data() -> list[dict[str, Any]]:
        """Generate invalid user data scenarios."""
        return [
            {"username": "", "password": "validpass"},
            {"username": "usr", "password": "validpass"},  # Too short username
            {"username": "validuser", "password": ""},
            {"username": "validuser", "password": "pwd"},  # Too short password
            {"username": EdgeCaseDataFactory.long_string(100), "password": "validpass"},
            {"password": "missing_username"},
            {"username": "missing_password"},
            {},
        ]

    @staticmethod
    def invalid_note_data() -> list[dict[str, Any]]:
        """Generate invalid note data scenarios."""
        return [
            {"title": "", "content": "valid content"},
            {"title": "tit", "content": "valid content"},  # Too short title
            {"title": "valid title", "content": ""},
            {"title": "valid title", "content": "abc"},  # Too short content
            {"title": EdgeCaseDataFactory.long_string(300), "content": "valid content"},
            {"content": "missing_title"},
            {"title": "missing_content"},
            {},
        ]


class SecurityTestDataFactory:
    """Factory for creating security-related test data."""

    @staticmethod
    def sql_injection_strings() -> list[str]:
        """Generate SQL injection test strings."""
        return [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "admin' /*",
            "' OR 1=1--",
            "' UNION SELECT * FROM users--",
        ]

    @staticmethod
    def xss_strings() -> list[str]:
        """Generate XSS test strings."""
        return [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'><script>alert('xss')</script>",
            "\"><script>alert('xss')</script>",
        ]

    @staticmethod
    def invalid_tokens() -> list[str]:
        """Generate various invalid token formats."""
        return [
            "invalid-token",
            "Bearer invalid-token",
            "",
            "   ",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            fake.uuid4(),
            "malformed.jwt.token.structure",
        ]


# Convenience functions for common test scenarios
def create_test_user(session=None, **kwargs) -> User:
    """Create a test user with optional database session."""
    user = UserFactory(**kwargs)
    if session:
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def create_test_note(session=None, user=None, **kwargs) -> Note:
    """Create a test note with optional database session and user."""
    if user:
        kwargs["user_id"] = user.id
    note = NoteFactory(**kwargs)
    if session:
        session.add(note)
        session.commit()
        session.refresh(note)
    return note


def create_test_data_scenario(scenario: str, session=None):
    """Create predefined test data scenarios."""
    scenarios = {
        "single_user_no_notes": lambda: create_test_user(session),
        "single_user_with_notes": lambda: DatabaseTestDataFactory.create_user_with_notes(session, 3),
        "multiple_users": lambda: DatabaseTestDataFactory.create_multiple_users_with_notes(session, 3, 2),
    }

    if scenario in scenarios:
        return scenarios[scenario]()
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
