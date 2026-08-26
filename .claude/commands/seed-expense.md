---
description: Insert an expense into expense_tracker.db
argument-hint: <amount> <category> [date] [description] [--user <id|email>]
allowed-tools: Bash(sqlite3:*), Bash(venv/bin/python:*)
---

Insert one expense row into `expense_tracker.db` (repo root) for an existing
user.

Arguments: $ARGUMENTS — amount, category, then optional date and description.
Prompt for amount and category if missing rather than inventing them.

Defaults for the optional fields:

- `date` — today, ISO `YYYY-MM-DD`. Accept a bare day-of-month or a relative
  phrase ("3 days ago") and resolve it, but store ISO.
- `description` — empty string, which is the column default.
- user — the lowest `users.id` when `--user` is absent. If more than one user
  exists, say which one you picked. `--user` accepts an id or an email.

Constraints the insert must respect, all enforced by CHECKs that surface as
`sqlite3.IntegrityError`:

- `amount` must be `> 0` and is stored as REAL.
- `category` must be exactly one of `Food`, `Travel`, `Bills`, `Other` —
  case-sensitive. Map a lowercase or plural input onto the right one; refuse
  anything that is not one of the four instead of substituting `Other`.
- `user_id` must reference a real user. `PRAGMA foreign_keys = ON` is off by
  default per connection, so set it or the reference is not checked.

Steps:

1. Run `venv/bin/python -c` from the repo root. No need to start Flask.
2. `INSERT INTO expenses (user_id, amount, category, date, description)
   VALUES (?, ?, ?, ?, ?)`. Leave `created_at` to its default.
3. Echo `cursor.lastrowid` and commit.

Report the new expense's id, amount, category, date, and which user it landed
on, in one line. On `IntegrityError`, name the constraint that failed rather
than retrying with adjusted values.

To seed a user, use `/seed-user`. For the full demo dataset use
`flask init-db`, which calls `seed_db()` — note it no-ops once any user exists.
