# Step 1 — Database Setup

> **Status: derived, not authoritative.** This file was empty when Step 1 was
> implemented. The requirements below were reverse-engineered from the finished
> UI (see Evidence). Correct this file against the real assignment text if it
> differs — the implementation follows what is written here.

## Goal

Create the data layer every later step builds on: a SQLite connection helper,
the schema, and development seed data. No routes and no templates change in
this step.

## Evidence

| Requirement | Source |
|---|---|
| Users hold username, email, hashed password | `templates/privacy.html:23` |
| Expenses hold amount, category, date, description | `templates/privacy.html:25`, `templates/landing.html:84` |
| Deleting an account removes its expenses | `templates/privacy.html:52` |
| Passwords never stored in plaintext | `templates/privacy.html:47` |
| Category breakdowns, monthly summaries, date-range reports | `templates/privacy.html:37`, `templates/landing.html:89` |
| Categories: Food, Travel, Bills (+ a 4th) | `templates/landing.html:57-71`, `static/css/style.css:249` |
| Currency is INR | `templates/landing.html:41` |

## Decisions

- **Amount** is `REAL` rupees with `CHECK (amount > 0)`. Routes insert `250.50`
  directly; no unit conversion anywhere. Accepts binary-float rounding on sums.
- **Category** is `TEXT` with a `CHECK (category IN (...))` over the four
  categories. SQLite cannot alter a CHECK in place, so changing the list means
  rebuilding the table.
- **Date** is ISO `TEXT` (`YYYY-MM-DD`). SQLite has no date type; ISO text makes
  range filters plain string comparison and lets `strftime('%Y-%m', date)`
  drive monthly summaries.

## Schema

```sql
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
```

`COLLATE NOCASE` on `email` makes the implicit UNIQUE index case-insensitive.
Both indexes lead with `user_id` because every query is scoped to the signed-in
user.

## API contract — `database/db.py`

| Function | Behaviour |
|---|---|
| `get_db()` | Request-scoped connection cached on `g`. Sets `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. Reads the path from `current_app.config["DATABASE"]`. Requires an app context. |
| `close_db(e=None)` | Pops and closes the connection. Registered as a teardown handler. |
| `init_db()` | `executescript(SCHEMA)`. Idempotent. |
| `seed_db()` | Inserts one demo user and 12 expenses across all four categories and the current + previous month. No-op when a user exists. Returns rows inserted. |
| `init_app(app)` | Registers the teardown handler and the `init-db` CLI command. |

`db.py` must not import `app.py`; `init_app(app)` inverts that dependency.

The `PRAGMA` is load-bearing: SQLite ignores `REFERENCES` unless foreign keys
are enabled **per connection**, so the account-deletion cascade silently fails
without it.

## Wiring — `app.py`

`app.config["DATABASE"]` (repo-root `expense_tracker.db`, already gitignored),
`app.config["SECRET_KEY"]` (for sessions in Step 3), and `db.init_app(app)`.

## Known mismatch for Step 2

`templates/register.html:26` posts a form field named `name`, which maps to the
`username` column. The template is the fixed interface — map it in the route,
do not rename the field.

## Commands

```bash
flask --app app init-db     # create tables + seed; safe to re-run
```

Demo credentials: `demo@spendly.app` / `demo1234`.
