"""medication checks

Revision ID: 9b6c7d8e0f15
Revises: 8a5b6c7d9e04
Create Date: 2026-10-30 17:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9b6c7d8e0f15'
down_revision: Union[str, None] = '8a5b6c7d9e04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('medication_checks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('prescription_id', sa.Integer(), nullable=False),
    sa.Column('taken_on', sa.Date(), nullable=False),
    sa.Column('slot', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('prescription_id', 'taken_on', 'slot', name='uq_medication_checks_slot')
    )
    op.create_index(op.f('ix_medication_checks_patient_id'), 'medication_checks', ['patient_id'], unique=False)


def downgrade() -> None:
    # 외래 키가 쓰는 인덱스는 따로 지우지 않는다 (MySQL error 1553)
    op.drop_table('medication_checks')
