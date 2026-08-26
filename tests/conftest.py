"""Shared fixtures for the Spendly test suite.

`app.py` builds its Flask object at import time — there is no app factory — so
these fixtures repoint `app.config["DATABASE"]` at a throwaway file rather than
constructing a fresh app. Every test gets its own `tmp_path`, so the real
`expense_tracker.db` at the repo root is never opened, read, or written.
"""

import pytest

from app import app as flask_app
from database import db


@pytest.fixture
def app(tmp_path):
    """The application, wired to an empty database seeded with demo data."""
    flask_app.config.update(
        TESTING=True,
        DATABASE=str(tmp_path / "test.db"),
        SECRET_KEY="test-only-key",
    )

    with flask_app.app_context():
        db.init_db()
        db.seed_db()

    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def demo(app):
    """The seeded demo user's id, email, and plaintext password.

    The id is looked up rather than assumed to be 1: `seed_db()` is a no-op
    when any user already exists, so the demo user is only row 1 on a database
    that was empty when it ran.
    """
    with app.app_context():
        row = db.get_db().execute(
            "SELECT id FROM users WHERE email = ?", (db.DEMO_USER["email"],)
        ).fetchone()

    return {
        "id": row["id"],
        "email": db.DEMO_USER["email"],
        "password": db.DEMO_USER["password"],
    }
