# Step 3 — Login, Logout, and the Session

> **Status: derived, not authoritative.** No assignment text was supplied for
> this step, and unlike Steps 1 and 2 the UI says almost nothing about it —
> see the note under Evidence. Most of this file is decisions, not
> requirements. Correct it against the real assignment text if it differs.

## Goal

Establish the signed-in session: `/login` exchanges credentials for
`session["user_id"]`, `/logout` discards it. This is the state every later
step reads to scope data to one user.

**Already done.** Both routes landed in `7cb39bc` on `main` — `/login`
verifies with `check_password_hash` and sets the session (`app.py:46-47`),
`/logout` clears it (`app.py:68-70`). `SECRET_KEY` was configured back in
Step 1 (`app.py:12`). This spec records what was built and, more usefully,
what was decided without evidence.

Not touched: the expense list, `/profile`, the schema, any template.

## Evidence

**The UI is nearly silent on this step.** A search of `templates/` for
`logout`, `sign out`, `session`, and `cookie` returns **no matches**. Steps 1
and 2 could be reverse-engineered from `privacy.html` and the auth forms;
Step 3 cannot. What little exists:

| Requirement | Source |
|---|---|
| A session exists and authenticates the user across requests | `templates/privacy.html:36` |
| Data is scoped per user; reaching another user's data is prohibited | `templates/terms.html:33` |
| Credentials are the user's to keep confidential | `templates/terms.html:28` |
| The navbar has a signed-out state | `templates/base.html:22` |
| A signing key is already configured | `app.py:12` |

Everything below the line — how logout is reached, which HTTP method it uses,
how long a session lasts, what the cookie flags are — has **no source in the
repo**. It is decided here.

## Decisions

- **`session.clear()`, not `session.pop("user_id")`.** Clearing discards
  everything, so a later step that stashes something else in the session
  cannot leak it across a logout. Cost: nothing survives logout, so a
  "remember this filter" feature would have to live elsewhere.
- **Logout is `GET`.** It is a plain link, matching every other nav item, and
  no form or CSRF machinery exists anywhere in this app. Cost is real: a `GET`
  logout can be triggered by anything that fetches URLs — a prefetching
  browser, a link scanner, an `<img src>` on a hostile page — so a user can be
  logged out without acting. The damage is bounded (annoyance, not data loss),
  which is why it is acceptable here and would not be in a production app.
  Making it `POST` would mean adding a form to `base.html`, and the template is
  the fixed interface.
- **Logout redirects to the landing page**, not back to `/login`. Signing out
  and being shown a sign-in form reads as a failed logout.
- **`session.clear()` runs *before* `session["user_id"]` is set on login**
  (`app.py:46-47`), not after. This is session fixation defence: a pre-existing
  session id is discarded rather than inherited by the newly authenticated
  user.
- **One error message for every login failure** — unknown email and wrong
  password are indistinguishable, so `/login` cannot be used to enumerate
  registered addresses. This is deliberately the opposite of what `/register`
  will need: registration has to tell the user an email is already taken, or
  it cannot explain why the signup failed. That tension is Step 2's to resolve
  and is **not yet resolved in code** — `/register` is still the GET-only
  placeholder at `app.py:26-28`, ignoring its form. It is resolved on paper:
  `.claude/plans/02-registration.md` specifies "An account with that email
  already exists." on `sqlite3.IntegrityError`. There is no matching
  `.claude/specs/02-registration.md`; the plan is the only record.
- **Flask's default cookie session**, with no cookie configuration of our own.
  Worth being precise about what that inherits, because the defaults are not
  uniformly bad: `SESSION_COOKIE_HTTPONLY` defaults to `True`, so the cookie
  already is unreadable from JavaScript. What is actually missing is
  `SESSION_COOKIE_SECURE` (defaults `False` — the cookie travels over plain
  HTTP) and `SESSION_COOKIE_SAMESITE` (unset). `session.permanent` stays
  `False`, so `PERMANENT_SESSION_LIFETIME` never applies and the session dies
  with the browser. Acceptable on `localhost:5001`; the two missing flags must
  be set before this is served over a network.
- **The signed-out navbar stays hard-coded in this step.** Adding the
  `{% if session.user_id %}` branch is Step 5. Cost is severe for usability —
  see Known mismatch.

## Route contract — `app.py`

| Route | Method | Behaviour |
|---|---|---|
| `/login` | GET | Render `login.html`, no error. |
| `/login` | POST | Look up by email (`COLLATE NOCASE`), verify with `check_password_hash`. On success `session.clear()` then `session["user_id"] = user["id"]`, redirect to `/` (**temporary** — see below). On failure re-render at HTTP 200 with `error="Invalid email or password."` — the same message for both causes. |
| `/logout` | GET | `session.clear()`, redirect to `/`. Succeeds whether or not anyone was signed in; visiting it while signed out is a no-op redirect, not an error. |

`session["user_id"]` is an `INTEGER` — `users.id`. It is the only key this step
writes. Later steps read it to scope queries; nothing else should be trusted
from the client.

## Wiring — `app.py`

`session`, `redirect`, and `url_for` come from `flask`; `check_password_hash`
from `werkzeug.security`. All are imported already.

`app.config["SECRET_KEY"]` (`app.py:12`) is what makes the session cookie
tamper-evident — Flask signs it, so a user can read their cookie but cannot
forge `user_id`. **The dev fallback `"dev-only-change-me"` is a published
value**: anyone who knows it can mint a cookie for any `user_id`. It is fine
for local work and must be a real secret from the environment anywhere else.

No template changes in this step.

## Known mismatch for Step 4

**`/login` redirects to `/`, and this is deliberately temporary.** It
originally redirected to `/profile`, but `/profile` is still the placeholder
string at `app.py:73-75`, so signing in dumped the user on a bare
`Profile page — coming in Step 4`. Landing on the real landing page is the
better interim experience. **Step 4 must point `app.py:48` back at
`url_for("profile")`**; the comment there and
`tests/test_auth.py::test_valid_credentials_start_a_session` both say so.

The cost until then: **a successful login has no visible effect whatsoever.**
`base.html:21-24` still renders the signed-out navbar, so `/` after signing in
is pixel-identical to `/` before. The placeholder string was ugly but it was
proof; nothing replaces it until Step 5 adds the `{% if session.user_id %}`
branch. The session is set — `pytest` confirms it — it just cannot be seen.

`/profile` is also unguarded: it renders for a signed-out visitor exactly as it
does for a signed-in one, because nothing reads `session["user_id"]` yet. Step 4
is where that check first has to exist.

### Looking further ahead — Step 5

**There is no way to log out from the UI.** No template links to `/logout` —
the route exists and can only be reached by typing the URL. `base.html:21-24`
hard-codes "Sign in" and "Get started" for every visitor, signed in or not, and
a grep of `templates/` for `logout`, `sign out`, `session`, and `cookie`
returns no matches.

Two things must land together in Step 5 (session wiring) for this to be usable:
the `{% if session.user_id %}` branch in `base.html`, and a logout link inside
it.

One trap for whoever writes that branch: `static/css/style.css:599` hides
`.nav-links a:not(.nav-cta)` below 600px. A logout link added as a plain nav
anchor **disappears on mobile**. It needs `.nav-cta`, or a new rule in the
Navbar section of `style.css`.

## Commands

```bash
source venv/bin/activate
python app.py                 # http://localhost:5001/login
```

Verify without a browser:

```bash
pytest tests/test_auth.py -v
```

Ten tests cover this contract: the form renders, valid credentials 302 to
`/profile` with `session["user_id"]` set, a stale session is discarded on
sign-in, wrong-password and unknown-email both return 200 with the *same*
message, email matching is case-insensitive, and `/logout` clears the session
whether or not one existed.

`tests/conftest.py` repoints `app.config["DATABASE"]` at a per-test `tmp_path`,
so the suite never touches the real `expense_tracker.db`. It looks the demo
user's id up rather than assuming `1`: `seed_db()` no-ops when any user already
exists (`database/db.py:125-126`), so the demo row is only id 1 on a database
that was empty when it ran.

Logging out is only reachable at `http://localhost:5001/logout` directly.
Credentials: `demo@spendly.app` / `demo1234`, plus any user from `/seed-user`.
