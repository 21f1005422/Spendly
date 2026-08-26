# Step 2 — Registration and Login POST

> **Status: derived, not authoritative.** No assignment text was supplied for
> this step. The requirements below were reverse-engineered from the finished
> UI and the legal pages (see Evidence). Correct this file against the real
> assignment text if it differs — the implementation follows what is written
> here.

## Goal

Make `/register` and `/login` accept POST, so an account can be created from
the UI and signed in to. This is the first step where a route reads
`request.form`.

**Already done.** The login half and the session wiring it implies landed
in `7cb39bc` — `/login` verifies with `check_password_hash`, sets
`session["user_id"]`, and `/logout` clears it. Step 2's remaining work is
**registration only**. This spec records the login contract anyway so the two
routes can be read side by side.

Not touched by this step: the expense list, `/profile`, any template, and the
schema. `base.html` still renders the signed-out navbar — see Known mismatch.

## Evidence

| Requirement | Source |
|---|---|
| Registration collects a name, an email, and a password | `templates/register.html:23,29,35` |
| The form POSTs to `/register` | `templates/register.html:20` |
| Field is `name`; the column is `username` | `templates/register.html:23` vs `database/db.py:26` |
| Account details are username + email + hashed password | `templates/privacy.html:23-24` |
| Passwords are never stored in plain text | `templates/privacy.html:47` |
| Failures render inline, above the form | `templates/register.html:16-18`, `static/css/style.css:413` |
| Email is unique, case-insensitively | `database/db.py:27` (`COLLATE NOCASE UNIQUE`) |
| Password minimum is 8 characters | `templates/register.html:36` (placeholder text only) |
| Account holders must be at least 13 | `templates/terms.html:21` |
| Login POSTs email + password, renders the same error block | `templates/login.html:20,23,29` |

## Decisions

Everything here is underdetermined by the evidence above.

- **Enforce the 8-character minimum server-side.** The only trace of the rule
  is placeholder text, and `required` in HTML is trivially bypassed. Cost: a
  rule invented from a placeholder now governs real accounts, and the two
  seeded dev users (`spendly-dev-1234`) happen to satisfy it while
  `seed_db()`'s `demo1234` sits exactly at the boundary.
- **Do not enforce the age-13 rule.** `terms.html:21` states it, but the form
  has no date-of-birth or checkbox field to collect it, and the schema has no
  column. Adding either means editing a template, which this repo forbids.
  Cost: a stated term goes unenforced; it is a click-through agreement only.
- **Register, then redirect to `/login`** rather than signing the new user in
  automatically. It keeps this step's session surface at zero and matches
  `register.html:43-45` pointing at Sign in. Cost: one extra step for the user.
- **Catch `sqlite3.IntegrityError` rather than pre-checking with a SELECT.**
  A `SELECT`-then-`INSERT` has a TOCTOU gap; the UNIQUE index is the real
  authority. Cost: the handler must distinguish which constraint fired if more
  are added later.
- **Registration errors name the specific problem** ("An account with that
  email already exists"), unlike login, which uses one message for every
  failure. Registration cannot hide whether an email is taken — the UNIQUE
  constraint reveals it either way — so a vague message would cost usability
  and buy no secrecy. Cost: `/register` is an email-enumeration oracle. That is
  inherent to unique-email signup, not a choice this spec introduces.
- **Strip surrounding whitespace from name and email; never from the
  password.** Trimming a password silently changes a credential.

## Route contract — `app.py`

| Route | Method | Behaviour |
|---|---|---|
| `/register` | GET | Render `register.html`, no error. |
| `/register` | POST | Read `name`, `email`, `password`. Validate. On success `INSERT INTO users (username, email, password_hash)` with `generate_password_hash`, commit, redirect to `/login`. On failure re-render `register.html` with `error=`, HTTP 200. |
| `/login` | GET | Render `login.html`, no error. |
| `/login` | POST | Look up by email, verify with `check_password_hash`, `session.clear()`, set `session["user_id"]`, redirect to `/profile`. One error message for both no-such-user and bad-password. |

### Validation order for `/register`

Check in this order and stop at the first failure, so the message names the
first thing wrong rather than the last:

1. Any of name, email, password empty after stripping → "All fields are required."
2. Password shorter than 8 characters → "Password must be at least 8 characters."
3. `IntegrityError` on insert → "An account with that email already exists."

The re-render must return 200, not a redirect — the error block is rendered
from a template variable, not a flash, so a redirect would lose it.

## Wiring — `app.py`

`@app.route("/register", methods=["GET", "POST"])`. The imports Step 2 needs
(`request`, `redirect`, `url_for`, `session`, `generate_password_hash`) are
mostly present already from the login work; `generate_password_hash` is not —
only `check_password_hash` is imported today.

Use `db.get_db()`, consistent with `/login`. No new helper, no blueprint.

## Known mismatch for Step 4

`templates/base.html:21-24` hard-codes the signed-out navbar — "Sign in" and
"Get started" render on every page, including for a user who has just logged
in. The `{% if session.user_id %}` branch is not part of Step 2. Until it
exists, a successful registration or login has no visible effect anywhere in
the chrome; `/profile` returning its Step 4 placeholder string is the only
confirmation.

`register.html` and `login.html` need no changes at all — both already POST and
both already render `{% if error %}`.

## Commands

```bash
source venv/bin/activate
python app.py                 # http://localhost:5001/register
```

Verify without a browser:

```python
from app import app
c = app.test_client()
c.post("/register", data={"name": "A", "email": "a@b.com", "password": "12345678"})
# -> 302 /login, then that email logs in
c.post("/register", data={"name": "A", "email": "A@B.COM", "password": "12345678"})
# -> 200, "already exists" (COLLATE NOCASE)
```

Existing accounts: `demo@spendly.app` / `demo1234` from `seed_db()`, plus any
user added by `/seed-user`.
