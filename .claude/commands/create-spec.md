---
description: Write a step spec into .claude/specs/
argument-hint: <step number or name>
allowed-tools: Bash(sqlite3:*), Bash(venv/bin/python:*), Read, Grep, Glob, Write, Edit
---

Write the requirements spec for one build step into
`.claude/specs/NN-slug.md`, following the house style of the existing
`01-database-setup.md`.

Argument: $ARGUMENTS — a step number, a step name, or both. Resolve it against
the table in `CLAUDE.md`:

| Step | Deliverable |
|------|-------------|
| 1 | `database/db.py` — `get_db()`, `init_db()`, `seed_db()` |
| 2 | registration + login POST handling |
| 3 | `/logout` |
| 4 | `/profile` |
| 5 | session wiring |
| 6 | the expense list |
| 7 | `/expenses/add` |
| 8 | `/expenses/<id>/edit` |
| 9 | `/expenses/<id>/delete` |

Ask which step is meant if the argument is ambiguous. If the target spec file
already exists and is non-empty, show what is there and ask before rewriting.

## Ground the spec in evidence, not invention

The UI is finished and the routes are not, so **the templates and CSS are the
requirements document**. Read them before writing anything. Cite every
requirement as `path:line` in an Evidence table — `01-database-setup.md`
derived the whole schema from `privacy.html` and `landing.html` this way.

Prefer, in order: the assignment text if the user supplies it, then the
templates and CSS, then the existing schema in `database/db.py`. If a
requirement comes from none of those, mark it as a decision rather than
dressing it up as a requirement.

If the spec is reverse-engineered rather than transcribed from a real
assignment, open the file with the same status banner `01-database-setup.md`
carries, so a reader knows it is derived and correctable.

## Structure

Mirror `01-database-setup.md`:

- `# Step N — Title`
- `## Goal` — what this step delivers, and explicitly what it does *not* touch.
- `## Evidence` — the Requirement | Source table, with `path:line` citations.
- `## Decisions` — choices the evidence underdetermines, each with its
  rationale and its cost. Name the tradeoff, not just the pick.
- The contract — a table of functions or routes with their behaviour, or the
  SQL, depending on what the step delivers.
- `## Wiring` — what changes in `app.py`, `base.html`, or the templates.
- `## Known mismatch for Step N+1` — any place a template already posts fields
  or renders variables the routes do not yet supply.
- `## Commands` — how to run and verify it.

## Repo facts the spec must respect

- Templates are the fixed interface. `register.html` posts `name`, which maps
  to the `username` column; `login.html` posts `email` and `password`; both
  render `{% if error %}`. A spec never proposes editing a template to match a
  route — map it in the route.
- No ORM, no blueprints, no app factory. Raw `sqlite3`, all routes in `app.py`.
- Categories are exactly `Food`, `Travel`, `Bills`, `Other`, enforced by a
  CHECK that SQLite cannot alter in place.
- Dates are ISO `TEXT`; amounts are `REAL` rupees.
- `PRAGMA foreign_keys = ON` is per-connection and off by default.
- Port is 5001.

Write the spec only. Do not implement the step, and do not modify `app.py`,
`database/db.py`, or any template. Report the path written and the requirements
you could not find evidence for, so they can be corrected.
