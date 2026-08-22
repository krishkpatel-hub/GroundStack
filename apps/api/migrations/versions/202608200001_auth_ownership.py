"""auth ownership fields

Revision ID: 202608200001
Revises: 202608190002
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202608200001"
down_revision: str | None = "202608190002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("owner_subject", sa.String(length=200)))
    op.add_column("conversations", sa.Column("demo_session_id", sa.String(length=120)))
    op.create_index("ix_conversations_owner_subject", "conversations", ["owner_subject"])
    op.create_index("ix_conversations_demo_session_id", "conversations", ["demo_session_id"])

    op.add_column("messages", sa.Column("owner_subject", sa.String(length=200)))
    op.create_index("ix_messages_owner_subject", "messages", ["owner_subject"])

    op.add_column("message_feedback", sa.Column("owner_subject", sa.String(length=200)))
    op.add_column("message_feedback", sa.Column("demo_session_id", sa.String(length=120)))
    op.create_index("ix_message_feedback_owner_subject", "message_feedback", ["owner_subject"])


def downgrade() -> None:
    op.drop_index("ix_message_feedback_owner_subject", table_name="message_feedback")
    op.drop_column("message_feedback", "demo_session_id")
    op.drop_column("message_feedback", "owner_subject")
    op.drop_index("ix_messages_owner_subject", table_name="messages")
    op.drop_column("messages", "owner_subject")
    op.drop_index("ix_conversations_demo_session_id", table_name="conversations")
    op.drop_index("ix_conversations_owner_subject", table_name="conversations")
    op.drop_column("conversations", "demo_session_id")
    op.drop_column("conversations", "owner_subject")
