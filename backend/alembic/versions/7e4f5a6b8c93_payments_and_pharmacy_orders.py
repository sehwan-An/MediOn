"""payments and pharmacy orders

Revision ID: 7e4f5a6b8c93
Revises: 6d3e4f5a7b82
Create Date: 2026-10-30 15:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7e4f5a6b8c93'
down_revision: Union[str, None] = '6d3e4f5a7b82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.String(length=64), nullable=False),
    sa.Column('order_name', sa.String(length=100), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('payment_key', sa.String(length=200), nullable=True),
    sa.Column('method', sa.String(length=30), nullable=True),
    sa.Column('receipt_url', sa.String(length=500), nullable=True),
    sa.Column('fail_code', sa.String(length=60), nullable=True),
    sa.Column('fail_message', sa.String(length=300), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('appointment_id'),
    sa.UniqueConstraint('order_id'),
    sa.UniqueConstraint('payment_key')
    )
    op.create_index(op.f('ix_payments_patient_id'), 'payments', ['patient_id'], unique=False)
    op.create_table('pharmacy_orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=False),
    sa.Column('pharmacy_ext_id', sa.String(length=20), nullable=False),
    sa.Column('pharmacy_name', sa.String(length=100), nullable=False),
    sa.Column('pharmacy_address', sa.String(length=200), nullable=False),
    sa.Column('pharmacy_tel', sa.String(length=20), nullable=True),
    sa.Column('pharmacy_lat', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('pharmacy_lng', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('receive_method', sa.String(length=10), nullable=False),
    sa.Column('delivery_reason', sa.String(length=20), nullable=True),
    sa.Column('delivery_address', sa.String(length=200), nullable=True),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('status_changed_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('appointment_id')
    )


def downgrade() -> None:
    # 외래 키가 쓰는 인덱스는 따로 지우지 않는다 (MySQL error 1553)
    op.drop_table('pharmacy_orders')
    op.drop_table('payments')
