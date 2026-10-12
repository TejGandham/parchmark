"""add notes events notify trigger

Revision ID: 8f4d2b1c9a7e
Revises: 7f1c343772e8
Create Date: 2026-05-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f4d2b1c9a7e"
down_revision: str | Sequence[str] | None = "7f1c343772e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOTIFY_FUNCTION = "notify_notes_events"
_INSERT_DELETE_TRIGGER = "notes_notify_events_insert_delete"
_UPDATE_TRIGGER = "notes_notify_events_update"


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Install a transactional notes_events NOTIFY trigger on notes."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "notes"):
        return

    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_NOTIFY_FUNCTION}()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            payload text;
        BEGIN
            IF TG_OP = 'INSERT' THEN
                payload = json_build_object(
                    'user_id', NEW.user_id,
                    'kind', 'created',
                    'note_id', NEW.id
                )::text;
                PERFORM pg_notify('notes_events', payload);
                RETURN NEW;
            ELSIF TG_OP = 'UPDATE' THEN
                payload = json_build_object(
                    'user_id', NEW.user_id,
                    'kind', 'updated',
                    'note_id', NEW.id
                )::text;
                PERFORM pg_notify('notes_events', payload);
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                payload = json_build_object(
                    'user_id', OLD.user_id,
                    'kind', 'deleted',
                    'note_id', OLD.id
                )::text;
                PERFORM pg_notify('notes_events', payload);
                RETURN OLD;
            END IF;

            RETURN NULL;
        END;
        $$;
        """
    )
    op.execute(f"DROP TRIGGER IF EXISTS {_INSERT_DELETE_TRIGGER} ON notes")
    op.execute(f"DROP TRIGGER IF EXISTS {_UPDATE_TRIGGER} ON notes")
    op.execute(
        f"""
        CREATE TRIGGER {_INSERT_DELETE_TRIGGER}
        AFTER INSERT OR DELETE ON notes
        FOR EACH ROW
        EXECUTE FUNCTION {_NOTIFY_FUNCTION}()
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER {_UPDATE_TRIGGER}
        AFTER UPDATE OF title, content ON notes
        FOR EACH ROW
        WHEN (OLD.title IS DISTINCT FROM NEW.title OR OLD.content IS DISTINCT FROM NEW.content)
        EXECUTE FUNCTION {_NOTIFY_FUNCTION}()
        """
    )


def downgrade() -> None:
    """Remove the notes_events NOTIFY triggers and trigger function."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if _table_exists(inspector, "notes"):
        op.execute(f"DROP TRIGGER IF EXISTS {_INSERT_DELETE_TRIGGER} ON notes")
        op.execute(f"DROP TRIGGER IF EXISTS {_UPDATE_TRIGGER} ON notes")
    op.execute(f"DROP FUNCTION IF EXISTS {_NOTIFY_FUNCTION}()")
