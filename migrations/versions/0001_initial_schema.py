"""Create stage-one FitTwin schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("garments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_image_url", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100)), sa.Column("color", sa.String(100)),
        sa.Column("status", sa.String(30), server_default="uploaded", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"))
    op.create_index("ix_garments_user_id", "garments", ["user_id"])
    op.create_table("fitting_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("garment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result_type", sa.String(2), nullable=False), sa.Column("result_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("result_type IN ('2d', '3d')", name="ck_fitting_result_type"),
        sa.ForeignKeyConstraint(["garment_id"], ["garments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"))
    op.create_index("ix_fitting_results_garment_id", "fitting_results", ["garment_id"])
    op.create_index("ix_fitting_results_user_id", "fitting_results", ["user_id"])
    op.create_table("assets_3d",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("garment_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("glb_url", sa.Text()), sa.Column("thumbnail_url", sa.Text()),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["garment_id"], ["garments.id"], ondelete="CASCADE"))

def downgrade() -> None:
    op.drop_table("assets_3d")
    op.drop_index("ix_fitting_results_user_id", table_name="fitting_results")
    op.drop_index("ix_fitting_results_garment_id", table_name="fitting_results")
    op.drop_table("fitting_results")
    op.drop_index("ix_garments_user_id", table_name="garments")
    op.drop_table("garments")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
