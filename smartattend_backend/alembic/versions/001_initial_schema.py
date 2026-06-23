"""initial_schema

Revision ID: 001
Revises: None
Create Date: 2026-06-23 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Students Table
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('roll_number', sa.String(length=50), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('face_embeddings', sa.JSON(), nullable=True),  # Native PostgreSQL JSON column
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('roll_number')
    )

    # 2. Faculty Table
    op.create_table(
        'faculty',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('employee_id')
    )

    # 3. Sessions Table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('faculty_id', sa.Integer(), nullable=False),
        sa.Column('subject_name', sa.String(length=100), nullable=False),
        sa.Column('classroom', sa.String(length=50), nullable=False),
        sa.Column('session_code', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculty.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_code')
    )

    # 4. Attendance Table
    op.create_table(
        'attendance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='present'),
        sa.Column('verification_method', sa.String(length=50), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'session_id', name='uq_student_session')
    )

    # 5. Liveness Tokens Table
    op.create_table(
        'liveness_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('challenge', sa.String(length=50), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )

    # 6. Classrooms Table
    op.create_table(
        'classrooms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('room_name', sa.String(length=50), nullable=False),
        sa.Column('building', sa.String(length=50), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_name')
    )

    # 7. BLE Beacons Table
    op.create_table(
        'ble_beacons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=100), nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=True),
        sa.Column('rssi_threshold', sa.Integer(), nullable=False, server_default='-70'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )

def downgrade() -> None:
    op.drop_table('ble_beacons')
    op.drop_table('classrooms')
    op.drop_table('liveness_tokens')
    op.drop_table('attendance')
    op.drop_table('sessions')
    op.drop_table('faculty')
    op.drop_table('students')

