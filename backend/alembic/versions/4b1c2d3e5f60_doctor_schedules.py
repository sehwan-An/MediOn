"""doctor schedules

Revision ID: 4b1c2d3e5f60
Revises: 8d3091b2b274
Create Date: 2026-10-30 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4b1c2d3e5f60'
down_revision: Union[str, None] = '8d3091b2b274'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('doctor_schedules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('weekday', sa.SmallInteger(), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('lunch_start', sa.Time(), nullable=True),
    sa.Column('lunch_end', sa.Time(), nullable=True),
    sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('doctor_id', 'weekday', name='uq_doctor_schedules_doctor_weekday')
    )


def downgrade() -> None:
    # 외래 키 인덱스는 따로 지우지 않는다 (MySQL error 1553). 테이블과 함께 지워진다.
    op.drop_table('doctor_schedules')
