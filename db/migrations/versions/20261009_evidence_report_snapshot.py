"""Save report provenance without changing legacy assessment records."""
from alembic import op
import sqlalchemy as sa

revision = "20261009_report"
down_revision = "6be36c86be19"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("patient_assessments"):
        # The original revision is a no-op; fresh installs historically create
        # tables at app startup. Create them here so migrations also work alone.
        from backend.cardio.models.patient_model import PatientAssessment, InferenceAudit
        PatientAssessment.__table__.create(bind, checkfirst=True)
        InferenceAudit.__table__.create(bind, checkfirst=True)
        return
    columns = {column["name"] for column in inspector.get_columns("patient_assessments")}
    if "assessment_uuid" not in columns:
        op.add_column("patient_assessments", sa.Column("assessment_uuid", sa.String(36), nullable=True))
    if "prediction_snapshot" not in columns:
        op.add_column("patient_assessments", sa.Column("prediction_snapshot", sa.JSON(), nullable=True))
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("patient_assessments")}
    if "ix_patient_assessments_assessment_uuid" not in indexes:
        op.create_index("ix_patient_assessments_assessment_uuid", "patient_assessments", ["assessment_uuid"], unique=True)


def downgrade():
    with op.batch_alter_table("patient_assessments") as batch:
        batch.drop_index("ix_patient_assessments_assessment_uuid")
        batch.drop_column("prediction_snapshot")
        batch.drop_column("assessment_uuid")
