"""Add asynchronous 3D asset job metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0004_asset_3d_jobs"
down_revision = "0003_fitting_job_cache"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("assets_3d", sa.Column("job_id", sa.String(50), nullable=True))
    op.add_column("assets_3d", sa.Column("error_message", sa.Text(), nullable=True))
    op.create_index("ix_assets_3d_job_id", "assets_3d", ["job_id"])

def downgrade() -> None:
    op.drop_index("ix_assets_3d_job_id", table_name="assets_3d")
    op.drop_column("assets_3d", "error_message")
    op.drop_column("assets_3d", "job_id")
