import os

# Must be set before the app is imported: tests use a throwaway in-memory SQLite database,
# so `make test` needs no running PostgreSQL.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # Entering the context runs the lifespan: tables are created and seed is loaded.
    with TestClient(app) as c:
        yield c
