---
description: Insert a user into expense_tracker.db
argument-hint: <name> <email> <password>
allowed-tools: Bash(sqlite3:*), Bash(venv/bin/python:*), Bash(source venv/bin/activate:*)
---

Insert one user into `expense_tracker.db` (repo root) so it can be logged in
with immediately.

Arguments: $ARGUMENTS — name, email, password, in that order. Prompt for any
that are missing rather than inventing values. A name with spaces may be
quoted; if the arguments are ambiguous, ask instead of guessing.

Steps:

1. Run `venv/bin/python -c` from the repo root — the venv has `werkzeug`,
   the system python does not. Do not start the Flask app for this.
2. Hash the password with `werkzeug.security.generate_password_hash`. Never
   write a plaintext password into the `password_hash` column.
3. `INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)`.
   The column is `username`, not `name`. Leave `created_at` to its default.
4. Echo `cursor.lastrowid` and commit.

Then report the new user's id and email in one line. If the insert raises
`sqlite3.IntegrityError`, say the email is already taken — `users.email` is
`UNIQUE COLLATE NOCASE`, so `Demo@Spendly.app` collides with
`demo@spendly.app` — and show the existing row's id rather than retrying.

Do not touch the `expenses` table; this command seeds a user with no expenses.
For the full demo dataset use `flask init-db`, which calls `seed_db()`.
