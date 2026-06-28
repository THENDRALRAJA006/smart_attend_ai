"""
SmartAttend AI — Master Embedding Migration
Revision: 003

Migrates from multi-row FaceEmbedding gallery to single master embedding
stored directly on the students table using pgvector.

Steps:
  1. Enable pgvector extension
  2. Add biometric columns to students table
  3. Migrate existing face_embeddings → master embedding (data preservation)
  4. Drop face_embeddings table
  5. Create HNSW index for cosine similarity search
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "003_master_embedding"
down_revision = "002_seed_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Enable pgvector extension ─────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── 2. Add biometric columns to students table ───────────────────────────
    # Using raw SQL because pgvector's vector type isn't a standard SA type
    op.execute(
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS "
        "master_embedding vector(512)"
    )
    op.add_column(
        "students",
        sa.Column("embedding_version", sa.String(20), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("embedding_quality_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("embedding_updated_at", sa.DateTime(), nullable=True),
    )

    # ── 3. Data migration: average existing embeddings into master ────────────
    # For each student who has face_embeddings, compute the average embedding
    # and store it as the master_embedding. This preserves existing registrations.
    conn = op.get_bind()

    # Check if face_embeddings table exists before attempting migration
    result = conn.execute(text(
        "SELECT EXISTS ("
        "  SELECT FROM information_schema.tables "
        "  WHERE table_name = 'face_embeddings'"
        ")"
    ))
    table_exists = result.scalar()

    if table_exists:
        # Get all students with embeddings
        students_with_embeddings = conn.execute(text(
            "SELECT DISTINCT student_id FROM face_embeddings"
        )).fetchall()

        for (student_id,) in students_with_embeddings:
            # Fetch all embeddings for this student
            rows = conn.execute(text(
                "SELECT embedding_json FROM face_embeddings "
                "WHERE student_id = :sid"
            ), {"sid": student_id}).fetchall()

            if not rows:
                continue

            # Parse JSON embeddings and compute average
            import json
            import numpy as np

            embeddings = []
            for (emb_json,) in rows:
                try:
                    emb = json.loads(emb_json)
                    if isinstance(emb, list) and len(emb) == 512:
                        embeddings.append(np.array(emb, dtype=np.float32))
                except (json.JSONDecodeError, TypeError):
                    continue

            if not embeddings:
                continue

            # Compute L2-normalised mean embedding
            stacked = np.array(embeddings, dtype=np.float32)
            mean_emb = stacked.mean(axis=0)
            norm = np.linalg.norm(mean_emb)
            if norm > 0:
                mean_emb = mean_emb / norm

            # Format as pgvector literal: '[0.1,0.2,...,0.5]'
            vector_str = "[" + ",".join(f"{v:.8f}" for v in mean_emb) + "]"

            # Update the student record
            conn.execute(text(
                "UPDATE students SET "
                "  master_embedding = :emb::vector, "
                "  embedding_version = 'migrated_v1', "
                "  embedding_quality_score = 0.90, "
                "  embedding_updated_at = NOW(), "
                "  is_face_registered = true "
                "WHERE id = :sid"
            ), {"emb": vector_str, "sid": student_id})

        # ── 4. Drop face_embeddings table ────────────────────────────────────
        op.drop_index("idx_face_embedding_student", table_name="face_embeddings")
        op.drop_table("face_embeddings")

    # ── 5. Create HNSW index for cosine similarity search ────────────────────
    # This index enables sub-millisecond approximate nearest neighbor search
    # at scale (100K–1M+ students). Uses cosine distance operator class.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_student_embedding_hnsw "
        "ON students USING hnsw (master_embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    # Drop the HNSW index
    op.execute("DROP INDEX IF EXISTS idx_student_embedding_hnsw")

    # Recreate face_embeddings table
    op.create_table(
        "face_embeddings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("pose_name", sa.String(50), nullable=True),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(),
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_face_embedding_student", "face_embeddings", ["student_id"]
    )

    # Remove biometric columns from students
    op.drop_column("students", "embedding_updated_at")
    op.drop_column("students", "embedding_quality_score")
    op.drop_column("students", "embedding_version")
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS master_embedding")
