"""Added randomize flag to Assignment

Revision ID: fc5f01c69efe
Revises: e43177bfe90b
Create Date: 2021-04-01 10:13:14.146790

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc5f01c69efe'
down_revision = 'e43177bfe90b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('assignment', sa.Column('randomize', sa.Boolean(), default=False))


def downgrade():
    op.drop_column('assignment', 'randomize')
