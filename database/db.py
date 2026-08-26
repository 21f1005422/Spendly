"""SQLite data layer for Spendly.

Public API (see Step 1 spec in .claude/specs/01-database-setup.md):
    get_db()   — returns a SQLite connection with row_factory and foreign keys enabled
    init_db()  — creates all tables using CREATE TABLE IF NOT EXISTS
    seed_db()  — inserts sample data for development

This module must not import app.py — init_app(app) inverts that dependency.
"""

import sqlite3
from datetime import date, timedelta

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

# The four categories the landing page charts. Mirrored by a CHECK constraint
# on expenses.category, so adding one here means rebuilding that table.
CATEGORIES = ("Food", "Travel", "Bills", "Other")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL,
    email         TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount      REAL    NOT NULL CHECK (amount > 0),
    category    TEXT    NOT NULL CHECK (category IN ('Food','Travel','Bills','Other')),
    date        TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date     ON expenses(user_id, date);
CREATE INDEX IF NOT EXISTS idx_expenses_user_category ON expenses(user_id, category);
"""


# ------------------------------------------------------------------ #
# Connection handling                                                 #
# ------------------------------------------------------------------ #

def get_db():
    """Return the request-scoped SQLite connection, opening it if needed.

    Requires an application context. Rows come back as sqlite3.Row so callers
    can use expense["amount"] in Python and in Jinja templates.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        # SQLite ignores REFERENCES clauses unless this is set, per connection.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the request-scoped connection. Registered as a teardown handler."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ------------------------------------------------------------------ #
# Schema and seed data                                                #
# ------------------------------------------------------------------ #

def init_db():
    """Create every table and index. Safe to run repeatedly."""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


DEMO_USER = {
    "username": "Yash Agarwal",
    "email": "demo@spendly.app",
    "password": "demo1234",
}

# (months_back, day_of_month, amount, category, description)
# Days stay <= 28 so every entry is valid in any month.
SEED_EXPENSES = [
    (0, 2, 1450.00, "Bills", "Electricity bill"),
    (0, 4, 320.50, "Food", "Groceries - vegetables and milk"),
    (0, 7, 899.00, "Travel", "Monthly metro pass"),
    (0, 11, 240.00, "Food", "Lunch with the team"),
    (0, 15, 1299.00, "Bills", "Broadband renewal"),
    (0, 18, 560.75, "Other", "Birthday gift"),
    (0, 22, 180.00, "Travel", "Auto to the station"),
    (1, 3, 1450.00, "Bills", "Electricity bill"),
    (1, 9, 2100.00, "Food", "Month's groceries"),
    (1, 14, 3400.00, "Travel", "Weekend trip - train tickets"),
    (1, 20, 450.00, "Other", "Stationery and printing"),
    (1, 26, 275.25, "Food", "Coffee and snacks"),
]


def _seed_date(months_back, day):
    """Return an ISO date `months_back` months before the current month."""
    anchor = date.today().replace(day=1)
    for _ in range(months_back):
        anchor = (anchor - timedelta(days=1)).replace(day=1)
    return anchor.replace(day=day).isoformat()


def seed_db():
    """Insert sample data for development.

    No-op when a user already exists, so running init-db twice does not
    duplicate rows. Returns the number of expenses inserted.
    """
    db = get_db()
    if db.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None:
        return 0

    cursor = db.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (
            DEMO_USER["username"],
            DEMO_USER["email"],
            generate_password_hash(DEMO_USER["password"]),
        ),
    )
    user_id = cursor.lastrowid

    db.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, amount, category, _seed_date(months_back, day), description)
            for months_back, day, amount, category, description in SEED_EXPENSES
        ],
    )
    db.commit()
    return len(SEED_EXPENSES)


# ------------------------------------------------------------------ #
# Flask integration                                                   #
# ------------------------------------------------------------------ #

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the tables and insert sample data."""
    init_db()
    click.echo(f"Initialized database at {current_app.config['DATABASE']}")

    inserted = seed_db()
    if inserted:
        click.echo(f"Seeded 1 demo user and {inserted} expenses.")
    else:
        click.echo("Seed data already present - skipped.")


def init_app(app):
    """Register the teardown handler and the `flask init-db` command."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
