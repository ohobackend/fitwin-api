"""Add background-removed garment image URL."""
from alembic import op
import sqlalchemy as sa

revision = "0002_garment_processed_image"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("garments", sa.Column("processed_image_url", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("garments", "processed_image_url")
