"""Always isolate suite persistence before application modules create their engine."""
import os
import tempfile

_database_directory = tempfile.TemporaryDirectory(prefix='cardiovision-pytest-')
os.environ['DATABASE_URL'] = f'sqlite:///{_database_directory.name}/test.db'
