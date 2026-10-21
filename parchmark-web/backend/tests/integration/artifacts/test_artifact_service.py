"""
Integration tests for the artifact service: publishing versions and the ownership rule.

They run against the per-worker PostgreSQL container, so foreign keys, check
constraints and the publish row lock behave as they do in production.
"""

import asyncio
from collections.abc import Awaitable, Callable

import pytest
from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.artifact import Artifact
from app.models.artifact_version import ArtifactVersion
from app.models.models import User
from app.schemas.artifact import ArtifactCreate, ArtifactVersionCreate, ArtifactVisibilityUpdate
from app.services import artifact_service

Sessions = async_sessionmaker[AsyncSession]

PAGE = ArtifactCreate(title="Quarterly report", content_type="html", content="<h1>Q3</h1>\n<script>x()</script>")
REVISION = ArtifactVersionCreate(content_type="markdown", content="# Q3, revised")


@pytest.fixture
def sessions(test_db_session: AsyncSession, test_async_db_session: Sessions) -> Sessions:
    """Factory for independent sessions; requesting both fixtures clears the database first."""
    return test_async_db_session


@pytest.fixture
async def users(sessions: Sessions) -> tuple[User, User]:
    """The artifact owner and a second, unrelated user."""
    async with sessions() as session:
        owner = User(username="owner", password_hash="not-a-real-hash")
        stranger = User(username="stranger", password_hash="not-a-real-hash")
        session.add_all([owner, stranger])
        await session.commit()
    return owner, stranger


async def _create(sessions: Sessions, owner: User, request: ArtifactCreate = PAGE) -> int:
    async with sessions() as db:
        return (await artifact_service.create_artifact(db, owner, request)).id


async def _stored(sessions: Sessions, artifact_id: int) -> tuple[Artifact | None, list[ArtifactVersion]]:
    """Read an artifact and its versions straight from the database, bypassing the service."""
    async with sessions() as session:
        artifact = await session.get(Artifact, artifact_id)
        versions = await session.scalars(
            select(ArtifactVersion).filter(ArtifactVersion.artifact_id == artifact_id).order_by(ArtifactVersion.version)
        )
        return artifact, list(versions)


class TestPublish:
    async def test_create_publishes_version_one_as_private(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        async with sessions() as db:
            created = await artifact_service.create_artifact(db, owner, PAGE)

        assert created.title == PAGE.title
        assert created.visibility == "private"
        assert created.current_version.version == 1
        assert created.current_version.content_type == "html"
        artifact, versions = await _stored(sessions, created.id)
        assert artifact is not None
        assert artifact.owner_id == owner.id
        assert artifact.slug == created.slug
        assert artifact.current_version_id == created.current_version.id
        assert [(v.version, v.content) for v in versions] == [(1, PAGE.content)]  # stored raw, not sanitized

    async def test_publishing_a_version_increments_the_number_and_moves_current_version(
        self, sessions: Sessions, users: tuple[User, User]
    ):
        owner, _ = users
        artifact_id = await _create(sessions, owner)

        async with sessions() as db:
            second = await artifact_service.publish_version(db, owner, artifact_id, REVISION)
        async with sessions() as db:
            third = await artifact_service.publish_version(db, owner, artifact_id, REVISION)

        assert (second.current_version.version, third.current_version.version) == (2, 3)
        assert second.current_version.content_type == "markdown"
        artifact, versions = await _stored(sessions, artifact_id)
        assert artifact is not None
        assert artifact.current_version_id == third.current_version.id
        assert [v.version for v in versions] == [1, 2, 3]
        assert versions[0].content == PAGE.content  # earlier versions are kept unchanged
        assert third.slug == second.slug  # the slug never changes

    async def test_version_numbers_are_counted_per_artifact(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        first_id = await _create(sessions, owner)
        async with sessions() as db:
            await artifact_service.publish_version(db, owner, first_id, REVISION)
        async with sessions() as db:
            other = await artifact_service.create_artifact(db, owner, PAGE)

        assert other.current_version.version == 1

    async def test_slugs_are_unique_and_unguessable(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        async with sessions() as db:
            slugs = {(await artifact_service.create_artifact(db, owner, PAGE)).slug for _ in range(3)}

        assert len(slugs) == 3
        assert all(len(slug) >= 22 for slug in slugs)  # 16 random bytes, URL-safe base64

    async def test_concurrent_publishes_get_consecutive_numbers(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        artifact_id = await _create(sessions, owner)

        async with sessions() as holder, sessions() as racer, sessions() as probe:
            # Hold the artifact row lock so the racing publish has to wait on it, then publish through the holder.
            await holder.execute(select(Artifact).filter(Artifact.id == artifact_id).with_for_update())
            racing = asyncio.create_task(artifact_service.publish_version(racer, owner, artifact_id, REVISION))
            for _ in range(100):
                if await probe.scalar(text("SELECT count(*) FROM pg_locks WHERE NOT granted")):
                    break
                await probe.rollback()
                await asyncio.sleep(0.05)
            else:
                racing.cancel()
                pytest.fail("the racing publish never waited on the artifact row lock")

            first = await artifact_service.publish_version(holder, owner, artifact_id, REVISION)
            second = await racing

        assert (first.current_version.version, second.current_version.version) == (2, 3)
        artifact, versions = await _stored(sessions, artifact_id)
        assert artifact is not None
        assert artifact.current_version_id == second.current_version.id
        assert [v.version for v in versions] == [1, 2, 3]


class TestOwnership:
    async def test_another_users_artifact_is_not_readable(self, sessions: Sessions, users: tuple[User, User]):
        owner, stranger = users
        artifact_id = await _create(sessions, owner)

        async with sessions() as db:
            with pytest.raises(HTTPException) as exc_info:
                await artifact_service.get_artifact(db, stranger, artifact_id)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert await artifact_service.list_artifacts(db, stranger) == []
            assert [a.id for a in await artifact_service.list_artifacts(db, owner)] == [artifact_id]

    @pytest.mark.parametrize(
        "operation",
        [
            lambda db, user, artifact_id: artifact_service.publish_version(db, user, artifact_id, REVISION),
            lambda db, user, artifact_id: artifact_service.set_visibility(
                db, user, artifact_id, ArtifactVisibilityUpdate(visibility="unlisted")
            ),
            lambda db, user, artifact_id: artifact_service.delete_artifact(db, user, artifact_id),
        ],
        ids=["publish_version", "set_visibility", "delete_artifact"],
    )
    async def test_another_user_cannot_change_an_artifact(
        self,
        sessions: Sessions,
        users: tuple[User, User],
        operation: Callable[[AsyncSession, User, int], Awaitable[object]],
    ):
        owner, stranger = users
        artifact_id = await _create(sessions, owner)

        async with sessions() as db:
            with pytest.raises(HTTPException) as exc_info:
                await operation(db, stranger, artifact_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        artifact, versions = await _stored(sessions, artifact_id)
        assert artifact is not None
        assert artifact.visibility == "private"
        assert [v.version for v in versions] == [1]


class TestManage:
    async def test_get_returns_the_current_version(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        artifact_id = await _create(sessions, owner)
        async with sessions() as db:
            published = await artifact_service.publish_version(db, owner, artifact_id, REVISION)

        async with sessions() as db:
            fetched = await artifact_service.get_artifact(db, owner, artifact_id)

        assert fetched == published

    async def test_list_returns_newest_first(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        first_id = await _create(sessions, owner)
        second_id = await _create(sessions, owner)

        async with sessions() as db:
            listed = await artifact_service.list_artifacts(db, owner)

        assert [a.id for a in listed] == [second_id, first_id]

    async def test_set_visibility(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        artifact_id = await _create(sessions, owner)

        async with sessions() as db:
            updated = await artifact_service.set_visibility(
                db, owner, artifact_id, ArtifactVisibilityUpdate(visibility="unlisted")
            )

        assert updated.visibility == "unlisted"
        artifact, _versions = await _stored(sessions, artifact_id)
        assert artifact is not None
        assert artifact.visibility == "unlisted"

    async def test_delete_removes_the_artifact_and_its_versions(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        artifact_id = await _create(sessions, owner)
        async with sessions() as db:
            await artifact_service.publish_version(db, owner, artifact_id, REVISION)

        async with sessions() as db:
            deleted = await artifact_service.delete_artifact(db, owner, artifact_id)

        assert deleted.deleted_id == str(artifact_id)
        assert await _stored(sessions, artifact_id) == (None, [])

    async def test_missing_artifact_is_not_found(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users

        async with sessions() as db:
            with pytest.raises(HTTPException) as exc_info:
                await artifact_service.get_artifact(db, owner, 999_999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_deleting_the_owner_deletes_their_artifacts(self, sessions: Sessions, users: tuple[User, User]):
        owner, _ = users
        artifact_id = await _create(sessions, owner)

        async with sessions() as session:
            await session.execute(text("DELETE FROM users WHERE id = :id"), {"id": owner.id})
            await session.commit()

        assert await _stored(sessions, artifact_id) == (None, [])
