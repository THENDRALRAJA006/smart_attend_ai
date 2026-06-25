"""
SmartAttend AI — Seed Data Migration
Revision: 002
Seeds: default admin, sample classroom, sample BLE beacon, sample subjects, sample faculty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime
import bcrypt

revision = "002_seed_data"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'

    # ── Default Admin ─────────────────────────────────────────────────────────
    if is_postgres:
        admin_sql = (
            "INSERT INTO admins (email, password_hash, name) VALUES "
            "(:email, :pw, :name) ON CONFLICT (email) DO NOTHING"
        )
    else:
        admin_sql = (
            "INSERT IGNORE INTO admins (email, password_hash, name) VALUES "
            "(:email, :pw, :name)"
        )
    bind.execute(
        sa.text(admin_sql),
        {
            "email": "admin@smartattend.ai",
            "pw": _hash("Admin@2026"),
            "name": "System Administrator",
        },
    )

    # ── Sample Classrooms ─────────────────────────────────────────────────────
    for room_name, building, cap in [
        ("ROOM101", "Main Block", 60),
        ("ROOM102", "Main Block", 60),
        ("ROOM201", "Science Block", 45),
        ("LAB301",  "Lab Block",   30),
    ]:
        if is_postgres:
            classroom_sql = (
                "INSERT INTO classrooms (room_name, building, capacity) "
                "VALUES (:rn, :b, :c) ON CONFLICT (room_name) DO NOTHING"
            )
        else:
            classroom_sql = (
                "INSERT IGNORE INTO classrooms (room_name, building, capacity) "
                "VALUES (:rn, :b, :c)"
            )
        bind.execute(
            sa.text(classroom_sql),
            {"rn": room_name, "b": building, "c": cap},
        )

    # Fetch ROOM101 id
    row = bind.execute(
        sa.text("SELECT id FROM classrooms WHERE room_name = 'ROOM101' LIMIT 1")
    ).fetchone()
    room101_id = row[0] if row else 1

    # ── Sample BLE Beacon for ROOM101 ─────────────────────────────────────────
    if is_postgres:
        beacon_sql = (
            "INSERT INTO ble_beacons (classroom_id, uuid, device_name, rssi_threshold, is_active) "
            "VALUES (:cid, :uuid, :dn, :rssi, :is_active) ON CONFLICT (uuid) DO NOTHING"
        )
    else:
        beacon_sql = (
            "INSERT IGNORE INTO ble_beacons (classroom_id, uuid, device_name, rssi_threshold, is_active) "
            "VALUES (:cid, :uuid, :dn, :rssi, :is_active)"
        )
    bind.execute(
        sa.text(beacon_sql),
        {
            "cid": room101_id,
            "uuid": "SMARTATTEND-ROOM101-ESP32-001",
            "dn": "SMARTATTEND_ROOM101",
            "rssi": -70,
            "is_active": True,
        },
    )

    # ── Sample Subjects ───────────────────────────────────────────────────────
    subjects = [
        ("Data Structures", "CS201", "Computer Science", 2),
        ("Database Systems", "CS301", "Computer Science", 3),
        ("Machine Learning", "CS401", "Computer Science", 4),
        ("Operating Systems", "CS302", "Computer Science", 3),
        ("Computer Networks", "CS303", "Computer Science", 3),
    ]
    for subject_name, code, dept, year in subjects:
        if is_postgres:
            subject_sql = (
                "INSERT INTO subjects (subject_name, subject_code, department, year) "
                "VALUES (:sn, :sc, :dept, :yr) ON CONFLICT (subject_code) DO NOTHING"
            )
        else:
            subject_sql = (
                "INSERT IGNORE INTO subjects (subject_name, subject_code, department, year) "
                "VALUES (:sn, :sc, :dept, :yr)"
            )
        bind.execute(
            sa.text(subject_sql),
            {"sn": subject_name, "sc": code, "dept": dept, "yr": year},
        )

    # ── Sample Faculty ────────────────────────────────────────────────────────
    if is_postgres:
        faculty_sql = (
            "INSERT INTO faculty (name, email, password_hash, department) "
            "VALUES (:name, :email, :pw, :dept) ON CONFLICT (email) DO NOTHING"
        )
    else:
        faculty_sql = (
            "INSERT IGNORE INTO faculty (name, email, password_hash, department) "
            "VALUES (:name, :email, :pw, :dept)"
        )
    bind.execute(
        sa.text(faculty_sql),
        {
            "name": "Dr. Sample Faculty",
            "email": "faculty@smartattend.ai",
            "pw": _hash("Faculty@123"),
            "dept": "Computer Science",
        },
    )

    print("[Seed] [OK] SmartAttend AI seed data inserted successfully.")


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM ble_beacons WHERE uuid = 'SMARTATTEND-ROOM101-ESP32-001'"))
    bind.execute(sa.text("DELETE FROM classrooms WHERE room_name IN ('ROOM101','ROOM102','ROOM201','LAB301')"))
    bind.execute(sa.text("DELETE FROM admins WHERE email = 'admin@smartattend.ai'"))
    bind.execute(sa.text("DELETE FROM faculty WHERE email = 'faculty@smartattend.ai'"))
    bind.execute(sa.text("DELETE FROM subjects WHERE subject_code IN ('CS201','CS301','CS401','CS302','CS303')"))
