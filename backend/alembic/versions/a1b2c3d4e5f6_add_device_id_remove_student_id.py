"""add device_id, remove student_id

Revision ID: a1b2c3d4e5f6
Revises: 55ad7b32f8c2
Create Date: 2026-04-22 22:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '55ad7b32f8c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # conversations: add device_id, drop student_id FK
    op.add_column('conversations', sa.Column('device_id', sa.String(36), nullable=True))
    op.drop_constraint('conversations_student_id_fkey', 'conversations', type_='foreignkey')
    op.drop_column('conversations', 'student_id')
    op.alter_column('conversations', 'device_id', nullable=False)
    op.create_index('ix_conversations_device_id', 'conversations', ['device_id'])

    # saved_plans: add device_id, drop student_id FK
    op.add_column('saved_plans', sa.Column('device_id', sa.String(36), nullable=True))
    op.drop_constraint('saved_plans_student_id_fkey', 'saved_plans', type_='foreignkey')
    op.drop_column('saved_plans', 'student_id')
    op.alter_column('saved_plans', 'device_id', nullable=False)
    op.create_index('ix_saved_plans_device_id', 'saved_plans', ['device_id'])

    # audit_logs: add device_id, drop student_id FK
    op.add_column('audit_logs', sa.Column('device_id', sa.String(36), nullable=True))
    op.drop_constraint('audit_logs_student_id_fkey', 'audit_logs', type_='foreignkey')
    op.drop_column('audit_logs', 'student_id')
    op.create_index('ix_audit_logs_device_id', 'audit_logs', ['device_id'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_device_id', table_name='audit_logs')
    op.add_column('audit_logs', sa.Column('student_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('audit_logs_student_id_fkey', 'audit_logs', 'students', ['student_id'], ['id'])
    op.drop_column('audit_logs', 'device_id')

    op.drop_index('ix_saved_plans_device_id', table_name='saved_plans')
    op.add_column('saved_plans', sa.Column('student_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('saved_plans_student_id_fkey', 'saved_plans', 'students', ['student_id'], ['id'])
    op.drop_column('saved_plans', 'device_id')

    op.drop_index('ix_conversations_device_id', table_name='conversations')
    op.add_column('conversations', sa.Column('student_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('conversations_student_id_fkey', 'conversations', 'students', ['student_id'], ['id'])
    op.drop_column('conversations', 'device_id')
