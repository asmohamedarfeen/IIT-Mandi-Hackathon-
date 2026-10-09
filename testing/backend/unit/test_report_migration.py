import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def test_report_migration_supports_fresh_and_legacy_databases(tmp_path):
    root = Path(__file__).resolve().parents[3]
    for legacy in (False, True):
        database = tmp_path / ("legacy.db" if legacy else "fresh.db")
        if legacy:
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE patient_assessments (id INTEGER PRIMARY KEY, patient_id TEXT)")
                connection.execute("INSERT INTO patient_assessments VALUES (1, 'preserved')")
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=root,
            env={**os.environ, "DATABASE_URL": f"sqlite:///{database}"}, check=True, capture_output=True,
        )
        with sqlite3.connect(database) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(patient_assessments)")}
            assert {"assessment_uuid", "prediction_snapshot"} <= columns
            assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "20261009_report"
            if legacy:
                assert connection.execute("SELECT patient_id FROM patient_assessments WHERE id=1").fetchone()[0] == "preserved"
