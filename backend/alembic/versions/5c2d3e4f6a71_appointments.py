"""appointments

Revision ID: 5c2d3e4f6a71
Revises: 4b1c2d3e5f60
Create Date: 2026-10-30 15:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5c2d3e4f6a71'
down_revision: Union[str, None] = '4b1c2d3e5f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('appointments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('subject_name', sa.String(length=30), nullable=False),
    sa.Column('subject_birth_year', sa.SmallInteger(), nullable=False),
    sa.Column('subject_gender', sa.String(length=1), nullable=True),
    sa.Column('start_at', sa.DateTime(), nullable=False),
    sa.Column('end_at', sa.DateTime(), nullable=False),
    sa.Column('slot_key', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('visit_type', sa.String(length=6), nullable=False),
    sa.Column('symptom_note', sa.String(length=500), nullable=True),
    sa.Column('cancelled_by', sa.String(length=8), nullable=True),
    sa.Column('cancel_reason', sa.String(length=200), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('doctor_id', 'slot_key', name='uq_appointments_doctor_slot')
    )
    op.create_index('ix_appointments_patient_start', 'appointments', ['patient_id', 'start_at'], unique=False)


def downgrade() -> None:
    # 외래 키가 쓰는 인덱스는 따로 지우지 않는다 (MySQL error 1553). 테이블과 함께 지워진다.
    op.drop_table('appointments')
