"""Add 2D fitting cache and async job fields."""
from alembic import op
import sqlalchemy as sa

revision = "0003_fitting_job_cache"
down_revision = "0002_garment_processed_image"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column("fitting_results", "result_url", existing_type=sa.Text(), nullable=True)
    op.add_column("fitting_results", sa.Column("input_image_url", sa.Text(), nullable=True))
    op.add_column("fitting_results", sa.Column("combination_hash", sa.String(64), nullable=True))
    op.add_column("fitting_results", sa.Column("job_id", sa.String(50), nullable=True))
    op.add_column("fitting_results", sa.Column("status", sa.String(30), server_default="pending", nullable=False))
    op.create_index("ix_fitting_results_combination_hash", "fitting_results", ["combination_hash"], unique=True)
    op.create_index("ix_fitting_results_job_id", "fitting_results", ["job_id"])

def downgrade() -> None:
    op.drop_index("ix_fitting_results_job_id", table_name="fitting_results")
    op.drop_index("ix_fitting_results_combination_hash", table_name="fitting_results")
    op.drop_column("fitting_results", "status")
    op.drop_column("fitting_results", "job_id")
    op.drop_column("fitting_results", "combination_hash")
    op.drop_column("fitting_results", "input_image_url")
    op.alter_column("fitting_results", "result_url", existing_type=sa.Text(), nullable=False)
