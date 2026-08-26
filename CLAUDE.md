# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**Spendly** — a Flask expense tracker built as a *teaching scaffold*. The UI (landing, auth pages, legal pages, CSS) is complete; the application logic is deliberately unimplemented and is meant to be filled in step by step. Placeholder routes in `app.py` name the step that implements them:

| Step | Deliverable |
|------|-------------|
| 1 | `database/db.py` — `get_db()`, `init_db()`, `seed_db()` |
| 3 | `/logout` |
| 4 | `/profile` |
| 7 | `/expenses/add` |
| 8 | `/expenses/<id>/edit` |
| 9 | `/expenses/<id>/delete` |

Steps 2, 5, 6 are unnamed in the code — registration/login POST handling, session wiring, and the expense list are the gaps. When implementing a step, replace the placeholder `return` string; don't add parallel routes.

## Commands

```bash
source venv/bin/activate          # Python 3.13; venv/ exists in the working tree and is gitignored
pip install -r requirements.txt
python app.py                     # dev server, debug=True, http://localhost:5001
```

Port is **5001**, not Flask's default 5000 (macOS AirPlay squats on 5000).

`pytest` and `pytest-flask` are installed but **no tests exist yet**. Once a `tests/` directory exists:

```bash
pytest                            # all
pytest tests/test_db.py           # one file
pytest tests/test_db.py::test_init_db -v   # one test
```

There is no linter or formatter configured.

## Architecture

Three pieces, no framework beyond Flask itself:

- **`app.py`** — the entire application: one module, no blueprints, no app factory, no config object. All routes live here.
- **`database/`** — a package holding raw `sqlite3` access. **There is no ORM** — no SQLAlchemy in `requirements.txt`, and none is intended. `database/db.py` is a stub whose comment block is the contract: `get_db()` returns a connection with `row_factory` set and foreign keys enabled (`PRAGMA foreign_keys = ON`, which SQLite defaults *off* per-connection), `init_db()` creates tables with `CREATE TABLE IF NOT EXISTS`, `seed_db()` inserts dev data.
- **`templates/` + `static/`** — Jinja2 with a single `base.html` all pages extend.

The database file is `expense_tracker.db` at the repo root — that exact name is already in `.gitignore`, so keep it.

### Templates are ahead of the routes

This is the most common trap. `register.html` and `login.html` **already** POST to `/register` and `/login` and already render `{% if error %}<div class="auth-error">{{ error }}</div>{% endif %}`. The corresponding routes in `app.py` are GET-only and ignore the form.

So implementing auth means changing `app.py` — add `methods=["GET", "POST"]`, read `request.form`, and re-render the same template with an `error=` kwarg on failure. Do **not** rewrite the templates to match a new design; the form field names (`name`, `email`, `password`) are the interface.

Likewise, `base.html`'s navbar is hard-coded to the signed-out state (Sign in / Get started). Adding sessions means adding a `{% if session.user_id %}` branch there, which changes every page at once.

### Template conventions

`base.html` defines four blocks: `title`, `head`, `content`, `scripts`.

- **Page-specific CSS** goes through `{% block head %}` — `landing.html` is the model: it links `static/css/landing.css`, which *overrides* rules already in `style.css` rather than replacing them. `style.css` loads globally for every page.
- **Page-specific JS** goes inline in `{% block scripts %}` (see the video modal in `landing.html`). `static/js/main.js` is a shared stub loaded on every page and is currently empty.

### Styling

`static/css/style.css` opens with a `:root` block of design tokens — `--ink*`, `--paper*`, `--accent`, `--danger`, `--border*`, `--radius-*`, `--font-display` / `--font-body`. Use these variables; don't hardcode colors or radii. Fonts (DM Serif Display, DM Sans) are pulled from Google Fonts in `base.html`.

Both CSS files are organized into banner-comment sections (`/* --- Navbar --- */`, `/* --- Auth pages --- */`, …). Add new rules to the matching section rather than appending to the end of the file.
