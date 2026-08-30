"""initial advanced schema

Revision ID: 0001_advanced
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_advanced"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create_all en runtime cubre SQLite; esta revisión documenta el esquema prod.
    bind = op.get_bind()
    from app.db.models import Base

    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    from app.db.models import Base

    Base.metadata.drop_all(bind=bind)
