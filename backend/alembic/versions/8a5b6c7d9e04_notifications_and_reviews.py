"""notifications appointment link and reviews

Revision ID: 8a5b6c7d9e04
Revises: 7e4f5a6b8c93
Create Date: 2026-10-30 16:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8a5b6c7d9e04'
down_revision: Union[str, None] = '7e4f5a6b8c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('notifications', 'type', existing_type=sa.String(length=20), type_=sa.String(length=30),
                    existing_nullable=False)
    op.add_column('notifications', sa.Column('appointment_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_notifications_appointment', 'notifications', 'appointments', ['appointment_id'], ['id'],
                          ondelete='CASCADE')

    op.create_table('reviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('wants_revisit', sa.Boolean(), nullable=False),
    sa.Column('tag_kind', sa.Boolean(), nullable=False),
    sa.Column('tag_detailed', sa.Boolean(), nullable=False),
    sa.Column('tag_punctual', sa.Boolean(), nullable=False),
    sa.Column('body', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('appointment_id')
    )
    op.create_index(op.f('ix_reviews_doctor_id'), 'reviews', ['doctor_id'], unique=False)


def downgrade() -> None:
    # 외래 키가 쓰는 인덱스는 따로 지우지 않는다 (MySQL error 1553). 테이블·컬럼과 함께 지워진다
    op.drop_table('reviews')
    op.drop_constraint('fk_notifications_appointment', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'appointment_id')
    # 30자를 넘는 값은 없지만 20자보다 긴 type 이 있으면 줄일 수 없으므로 먼저 지운다
    op.execute("DELETE FROM notifications WHERE CHAR_LENGTH(type) > 20")
    op.alter_column('notifications', 'type', existing_type=sa.String(length=30), type_=sa.String(length=20),
                    existing_nullable=False)
