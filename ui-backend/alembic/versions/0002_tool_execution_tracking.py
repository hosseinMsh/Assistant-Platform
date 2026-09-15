"""tool execution tracking

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-14 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tool_executions", sa.Column("mcp_server", sa.String(128), nullable=True))
    op.add_column("tool_executions", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("tool_executions", sa.Column("request_id", sa.String(128), nullable=True))
    op.add_column("tool_executions", sa.Column("confirmation_id", sa.String(128), nullable=True))
    op.add_column("tool_executions", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tool_executions", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tool_executions", sa.Column("duration_ms", sa.Float(), nullable=True))
    op.create_index("ix_tool_executions_confirmation_id", "tool_executions", ["confirmation_id"])


def downgrade() -> None:
    op.drop_index("ix_tool_executions_confirmation_id", table_name="tool_executions")
    op.drop_column("tool_executions", "duration_ms")
    op.drop_column("tool_executions", "finished_at")
    op.drop_column("tool_executions", "started_at")
    op.drop_column("tool_executions", "confirmation_id")
    op.drop_column("tool_executions", "request_id")
    op.drop_column("tool_executions", "error")
    op.drop_column("tool_executions", "mcp_server")
