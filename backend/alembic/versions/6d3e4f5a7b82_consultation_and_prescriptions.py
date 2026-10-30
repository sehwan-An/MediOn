"""consultation and prescriptions

Revision ID: 6d3e4f5a7b82
Revises: 5c2d3e4f6a71
Create Date: 2026-10-30 15:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6d3e4f5a7b82'
down_revision: Union[str, None] = '5c2d3e4f6a71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('doctor_summary', sa.Text(), nullable=True))
    op.add_column('appointments', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('appointments', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.create_table('drugs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('item_code', sa.String(length=20), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('maker', sa.String(length=60), nullable=False),
    sa.Column('form', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drugs_name'), 'drugs', ['name'], unique=False)
    op.create_table('prescriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('issued_at', sa.DateTime(), nullable=False),
    sa.Column('note', sa.String(length=300), nullable=True),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('appointment_id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('prescription_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('prescription_id', sa.Integer(), nullable=False),
    sa.Column('drug_id', sa.Integer(), nullable=False),
    sa.Column('dose', sa.String(length=20), nullable=False),
    sa.Column('times_per_day', sa.SmallInteger(), nullable=False),
    sa.Column('days', sa.SmallInteger(), nullable=False),
    sa.Column('instruction', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['drug_id'], ['drugs.id']),
    sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prescription_items_prescription_id'), 'prescription_items', ['prescription_id'], unique=False)


def downgrade() -> None:
    # 외래 키가 쓰는 인덱스는 따로 지우지 않는다 (MySQL error 1553). 자식 테이블부터 지운다.
    op.drop_table('prescription_items')
    op.drop_table('prescriptions')
    op.drop_table('drugs')
    op.drop_column('appointments', 'completed_at')
    op.drop_column('appointments', 'started_at')
    op.drop_column('appointments', 'doctor_summary')
