"""
SmartAttend AI — Initial Schema Migration
Revision: 001
Creates all tables for MySQL 8.0 / AWS RDS.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── students ──────────────────────────────────────────────────────────────
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("roll_no", sa.String(20), nullable=False),
        sa.Column("department", sa.String(50), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(10), nullable=True),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_face_registered", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("roll_no"),
        sa.UniqueConstraint("email"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── faculty ───────────────────────────────────────────────────────────────
    op.create_table(
        "faculty",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("department", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── admins ────────────────────────────────────────────────────────────────
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── subjects ──────────────────────────────────────────────────────────────
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_name", sa.String(100), nullable=True),
        sa.Column("subject_code", sa.String(20), nullable=True),
        sa.Column("department", sa.String(50), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── classrooms ────────────────────────────────────────────────────────────
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_name", sa.String(50), nullable=False),
        sa.Column("building", sa.String(50), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_name"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── ble_beacons ───────────────────────────────────────────────────────────
    op.create_table(
        "ble_beacons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(100), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=True),
        sa.Column("rssi_threshold", sa.Integer(), server_default=sa.text("-70")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── attendance_sessions ───────────────────────────────────────────────────
    op.create_table(
        "attendance_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("faculty_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("classroom_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("start_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("qr_token", sa.String(255), nullable=True),
        sa.Column("qr_expires_at", sa.DateTime(), nullable=True),
        # Legacy fields for backwards compatibility
        sa.Column("subject_name", sa.String(100), nullable=True),
        sa.Column("classroom", sa.String(50), nullable=True),
        sa.Column("session_code", sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── face_embeddings ───────────────────────────────────────────────────────
    # embedding_json is LONGTEXT to hold 512 floats as JSON array
    op.create_table(
        "face_embeddings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("pose_name", sa.String(50), nullable=True),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_face_embedding_student", "face_embeddings", ["student_id"])

    # ── attendance ─────────────────────────────────────────────────────────────
    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column(
            "attendance_status",
            sa.Enum("present", "manual_review", "rejected", name="attendance_status_enum"),
            server_default="present",
        ),
        sa.Column("liveness_verified", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("marked_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["attendance_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "session_id", name="no_duplicate_attendance"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # ── liveness_tokens ───────────────────────────────────────────────────────
    op.create_table(
        "liveness_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column(
            "challenge",
            sa.Enum("blink", "smile", "turn_left", "turn_right", name="liveness_challenge_enum"),
            nullable=False,
        ),
        sa.Column("is_used", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("liveness_tokens")
    op.drop_table("attendance")
    op.drop_index("idx_face_embedding_student", "face_embeddings")
    op.drop_table("face_embeddings")
    op.drop_table("attendance_sessions")
    op.drop_table("ble_beacons")
    op.drop_table("classrooms")
    op.drop_table("subjects")
    op.drop_table("admins")
    op.drop_table("faculty")
    op.drop_table("students")
