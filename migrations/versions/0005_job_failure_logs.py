"""Create centralized failed-task log."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_job_failure_logs"
down_revision = "0004_asset_3d_jobs"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "job_failure_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.String(50), nullable=False),
        sa.Column("task_name", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(30)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("error_type", sa.String(200), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text()),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("task_id", "task_name", "entity_type", "entity_id", "created_at"):
        op.create_index(f"ix_job_failure_logs_{column}", "job_failure_logs", [column])

def downgrade() -> None:
    op.drop_table("job_failure_logs")
